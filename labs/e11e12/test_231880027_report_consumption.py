"""Issue #39 report-consumption tests; requires the E11 public foundation."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/e11e12'))
from verify_issue39_report import consume


@unittest.skipUnless((ROOT / 'labs/e11e12/pipeline.py').is_file(),
                     'requires the E11 public foundation')
class Student231880027ReportConsumptionTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.report = {
            'schema_version': 'e11e12-1', 'kind': 'incremental-check',
            'status': 'SUCCEEDED', 'commit': 'a' * 40,
            'configuration_id': 'test-configuration',
            'job_id': 'test-job', 'trace_id': 'test-trace',
        }
        self.path = self.root / 'report.json'
        self.path.write_text(json.dumps(self.report))
        self.sha = hashlib.sha256(self.path.read_bytes()).hexdigest()

    def check(self, commit, kind, code=None):
        result = consume(self.path, self.sha, commit, kind, self.root / 'result.json')
        persisted = json.loads((self.root / 'result.json').read_text())
        self.assertEqual(result, persisted)
        self.assertEqual(result['accepted'], code is None)
        self.assertEqual(result['status'], 'SUCCEEDED' if code is None else 'FAILED')
        if code:
            self.assertEqual(result['error']['code'], code)
        return result

    def test_current_report_is_accepted(self):
        result = self.check('a' * 40, 'incremental-check')
        self.assertEqual(result['job_id'], 'test-job')
        self.assertEqual(result['configuration_id'], 'test-configuration')

    def test_old_report_returns_public_stale_report_code(self):
        self.check('b' * 40, 'incremental-check', 'STALE_REPORT')

    def test_baseline_from_another_commit_is_rejected(self):
        self.report['kind'] = 'full-check'
        self.path.write_text(json.dumps(self.report))
        self.sha = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.check('b' * 40, 'full-check', 'STALE_REPORT')

    def test_changed_bytes_are_rejected_before_envelope_consumption(self):
        self.path.write_bytes(self.path.read_bytes() + b'\n')
        self.check('a' * 40, 'incremental-check', 'ARTIFACT_HASH_MISMATCH')


def load_tests(loader, tests, pattern):
    # The public test command discovers this file; include the personal scan tests.
    tests.addTests(unittest.TestLoader().discover(str(ROOT / 'tests/e11e12'),
                                  pattern='test_231880027_refresh_reuse.py'))
    return tests


if __name__ == '__main__':
    unittest.main()
