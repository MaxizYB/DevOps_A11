"""Submit one microservice job and record its HTTP evidence."""

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts' / 'e11e12'))
from api_client import artifact_name, exchange, save

STAGES = ['draft', 'full-check', 'incremental-check', 'repair', 'recheck']


def collect(base, request, key, out, timeout, expected_error=None):
    out.mkdir(parents=True)
    body = {'input': request, 'idempotency_key': key}
    save(out / 'request.json', body)

    def get_json(path, expected, filename, payload=None):
        code, _, raw = exchange(base, path, payload)
        data = json.loads(raw)
        save(out / filename, data)
        if code != expected:
            raise ValueError(f'{path} returned HTTP {code}. See {out / filename}')
        return data

    get_json('/health', 200, 'health.json')
    first = get_json('/v1/jobs', 202, 'submitted.json', body)
    replay = get_json('/v1/jobs', 202, 'repeated.json', body)
    identity = first['job_id'], first['trace_id']
    if (replay['job_id'], replay['trace_id']) != identity:
        raise ValueError('Same request/key created a second job')
    job_url = '/v1/jobs/' + quote(first['job_id'], safe='')
    deadline = time.monotonic() + timeout
    while True:
        state = get_json(job_url, 200, 'status.json')
        if (state['job_id'], state['trace_id']) != identity:
            raise ValueError('Task identity changed during polling')
        if state['status'] not in ('QUEUED', 'RUNNING'):
            break
        if time.monotonic() >= deadline:
            raise TimeoutError(f'Task still running: {first["job_id"]}')
        time.sleep(1)
    manifest = get_json(job_url + '/artifacts', 200, 'manifest.json')
    if (manifest['job_id'], manifest['trace_id'], manifest['status']) != (*identity, state['status']):
        raise ValueError('Manifest disagrees with task status')
    if expected_error is not None:
        if (state['status'] not in ('FAILED', 'TIMED_OUT') or
                state.get('error', {}).get('code') != expected_error):
            raise ValueError(f'Expected error {expected_error}: {state}')
        return state
    if state['status'] != 'SUCCEEDED':
        raise ValueError(f'Expected success: {state.get("error")}')
    if (manifest['base_commit'], manifest['target_commit']) != (request['base'].lower(), request['target'].lower()):
        raise ValueError('Manifest commits differ from the request')
    if [stage['name'] for stage in manifest['stages']] != STAGES:
        raise ValueError('Expected all five stages in order')

    descriptors = {}
    for item in manifest['artifacts']:
        name = artifact_name(item, identity[0])
        if name in descriptors:
            raise ValueError(f'Duplicate manifest entry: {name}')
        code, headers, raw = exchange(base, job_url + '/files/' + quote(name, safe='/'))
        digest = hashlib.sha256(raw).hexdigest()
        if (code != 200 or digest != item['sha256'] or len(raw) != item['bytes']
                or headers.get('X-Content-SHA256') != digest):
            raise ValueError(f'Artifact verification failed: {name}')
        file = out / 'downloads' / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(raw)
        descriptors[name] = item

    for stage in manifest['stages']:
        name = stage['name']
        filename = name + '.json'
        envelope = json.loads((out / 'downloads' / filename).read_text())
        commit = manifest['base_commit'] if name == 'full-check' else manifest['target_commit']
        if (descriptors[filename] != stage['artifact']
                or (envelope['job_id'], envelope['trace_id'], envelope['commit'], envelope['status'])
                    != (*identity, commit, 'SUCCEEDED')):
            raise ValueError(f'Stage identity mismatch: {name}')
    repair = json.loads((out / 'downloads' / 'repair.json').read_text())['data']
    if repair['sha256'] != descriptors['candidate.patch']['sha256']:
        raise ValueError('Published patch differs from repair output')
    incremental = json.loads((out / 'downloads' / 'incremental-check.json').read_text())['data']
    final = json.loads((out / 'downloads' / 'recheck.json').read_text())['data']
    missing = [row for row in incremental['findings'] if row['type'] == 'MISSING']
    if (not missing or final['validation']['accepted'] is not True
            or any(row['type'] == 'MISSING' for row in final['findings'])):
        raise ValueError('Expected a missing dependency and a successful repair')
    save(out / 'check.json', dict(job_id=identity[0], trace_id=identity[1], artifacts=len(descriptors),
                                 missing_before=missing, findings_after=final['findings']))
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:18280')
    parser.add_argument('--request', required=True, type=Path)
    parser.add_argument('--key', required=True)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--timeout', type=int, default=900)
    parser.add_argument('--expect-error')
    args = parser.parse_args()
    try:
        state = collect(args.url.rstrip('/'), json.loads(args.request.read_text()), args.key,
                        args.out, args.timeout, args.expect_error)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f'{exc}\n')
    print(json.dumps(state, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
