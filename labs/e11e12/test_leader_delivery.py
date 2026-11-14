"""Leader API client: transport verification must fail on changed bytes."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'scripts/e11e12'))
import api_client


class APIClientVerification(unittest.TestCase):
    def fixture(self, corrupt=False):
        job = 'job-client-test'
        state = {'job_id': job, 'trace_id': 'trace-client-test', 'status': 'SUCCEEDED'}
        content = b'public artifact\n'
        digest = hashlib.sha256(content).hexdigest()
        manifest = dict(state, configuration_id='cfg-test', base_commit='a'*40, target_commit='b'*40,
                        artifacts=[{'uri': 'artifact://'+job+'/stage.json', 'sha256': digest, 'bytes': len(content)}])
        def reply(code, value):
            return code, {}, json.dumps(value).encode()
        responses = [reply(200, {'schema_version':'e11e12-1'}), reply(202, state),
                     reply(202, state), reply(409, {'code':'IDEMPOTENCY_CONFLICT'}),
                     reply(200, state), reply(200, manifest),
                     (200, {'X-Content-SHA256':digest}, b'changed' if corrupt else content)]
        return responses, content

    def test_real_exchange_record_and_all_download_hashes(self):
        responses, content = self.fixture()
        with tempfile.TemporaryDirectory() as directory, patch.object(api_client,'exchange',side_effect=responses):
            out = Path(directory)/'client'
            result = api_client.run('http://127.0.0.1:8080', {'mode':'e11-a'}, 'key', out, 5)
            self.assertEqual(result['status'],'SUCCEEDED',result.get('error'))
            self.assertEqual(result['artifact_count'],1)
            self.assertEqual((out/'downloads/stage.json').read_bytes(),content)
            self.assertTrue((out/'conflict.json').is_file())

    def test_changed_download_is_not_saved_or_accepted(self):
        responses, _ = self.fixture(corrupt=True)
        with tempfile.TemporaryDirectory() as directory, patch.object(api_client,'exchange',side_effect=responses):
            out=Path(directory)/'client'
            result=api_client.run('http://127.0.0.1:8080',{},'key',out,5)
            self.assertEqual(result['status'],'FAILED')
            self.assertIn('artifact transport SHA256',result['error'])
            self.assertFalse((out/'downloads/stage.json').exists())

    def test_foreign_and_traversing_uris_are_rejected(self):
        for uri in ['artifact://other/x','artifact://job/../state.json',
                    'artifact://job/%2e%2e/state.json','artifact://job/.git/config']:
            with self.subTest(uri=uri), self.assertRaises(ValueError):
                api_client.artifact_name({'uri':uri},'job')
