import hashlib
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'labs/e11e12'))
sys.path.insert(0, str(ROOT / 'labs/e13e14'))
import pipeline
import handoff_a_to_b


class FoundationTests(unittest.TestCase):
    def setUp(self):
        data = ROOT / 'data'
        data.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=data)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.fixed = self.root / 'fixed.json'
        self.fixed.write_text('{}')
        self.candidate = self.root / 'candidate.Dockerfile'
        self.candidate.write_text('FROM example@sha256:' + '0' * 64)
        self.request = dict(mode='e11-b', repo=str(self.repo), base='a'*40, target='b'*40,
                            candidate=str(self.candidate), fixed_report=str(self.fixed))

    def test_fractional_timeout_allowed(self):
        self.request['build_timeout'] = 0.01
        self.assertEqual(pipeline.validate_request(self.request)['build_timeout'], 0.01)

    def test_invalid_timeouts_rejected(self):
        for value in (True, False, 0, -1, math.inf, -math.inf, math.nan, '1', None):
            with self.subTest(value=value), self.assertRaises(pipeline.Failure):
                pipeline.validate_request(dict(self.request, build_timeout=value))

    def test_digest_field_validated(self):
        for digest in ('0'*63, 'G'*64, None, 12):
            with self.subTest(digest=digest), self.assertRaises(pipeline.Failure):
                pipeline.validate_request(dict(self.request, fixed_report_sha256=digest))
        pipeline.validate_request(dict(self.request, fixed_report_sha256='0'*64))

    def test_hash_checked_on_external_report_before_parse(self):
        # Keep invalid JSON; the transfer hash must fail before JSON interpretation.
        self.fixed.write_text('changed bytes, not JSON')
        request = dict(self.request, fixed_report_sha256=hashlib.sha256(b'{}').hexdigest())
        with tempfile.TemporaryDirectory() as output, \
             patch.object(pipeline, 'snapshot', side_effect=['a'*40, 'b'*40]), \
             patch('draft.autobuild.auto_build', return_value={'status': 'SUCCEEDED'}):
            folder = Path(output) / 'run'
            (folder / 'draft-build').mkdir(parents=True)
            (folder / 'draft-build/result.json').write_text('{}')
            # execute requires a fresh directory; arrange the fake DRAFT output at call time.
            (folder / 'draft-build/result.json').unlink()
            (folder / 'draft-build').rmdir()
            folder.rmdir()
            def draft(*args, **kwargs):
                p = folder / 'draft-build'
                p.mkdir(parents=True)
                (p / 'result.json').write_text('{}')
                return {'status': 'SUCCEEDED'}
            with patch('draft.autobuild.auto_build', side_effect=draft):
                result = pipeline.execute(request, folder)
            self.assertEqual(result['status'], 'FAILED')
            self.assertEqual(result['error']['code'], 'ARTIFACT_HASH_MISMATCH')

    def test_runtime_scanner_missing_is_incomplete(self):
        from scan_runtime_logs import main
        self.assertEqual(main([str(self.root / 'absent')]), 2)

    def test_runtime_scanner_fake_value_redacted(self):
        import contextlib
        import io
        from scan_runtime_logs import main
        probe = self.root / 'probe.log'
        fake = 'sk-' + 'a' * 24
        probe.write_text('api_key = "' + fake + '"\n')
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(main([str(probe)]), 1)
        self.assertNotIn(fake, out.getvalue())
        probe.write_text('clean log\n')
        self.assertEqual(main([str(probe)]), 0)


if __name__ == '__main__':
    unittest.main()
