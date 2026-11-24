"""Submit a project to the E12 API and collect its reports."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import quote
from urllib.request import Request, urlopen
import uuid

from lab import ROOT, check, write


STAGES = ('draft', 'full-check', 'incremental-check', 'repair', 'recheck')


def fetch(address, body=None):
    request = Request(address, data=None if body is None else json.dumps(body).encode(),
                      headers={'Content-Type': 'application/json'})
    with urlopen(request, timeout=10) as response:
        return response.read()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=Path, help='E12 input JSON, without the HTTP wrapper')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--wait', type=int, default=900, help='Max polling time in seconds')
    args = parser.parse_args()
    try:
        task_input = json.loads(args.input.read_text(encoding='utf-8'))
        check(isinstance(task_input, dict) and task_input.get('mode') == 'e12', 'Expected E12 input JSON')
        for field in ('base', 'target'):
            check(bool(re.fullmatch(r'[0-9a-f]{40}', task_input.get(field, ''))), f'Use a complete Git SHA for {field}')
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        out = ROOT/'work'/f'project-{stamp}-{uuid.uuid4().hex[:6]}'
        out.mkdir(parents=True)
        print(f'EVIDENCE_DIR={out.relative_to(ROOT)}', flush=True)
        request = {'input': task_input, 'idempotency_key': uuid.uuid4().hex}
        write(out/'request.json', request)
        root_url = f'http://127.0.0.1:{args.port}/v1/jobs'
        submitted = json.loads(fetch(root_url, request))
        write(out/'submitted.json', submitted)
        job_id = submitted['job_id']
        check(bool(re.fullmatch(r'job-[0-9a-f]{32}', job_id)), 'Unexpected job ID format')
        job_url = root_url + '/' + job_id
        deadline = time.monotonic() + args.wait
        while time.monotonic() < deadline:
            state = json.loads(fetch(job_url))
            write(out/'status.json', state)
            if state['status'] in ('SUCCEEDED', 'FAILED', 'TIMED_OUT', 'CANCELLED'):
                break
            time.sleep(2)
        else:
            raise ValueError('Polling deadline reached; inspect the saved job ID')
        check(state['status'] == 'SUCCEEDED', f"Task {state['status']}: {state.get('error')}")
        result = json.loads(fetch(job_url + '/artifacts'))
        write(out/'result.json', result)
        check(result['job_id'] == job_id and result['trace_id'] == state['trace_id'], 'Task IDs differ')
        check((result['base_commit'], result['target_commit']) == (task_input['base'], task_input['target']), 'Commit mismatch')
        check(tuple(stage['name'] for stage in result['stages']) == STAGES, 'Expected five E12 stages')
        refs = {item['uri']: item for item in result['artifacts']}

        def save_artifact(name, ref):
            check(ref['uri'] == f'artifact://{job_id}/{name}', f'Unexpected URI for {name}')
            content = fetch(job_url + '/files/' + quote(name))
            check(hashlib.sha256(content).hexdigest() == ref['sha256'], f'Artifact hash mismatch: {name}')
            (out/name).write_bytes(content)
            return content

        envelopes = {}
        for stage in result['stages']:
            name = stage['name']
            envelope = json.loads(save_artifact(name+'.json', stage['artifact']))
            expected_sha = task_input['base'] if name == 'full-check' else task_input['target']
            check(envelope['commit'] == expected_sha and envelope['job_id'] == job_id
                  and envelope['trace_id'] == state['trace_id'] and envelope['status'] == 'SUCCEEDED', f'Stage mismatch: {name}')
            envelopes[name] = envelope
        save_artifact('candidate.patch', refs[f'artifact://{job_id}/candidate.patch'])
        md = {(f['target'], f['dependency']) for f in envelopes['incremental-check']['data']['findings'] if f['type'] == 'MISSING'}
        final = envelopes['recheck']['data']
        check(bool(md) and final['validation']['accepted'], 'Expected a missing dependency and an accepted repair')
        check(not any(f['type'] == 'MISSING' for f in final['findings']), 'Missing dependency remains')
        write(out/'check.json', {'passed': True, 'job_id': job_id, 'trace_id': state['trace_id'],
                                'missing_before': sorted(md), 'findings_after': final['findings']})
        print(f'PASS E12 {job_id}')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f'FAIL: {exc}\n')


if __name__ == '__main__':
    main()
