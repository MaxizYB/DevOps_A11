"""Input preparation must preserve history, names and failed-run evidence."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts/e11e12'))
import prepare_cjson
from draft.autobuild import prepare_candidate


class PrepareCjsonTests(unittest.TestCase):
    def test_mirror_dataset_keeps_requested_name_and_original_commands(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            bundle=root/'input.bundle'
            bundle.write_bytes(b'test bundle, not project evidence')
            data=root/'data'
            (data/'real-project').mkdir(parents=True)
            def git(repo,*args):
                if args[0]=='status':
                    return ''
                if args[0]=='show':
                    return 'fixture description'
                return prepare_cjson.TARGET if args[1]=='HEAD' else args[1].split('^')[0]
            with patch.object(prepare_cjson,'git',side_effect=git), \
                    patch.object(prepare_cjson,'BUNDLE_SHA256',hashlib.sha256(bundle.read_bytes()).hexdigest()):
                result=prepare_cjson.prepare(bundle,data,'cjson-a11','mirror.invalid/python:3.13-slim@sha256:'+'a'*64,
                                             'https://mirror.invalid')
            self.assertEqual(Path(result['request']).name,'cjson-a11-request.json')
            self.assertFalse((data/'target-request.json').exists())
            request=json.loads(Path(result['request']).read_text())
            self.assertTrue(request['candidate'].endswith('cjson-a11.Dockerfile.candidate'))
            broken=(data/'cjson-a11.Dockerfile.broken').read_text()
            candidate=(data/'cjson-a11.Dockerfile.candidate').read_text()
            self.assertIn('RUN make cJSON_Utils.o',prepare_candidate(broken,candidate))
            dataset=json.loads(Path(result['dataset']).read_text())
            self.assertFalse(dataset['maintenance_claim'])
            self.assertEqual(dataset['commits']['base']['sha'],prepare_cjson.BASE)
            self.assertEqual(dataset['mirror_overrides']['debian_mirror'],'https://mirror.invalid')

    def test_different_existing_input_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'existing'
            path.write_bytes(b'keep original failed-run input')
            with self.assertRaisesRegex(ValueError,'Refusing to overwrite'):
                prepare_cjson.write_once(path,b'changed')
            self.assertEqual(path.read_bytes(),b'keep original failed-run input')

    def test_unsafe_mirror_is_rejected_before_creating_data(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with self.assertRaisesRegex(ValueError,'plain HTTPS'):
                prepare_cjson.prepare(root/'bundle',root/'data','cjson-a11',debian_mirror="https://x'; bad")
            self.assertFalse((root/'data').exists())
