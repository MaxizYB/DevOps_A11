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
import orchestrate


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

    def test_e14_profile_validation_accepts_cjson_files(self):
        project = self.root / 'cjson'
        project.mkdir()
        for name in ('cJSON.c', 'cJSON.h', 'cJSON_Utils.c', 'cJSON_Utils.h', 'Makefile'):
            (project / name).write_text('fixture\n')
        orchestrate.validate_project_profile(project, 'cjson')

    def test_e14_profile_validation_rejects_teaching_shape_for_cjson(self):
        project = self.root / 'cjson'
        project.mkdir()
        (project / 'main.c').write_text('fixture\n')
        with self.assertRaisesRegex(ValueError, 'Unsupported cJSON project profile'):
            orchestrate.validate_project_profile(project, 'cjson')

    def test_cjson_harness_preserves_candidate_and_records_original_bytes(self):
        target = self.root / 'snapshot'
        target.mkdir()
        broken = self.root / 'Dockerfile.broken'
        raw = b'FROM example:tag\nWORKDIR /work\n'
        broken.write_bytes(raw)
        original = self.candidate.read_bytes()
        out = self.root / 'run'
        request = dict(project_profile='cjson', broken_dockerfile=orchestrate.container_path(broken))
        orchestrate.prepare_harness(request, target, self.candidate, out)
        self.assertEqual((target / 'Dockerfile.broken').read_bytes(), raw)
        self.assertEqual(broken.read_bytes(), raw)
        self.assertEqual(self.candidate.read_bytes(), original)
        provenance = json.loads((out / 'harness-provenance.json').read_text())
        self.assertEqual(provenance['candidate_sha256'], hashlib.sha256(original).hexdigest())
        self.assertEqual(provenance['broken_sha256'], hashlib.sha256(raw).hexdigest())

    def test_cjson_harness_never_overwrites_upstream_file(self):
        target = self.root / 'snapshot'
        target.mkdir()
        existing = target / 'Dockerfile.broken'
        existing.write_bytes(b'keep upstream')
        broken = self.root / 'broken'
        broken.write_bytes(b'experiment')
        request = dict(project_profile='cjson', broken_dockerfile=orchestrate.container_path(broken))
        with self.assertRaisesRegex(ValueError, 'Refusing to overwrite'):
            orchestrate.prepare_harness(request, target, self.candidate, self.root / 'run')
        self.assertEqual(existing.read_bytes(), b'keep upstream')

    def test_cjson_harness_rejects_broken_file_outside_data(self):
        request = dict(project_profile='cjson', broken_dockerfile='/course/work/outside')
        with self.assertRaisesRegex(ValueError, 'inside data'):
            orchestrate.prepare_harness(request, self.repo, self.candidate, self.root / 'run')

    def test_teaching_harness_rejects_cjson_only_input(self):
        with self.assertRaisesRegex(ValueError, 'only supported for cjson'):
            orchestrate.prepare_harness(dict(broken_dockerfile='/course/data/input'),
                                        self.repo, self.candidate, self.root / 'run')

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
