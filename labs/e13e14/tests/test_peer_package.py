import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT))
from package_peer_results import security_review


class PeerSecurityReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name) / 'peer-run'
        self.run.mkdir()
        self.blobs = {}
        findings = []
        for name, linenos in [('testRunnerGenerator.c', (115, 127)), ('testRunnerGeneratorWithMocks.c', (116, 128))]:
            relative = 'tests/unity/test/testdata/' + name
            lines = ['// fixture'] * 128
            for lineno in linenos:
                lines[lineno - 1] = 'Postman-' + 'Token: ' + '768c7149-c3fb-f704-71a2-63918d9195b2'
            raw = ('\n'.join(lines) + '\n').encode()
            self.blobs[relative] = raw
            for copy in ('A-result/base-project', 'A-result/target-project',
                         'A-result/baseline-full/project', 'A-result/target-full/project',
                         'base-functional', 'target-functional'):
                path = self.run / copy / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
                for lineno in linenos:
                    findings.append('FOUND /cloud/peer-run/' + copy + '/' + relative + ':' + str(lineno) + ' secret assignment 768c***')
        self.scan = self.run / 'runtime-scan.stdout.log'
        self.scan.write_text('\n'.join(findings) + '\nruntime log scan: text_files=50 hits=24 errors=0\n')

    def git_blob(self, argv, **kwargs):
        return self.blobs[argv[2].split(':', 1)[1]]

    def test_only_exact_unchanged_fixtures_reviewed(self):
        with patch('package_peer_results.subprocess.check_output', side_effect=self.git_blob):
            result = security_review(self.run, Path('unused'))
        self.assertEqual(result['raw_scan_exit_code'], 1)
        self.assertEqual(len(result['findings']), 24)

    def test_unexpected_hit_not_suppressed(self):
        self.scan.write_text(self.scan.read_text().replace('secret assignment 768c***', 'GitHub token ghp_***', 1))
        with patch('package_peer_results.subprocess.check_output', side_effect=self.git_blob), self.assertRaises(ValueError):
            security_review(self.run, Path('unused'))

    def test_changed_copy_not_suppressed(self):
        (self.run / 'base-functional/tests/unity/test/testdata/testRunnerGenerator.c').write_text('changed')
        with patch('package_peer_results.subprocess.check_output', side_effect=self.git_blob), self.assertRaises(ValueError):
            security_review(self.run, Path('unused'))

    def test_missing_hit_not_assumed_reviewed(self):
        self.scan.write_text('\n'.join(self.scan.read_text().splitlines()[1:]) + '\n')
        with patch('package_peer_results.subprocess.check_output', side_effect=self.git_blob), self.assertRaises(ValueError):
            security_review(self.run, Path('unused'))


if __name__ == '__main__':
    unittest.main()
