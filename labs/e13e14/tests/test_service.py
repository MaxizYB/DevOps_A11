import hashlib
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'labs/e11e12/vendor'),str(ROOT/'labs/e8e10'),str(ROOT/'labs/e11e12/environment/services/buildchecker')]
spec=importlib.util.spec_from_file_location('e14_service_test',ROOT/'labs/e13e14/service.py')
service=importlib.util.module_from_spec(spec)
with patch.dict(os.environ,{'E14_ROLE':'echecker'}):
    spec.loader.exec_module(service)

class ServiceTests(unittest.TestCase):
    def test_allowlists_one_exact_snapshot_not_wildcard(self):
        with patch.object(service.subprocess,'run') as command:
            service.mark_safe(Path('/course/work/example/base-project'))
        self.assertEqual(command.call_args.args[0],['git','config','--global','--add','safe.directory','/course/work/example/base-project'])

    def test_rejects_work_root_and_outside_paths(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(service,'ROOT',Path(temp).resolve()):
            for value in (str(Path(temp)/'work'),str(Path(temp)/'data/p'),'/tmp/outside'):
                with self.subTest(value=value),self.assertRaises(ValueError):
                    service.local(value)

    def test_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as other, patch.object(service,'ROOT',Path(temp).resolve()):
            work=Path(temp)/'work';work.mkdir()
            (work/'link').symlink_to(other,target_is_directory=True)
            with self.assertRaises(ValueError):service.local(str(work/'link/report.json'))

    def test_mdfixer_rejects_transfer_hash_before_json_parse(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(service,'ROOT',Path(temp).resolve()),patch.object(service,'ROLE','mdfixer'),patch.object(service,'mark_safe'):
            work=Path(temp)/'work';work.mkdir()
            report=work/'report.json';report.write_text('not json')
            project=work/'project';project.mkdir()
            with self.assertRaisesRegex(ValueError,'hash mismatch'):
                service.run(dict(project=str(project),out=str(work/'output'),report=str(report),report_sha256='0'*64))
            self.assertFalse((work/'output').exists())

if __name__=='__main__':unittest.main()
