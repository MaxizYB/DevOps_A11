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
        baseline = b'{}'
        current = {'commit':'b'*40, 'baseline_commit':'a'*40,
                   'baseline_cache_sha256':hashlib.sha256(baseline).hexdigest(), 'findings':[]}
        payloads = {'baseline-cache.json':baseline,
                    'target-full/findings.json':json.dumps({'findings':[]}).encode()}
        for name, commit, data in [('full-check','a'*40,{}),('incremental-check','b'*40,current)]:
            payloads[name+'.json'] = json.dumps(dict(state, schema_version='e11e12-1', kind=name,
                commit=commit, configuration_id='cfg-test', data=data)).encode()
        descriptors = {name:{'uri':'artifact://'+job+'/'+name,
                            'sha256':hashlib.sha256(raw).hexdigest(), 'bytes':len(raw)}
                       for name,raw in payloads.items()}
        manifest = dict(state, configuration_id='cfg-test', base_commit='a'*40, target_commit='b'*40,
                        artifacts=list(descriptors.values()),
                        stages=[{'name':name,'artifact':descriptors[name+'.json']}
                                for name in ['full-check','incremental-check']])
        def reply(code, value):
            return code, {}, json.dumps(value).encode()
        responses = [reply(200, {'schema_version':'e11e12-1'}), reply(202, state),
                     reply(202, state), reply(409, {'code':'IDEMPOTENCY_CONFLICT'}),
                     reply(200, state), reply(200, manifest)]
        responses += [(200, {'X-Content-SHA256':hashlib.sha256(raw).hexdigest()},
                       b'changed' if corrupt else raw) for raw in payloads.values()]
        return responses, payloads

    def test_real_exchange_record_and_all_download_hashes(self):
        responses, payloads = self.fixture()
        with tempfile.TemporaryDirectory() as directory, patch.object(api_client,'exchange',side_effect=responses):
            out = Path(directory)/'client'
            result = api_client.run('http://127.0.0.1:8080',
                                    {'mode':'e11-a','base':'a'*40,'target':'b'*40}, 'key', out, 5)
            self.assertEqual(result['status'],'SUCCEEDED',result.get('error'))
            self.assertEqual(result['artifact_count'],len(payloads))
            self.assertEqual((out/'downloads/full-check.json').read_bytes(),payloads['full-check.json'])
            self.assertTrue((out/'conflict.json').is_file())

    def test_changed_download_is_not_saved_or_accepted(self):
        responses, _ = self.fixture(corrupt=True)
        with tempfile.TemporaryDirectory() as directory, patch.object(api_client,'exchange',side_effect=responses):
            out=Path(directory)/'client'
            result=api_client.run('http://127.0.0.1:8080',{},'key',out,5)
            self.assertEqual(result['status'],'FAILED')
            self.assertIn('artifact transport SHA256',result['error'])
            self.assertFalse((out/'downloads/baseline-cache.json').exists())

    def test_wrong_deployment_is_rejected_before_submission(self):
        responses, _ = self.fixture()
        with tempfile.TemporaryDirectory() as directory, patch.object(api_client,'exchange',side_effect=responses) as exchange:
            result = api_client.run('http://127.0.0.1:8080',{},'key',Path(directory)/'client',5,'f'*64)
            self.assertEqual(result['status'],'FAILED')
            self.assertIn('deployment fingerprint',result['error'])
            self.assertEqual(exchange.call_count,1)

    def test_foreign_and_traversing_uris_are_rejected(self):
        for uri in ['artifact://other/x','artifact://job/../state.json',
                    'artifact://job/%2e%2e/state.json','artifact://job/.git/config']:
            with self.subTest(uri=uri), self.assertRaises(ValueError):
                api_client.artifact_name({'uri':uri},'job')
