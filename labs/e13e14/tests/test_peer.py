"""Independent Issue #45 oracle rejects plausible but incorrect evidence."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'scripts/e13e14'))
from verify_peer import ACTUAL, BASE, DECLARED, OBJECT, TARGET, checked, manifest, oracle, sha


class PeerOracleTests(unittest.TestCase):
    def setUp(self):
        self.report = dict(commit=TARGET, actual={OBJECT: ACTUAL}, declared={OBJECT: DECLARED},
                           findings=[dict(type='MISSING', target=OBJECT, dependency='cJSON.h')],
                           reused=[OBJECT], refreshed=[], cache_source_commit=BASE)

    def test_valid_independent_expectation(self):
        oracle(self.report)

    def test_duplicate_finding_is_not_hidden_by_set(self):
        self.report['findings'] *= 2
        with self.assertRaisesRegex(ValueError, 'duplicate findings'):
            oracle(self.report)

    def test_extra_redundant_is_rejected(self):
        self.report['findings'].append(dict(type='REDUNDANT', target=OBJECT, dependency='cJSON_Utils.h'))
        with self.assertRaisesRegex(ValueError, 'findings'):
            oracle(self.report)

    def test_wrong_refresh_is_rejected(self):
        self.report.update(refreshed=[OBJECT], reused=[])
        with self.assertRaisesRegex(ValueError, 'reuse/refresh'):
            oracle(self.report)

    def test_old_cache_is_rejected(self):
        self.report['cache_source_commit'] = TARGET
        with self.assertRaisesRegex(ValueError, 'cache source'):
            oracle(self.report)

    def test_other_job_is_rejected_even_with_matching_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'report.json').write_text('{}')
            item = dict(uri='artifact://other/report.json', sha256=sha(root / 'report.json'), bytes=2)
            with self.assertRaisesRegex(ValueError, 'another job'):
                checked(root, item, 'expected')

    def test_modified_bytes_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / 'report.json'
            path.write_text('{}')
            item = dict(uri='artifact://job/report.json', sha256=sha(path), bytes=2)
            path.write_text('{}\n')
            with self.assertRaisesRegex(ValueError, 'SHA mismatch'):
                checked(root, item, 'job')

    def test_resigned_stage_with_wrong_commit_is_rejected(self):
        # Updating hashes alone must not make a wrong-version stage acceptable.
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            envelope = dict(job_id='job', trace_id='trace', status='SUCCEEDED', commit=TARGET)
            path = root / 'full-check.json'
            path.write_text(json.dumps(envelope))
            item = dict(uri='full-check.json', sha256=sha(path), bytes=path.stat().st_size)
            result = dict(job_id='job', trace_id='trace', status='SUCCEEDED', base_commit=BASE,
                          target_commit=TARGET, stages=[dict(name='full-check', artifact=deepcopy(item))], artifacts=[item])
            (root / 'result.json').write_text(json.dumps(result))
            with self.assertRaisesRegex(ValueError, 'Stage commit mismatch'):
                manifest(root, ['full-check'], True)


if __name__ == '__main__':
    unittest.main()
