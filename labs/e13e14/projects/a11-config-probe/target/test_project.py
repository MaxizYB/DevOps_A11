"""A11 functional tests, independent of the dependency detector's oracle."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent

class ProbeTests(unittest.TestCase):
    def compile(self, root, app):
        subprocess.run(['gcc', '-O0', str(root / 'main.c'), str(root / 'helper.c'), '-o', str(app)], check=True)

    def test_default_output(self):
        with tempfile.TemporaryDirectory() as temp:
            app = Path(temp) / 'probe'
            self.compile(ROOT, app)
            self.assertEqual(subprocess.check_output([str(app)], text=True), '1\n')

    def test_configuration_change(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'source'
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('.git', '*.o', 'app'))
            (root / 'config.h').write_text('#define VALUE 2\n')
            app = Path(temp) / 'probe'
            self.compile(root, app)
            self.assertEqual(subprocess.check_output([str(app)], text=True), '2\n')

    def test_group_validation_boundaries(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            harness = root / 'harness.c'
            harness.write_text('int a11_group_is_valid(const char *);\n'
                'int main(int argc, char **argv) { return a11_group_is_valid(argc > 1 ? argv[1] : 0) ? 0 : 1; }\n')
            app = root / 'harness'
            subprocess.run(['gcc', '-O0', str(harness), str(ROOT / 'helper.c'), '-o', str(app)], check=True)
            for value in ('A00', 'A11', 'A99'):
                self.assertEqual(subprocess.run([str(app), value]).returncode, 0, value)
            for value in ('', 'A', 'A1', 'B11', 'A1x', 'A111'):
                self.assertEqual(subprocess.run([str(app), value]).returncode, 1, value)
            self.assertEqual(subprocess.run([str(app)]).returncode, 1)

if __name__ == '__main__':
    unittest.main(verbosity=2)
