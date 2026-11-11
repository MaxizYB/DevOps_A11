"""Issue #38: independent A11 artifact and HTTP boundary checks (241880411).

The HTTP handler, request validator and store are real. Worker scheduling alone
is paused in API tests; real BuildChecker/EChecker runs belong to the personal
evidence runner, not these deterministic boundary tests.
"""
import copy
import hashlib
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
from pathlib import Path, PurePosixPath
import tempfile
import threading
import unittest
from unittest.mock import patch

import pipeline
import server


class Student241880411ArtifactBoundaries(unittest.TestCase):
    def test_changed_valid_json_has_exact_hash_mismatch_code(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / 'incremental-check.json'
            original = {'schema_version': 'e11e12-1', 'status': 'SUCCEEDED'}
            pipeline.save(report, original)
            metadata = pipeline.artifact(report, root, 'job-241880411')
            self.assertEqual(pipeline.load_artifact(report, metadata['sha256']), original)
            pipeline.save(report, dict(original, status='FAILED'))
            with self.assertRaises(pipeline.Failure) as caught:
                pipeline.load_artifact(report, metadata['sha256'])
            self.assertEqual(caught.exception.code, 'ARTIFACT_HASH_MISMATCH')

    def test_manifest_binds_bytes_producer_commit_and_configuration(self):
        # Independent two-target oracle; these substitutes exercise envelope and
        # manifest construction without claiming to execute a traced build.
        base, target = 'a' * 40, 'b' * 40
        job_id, trace_id = 'job-241880411-metadata', 'trace-241880411-metadata'
        actual = {'main.o': ['config.h', 'main.c'], 'helper.o': ['helper.c']}
        findings = [
            {'type': 'MISSING', 'target': 'main.o', 'dependency': 'config.h'},
            {'type': 'REDUNDANT', 'target': 'main.o', 'dependency': 'unused.h'},
        ]

        def observed_full(project, folder, timeout=120):
            pipeline.save(folder / 'actual-graph.json', [
                {'target': name, 'dependency': dependency}
                for name, dependencies in actual.items() for dependency in dependencies
            ])
            pipeline.save(folder / 'findings.json', {'status': 'SUCCEEDED', 'findings': findings})
            return {'status': 'SUCCEEDED', 'findings': findings}

        def snapshot_with_logs(repo, commit, destination, logs):
            logs.mkdir(parents=True, exist_ok=True)
            for step in ('resolve', 'clone', 'checkout'):
                (logs / f'{destination.name}-{step}.log').write_text(commit + '\n')
            return commit

        data_root = pipeline.ROOT / 'data'
        data_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=data_root) as directory:
            root = Path(directory)
            repo = root / 'repo'
            repo.mkdir()
            out = root / 'out'
            request = {'mode': 'e11-a', 'repo': str(repo), 'base': base, 'target': target}
            report = {'actual': actual, 'findings': findings}
            with patch.object(pipeline, 'snapshot', side_effect=snapshot_with_logs), \
                    patch.object(pipeline, 'full', side_effect=observed_full), \
                    patch.object(pipeline, 'scan', return_value=report):
                result = pipeline.execute(request, out, job_id, trace_id)
            self.assertEqual(result['status'], 'SUCCEEDED', result.get('error'))
            self.assertEqual(result['schema_version'], 'e11e12-1')
            self.assertEqual(result['job_id'], job_id)
            self.assertEqual(result['trace_id'], trace_id)
            self.assertTrue(result['artifacts'])
            for metadata in result['artifacts']:
                with self.subTest(artifact=metadata['uri']):
                    self.assertEqual(metadata['producer_job_id'], job_id)
                    self.assertTrue(metadata['uri'].startswith(f'artifact://{job_id}/'))
                    name = metadata['uri'][len(f'artifact://{job_id}/'):]
                    path = PurePosixPath(name)
                    self.assertFalse(path.is_absolute())
                    self.assertNotIn('..', path.parts)
                    self.assertNotIn('.git', path.parts)
                    data = (out / name).read_bytes()
                    self.assertEqual(metadata['sha256'], hashlib.sha256(data).hexdigest())
                    self.assertEqual(metadata['bytes'], len(data))
                    expected_commit = base if name.startswith((
                        'baseline-', 'full-check.', 'logs/base-project-',
                    )) else target
                    self.assertEqual(metadata['commit'], expected_commit)
                    self.assertEqual(metadata['configuration_id'], result['configuration_id'])
            for kind, commit in [('full-check', base), ('incremental-check', target)]:
                envelope = json.loads((out / (kind + '.json')).read_text())
                self.assertEqual(envelope['commit'], commit)
                self.assertEqual(envelope['job_id'], job_id)
                self.assertEqual(envelope['trace_id'], trace_id)
                for metadata in envelope['artifacts']:
                    self.assertEqual(metadata['commit'], commit)
                    self.assertEqual(metadata['configuration_id'], result['configuration_id'])


class Student241880411HTTPBoundaries(unittest.TestCase):
    def setUp(self):
        data_root = pipeline.ROOT / 'data'
        data_root.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=data_root)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.candidate = self.root / 'candidate.Dockerfile'
        self.candidate.write_text('FROM scratch\n', encoding='utf-8')
        self.request = {
            'mode': 'e11-a', 'repo': str(self.repo),
            'base': 'a' * 40, 'target': 'b' * 40,
        }
        self.store = server.Store(self.root / 'jobs')
        self.addCleanup(self.store.pool.shutdown)
        self.submit_patch = patch.object(self.store.pool, 'submit')
        self.schedule = self.submit_patch.start()
        self.addCleanup(self.submit_patch.stop)
        self.store_patch = patch.object(server, 'Store', return_value=self.store)
        self.store_patch.start()
        self.addCleanup(self.store_patch.stop)
        created = threading.Event()

        def make_http_server(address, handler):
            # Exercise the production handler on an OS-selected loopback port.
            handler.log_message = lambda *_args: None
            self.http = ThreadingHTTPServer(('127.0.0.1', 0), handler)
            created.set()
            return self.http

        self.http_patch = patch.object(server, 'ThreadingHTTPServer', side_effect=make_http_server)
        self.http_patch.start()
        self.addCleanup(self.http_patch.stop)
        self.thread = threading.Thread(target=server.serve, daemon=True)
        self.thread.start()
        self.assertTrue(created.wait(5), 'HTTP server did not start')
        self.addCleanup(self.stop_http)

    def stop_http(self):
        self.http.shutdown()
        self.thread.join(5)
        self.http.server_close()

    def exchange(self, method, path, payload=None):
        connection = HTTPConnection(*self.http.server_address, timeout=5)
        try:
            encoded = None if payload is None else json.dumps(payload).encode()
            connection.request(method, path, encoded, {'Content-Type': 'application/json'})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def post(self, request=None, key='personal-key'):
        code, _, data = self.exchange('POST', '/v1/jobs', {
            'input': self.request if request is None else request,
            'idempotency_key': key,
        })
        return code, json.loads(data)

    def assert_rejected(self, request, message):
        code, body = self.post(request)
        self.assertEqual(code, 400, body)
        self.assertEqual(body['code'], 'REQUEST_1001')
        self.assertIn(message, body['error'])
        self.assertEqual(self.store.jobs, {})
        self.assertFalse(list(self.store.root.glob('job-*/state.json')))
        self.schedule.assert_not_called()

    def test_same_key_reuses_job_and_changed_input_returns_409(self):
        code, original = self.post()
        self.assertEqual(code, 202, original)
        self.assertEqual(original['status'], 'QUEUED')
        self.assertEqual(original['schema_version'], 'e11e12-1')
        code, replay = self.post(copy.deepcopy(self.request))
        self.assertEqual(code, 202)
        self.assertEqual(replay['job_id'], original['job_id'])
        self.assertEqual(replay['trace_id'], original['trace_id'])
        code, conflict = self.post(dict(self.request, target='c' * 40))
        self.assertEqual(code, 409, conflict)
        self.assertEqual(conflict['code'], 'IDEMPOTENCY_CONFLICT')
        self.assertEqual(len(self.store.jobs), 1)
        self.schedule.assert_called_once()
        code, _, state = self.exchange('GET', '/v1/jobs/' + original['job_id'])
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(state)['status'], 'QUEUED')

    def test_repo_outside_data_creates_no_job(self):
        self.assert_rejected(dict(self.request, repo=str(pipeline.ROOT)), 'under data/')

    def test_symlink_escape_from_data_creates_no_job(self):
        link = self.root / 'outside'
        link.symlink_to(pipeline.ROOT, target_is_directory=True)
        self.assert_rejected(dict(self.request, repo=str(link)), 'under data/')

    def test_e12_without_candidate_creates_no_job(self):
        self.assert_rejected(dict(self.request, mode='e12'), 'candidate')

    def test_e12_with_fixed_report_creates_no_job(self):
        self.assert_rejected(dict(
            self.request, mode='e12', candidate=str(self.candidate),
            fixed_report=str(self.root / 'fixed-report.json'),
        ), 'current incremental report')

    def test_short_sha_creates_no_job(self):
        self.assert_rejected(dict(self.request, target='b' * 7), 'full 40-character')

    def test_equal_sha_creates_no_job(self):
        self.assert_rejected(dict(self.request, target=self.request['base']), 'different commits')

    def test_extra_body_key_creates_no_job(self):
        code, _, data = self.exchange('POST', '/v1/jobs', {
            'input': self.request, 'idempotency_key': 'key', 'status': 'SUCCEEDED',
        })
        self.assertEqual(code, 400, data)
        self.assertEqual(json.loads(data)['code'], 'REQUEST_1001')
        self.assertEqual(self.store.jobs, {})
        self.schedule.assert_not_called()

    def test_artifact_download_hash_and_manifest_allowlist(self):
        # A synthetic manifest isolates HTTP transport behavior. The job is
        # deliberately left QUEUED; no successful build is represented here.
        code, state = self.post()
        self.assertEqual(code, 202)
        job_id = state['job_id']
        out = self.store.root / job_id / 'evidence'
        pipeline.save(out / 'public.json', {'value': 241880411})
        (out / 'private.txt').write_text('not in manifest', encoding='utf-8')
        metadata = pipeline.artifact(out / 'public.json', out, job_id)
        pipeline.save(out / 'result.json', {'artifacts': [metadata]})
        code, headers, data = self.exchange('GET', f'/v1/jobs/{job_id}/files/public.json')
        self.assertEqual(code, 200)
        self.assertEqual(headers['X-Content-SHA256'], metadata['sha256'])
        self.assertEqual(hashlib.sha256(data).hexdigest(), metadata['sha256'])
        for path in ['private.txt', '../state.json', '%2e%2e/state.json', '.git/config']:
            with self.subTest(path=path):
                code, _, _ = self.exchange('GET', f'/v1/jobs/{job_id}/files/{path}')
                self.assertEqual(code, 404)


if __name__ == '__main__':
    unittest.main()
