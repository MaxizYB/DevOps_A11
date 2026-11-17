"""A11 configuration probe behavior tests; build outputs stay outside source."""
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent

class ProbeTests(unittest.TestCase):
    def test_default_output(self):
        with tempfile.TemporaryDirectory() as temp:
            app = Path(temp) / 'probe'
            subprocess.run(['gcc', '-O0', str(ROOT / 'main.c'), str(ROOT / 'helper.c'), '-o', str(app)], check=True)
            self.assertEqual(subprocess.check_output([str(app)], text=True), '1\n')

if __name__ == '__main__':
    unittest.main(verbosity=2)
