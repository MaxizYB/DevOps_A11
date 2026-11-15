"""Record a real orchestration API exchange and verify every downloaded artifact."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import time
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def exchange(base, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    request = Request(base + path, data=data, headers={'Content-Type': 'application/json'})
    try:
        response = urlopen(request, timeout=30)
    except HTTPError as error:
        response = error
    with response:
        raw = response.read()
        return response.status, dict(response.headers.items()), raw


def artifact_name(item, job_id):
    uri = urlsplit(item['uri'])
    name = uri.path.removeprefix('/')
    parts = name.split('/')
    if (uri.scheme != 'artifact' or uri.netloc != job_id or uri.query or uri.fragment
            or not name or any(part in ('', '.', '..', '.git') for part in parts)
            or '%' in name or '\\' in name or PurePosixPath(name).is_absolute()):
        raise ValueError('Non-canonical artifact URI: ' + item['uri'])
    return name


def verify_pipeline(request, manifest, out, require):
    """Verify stage identity and live report consumption, not just transport."""
    mode = request.get('mode')
    stages = {
        'e11-a':['full-check','incremental-check'],
        'e11-b':['draft','fixed-md','repair','recheck'],
        'e12':['draft','full-check','incremental-check','repair','recheck'],
    }[mode]
    require(manifest['base_commit'] == request['base'].lower()
            and manifest['target_commit'] == request['target'].lower(), 'result matches requested commits')
    require(manifest.get('project_profile','teaching') == request.get('project_profile','teaching'),
            'result matches requested project profile')
    require([item['name'] for item in manifest['stages']] == stages, 'expected ordered stages')
    envelopes = {}
    for name in stages:
        raw = (out/'downloads'/(name+'.json')).read_bytes()
        descriptor = next(item['artifact'] for item in manifest['stages'] if item['name'] == name)
        require(hashlib.sha256(raw).hexdigest() == descriptor['sha256'], 'stage descriptor SHA256: '+name)
        envelope = json.loads(raw)
        expected_commit = manifest['base_commit'] if name == 'full-check' else manifest['target_commit']
        require(envelope['schema_version'] == 'e11e12-1' and envelope['kind'] == name
                and envelope['status'] == 'SUCCEEDED' and envelope['commit'] == expected_commit
                and envelope['job_id'] == manifest['job_id'] and envelope['trace_id'] == manifest['trace_id']
                and envelope['configuration_id'] == manifest['configuration_id'], 'stage identity/configuration: '+name)
        envelopes[name] = envelope
    if 'incremental-check' in envelopes:
        current = envelopes['incremental-check']['data']
        baseline_raw = (out/'downloads/baseline-cache.json').read_bytes()
        require(current['commit'] == manifest['target_commit']
                and current['baseline_commit'] == manifest['base_commit']
                and current['baseline_cache_sha256'] == hashlib.sha256(baseline_raw).hexdigest(),
                'incremental report consumes this baseline cache')
        reference = json.loads((out/'downloads/target-full/findings.json').read_text())
        targets = {'cJSON_Utils.o'} if request.get('project_profile') == 'cjson' else {'main.o','helper.o'}
        normalized = lambda findings: sorted((f['type'],f['target'],f['dependency'])
                                             for f in findings if f['target'] in targets)
        require(normalized(current['findings']) == normalized(reference['findings']),
                'incremental findings match target full check')
    if 'repair' in envelopes:
        expected_input = 'incremental-check' if mode == 'e12' else 'fixed-md'
        consumed = envelopes['repair']['data']['input_report']
        raw = (out/'downloads'/(expected_input+'.json')).read_bytes()
        require(artifact_name(consumed, manifest['job_id']) == expected_input+'.json'
                and hashlib.sha256(raw).hexdigest() == consumed['sha256'], 'repair uses this run report')
        final = envelopes['recheck']['data']
        verdict = final['validation']
        require(verdict['accepted'] is True and bool(verdict['checks'])
                and all(value is True for value in verdict['checks'].values()), 'patch accepted with all validation checks')
        require(not any(f['type'] == 'MISSING' for f in final['findings']), 'no missing dependencies after repair')


def run(base, request, key, out, timeout, expected_deployment=None):
    out.mkdir(parents=True, exist_ok=False)
    body = {'idempotency_key': key, 'input': request}
    save(out/'request.json', body)
    checks = []

    def require(condition, description):
        checks.append({'check': description, 'passed': bool(condition)})
        if not condition:
            raise ValueError(description)

    def json_exchange(name, path, payload=None):
        status, headers, raw = exchange(base, path, payload)
        value = json.loads(raw)
        save(out/(name+'.json'), {'http_status': status, 'response': value})
        return status, value

    summary = {'scope': 'API client replay; peer identity must be recorded separately',
               'endpoint': base, 'status': 'RUNNING', 'checks': checks}
    try:
        code, health = json_exchange('health', '/health')
        require(code == 200 and health.get('schema_version') == 'e11e12-1', 'health and version')
        summary['deployment'] = health.get('deployment')
        if expected_deployment:
            require(health.get('deployment',{}).get('implementation_sha256') == expected_deployment,
                    'server matches agreed deployment fingerprint')
        code, submitted = json_exchange('submit', '/v1/jobs', body)
        require(code == 202, 'accepted real task')
        job = submitted['job_id']
        summary.update(job_id=job, trace_id=submitted['trace_id'])
        code, replay = json_exchange('same-key', '/v1/jobs', body)
        require(code == 202 and replay.get('job_id') == job, 'same key reuses same job')
        # Exercise the handbook's same-key/different-target conflict without
        # creating a second job or needing another available project commit.
        changed_target = next(value * 40 for value in '012'
                              if value * 40 not in (request['base'], request['target']))
        changed = dict(body, input=dict(request, target=changed_target))
        save(out/'conflict-request.json', changed)
        code, conflict = json_exchange('conflict', '/v1/jobs', changed)
        require(code == 409 and conflict.get('code') == 'IDEMPOTENCY_CONFLICT', 'changed input returns 409')
        deadline = time.monotonic() + timeout
        polls = []
        while True:
            code, state = json_exchange('latest-state', '/v1/jobs/'+quote(job, safe=''))
            polls.append(state)
            save(out/'polls.json', polls)
            require(code == 200 and state.get('trace_id') == submitted['trace_id'], 'poll task identity')
            if state.get('status') not in ('QUEUED', 'RUNNING'):
                break
            if time.monotonic() >= deadline:
                raise TimeoutError('API task did not finish before client deadline')
            time.sleep(1)
        require(state.get('status') == 'SUCCEEDED', 'task succeeds: '+str(state.get('error')))
        code, manifest = json_exchange('manifest', '/v1/jobs/'+quote(job, safe='')+'/artifacts')
        require(code == 200 and manifest.get('job_id') == job and manifest.get('status') == 'SUCCEEDED',
                'successful task-local result manifest')
        summary.update(configuration_id=manifest['configuration_id'],
                       base_commit=manifest['base_commit'], target_commit=manifest['target_commit'])
        if expected_deployment:
            require(manifest.get('deployment',{}).get('implementation_sha256') == expected_deployment,
                    'job matches agreed deployment fingerprint')
        downloaded = []
        for item in manifest['artifacts']:
            name = artifact_name(item, job)
            destination = out/'downloads'/name
            require(destination.resolve().is_relative_to((out/'downloads').resolve()), 'download stays under output')
            code, headers, raw = exchange(base, '/v1/jobs/'+quote(job, safe='')+'/files/'+quote(name, safe='/'))
            digest = hashlib.sha256(raw).hexdigest()
            require(code == 200 and digest == item['sha256']
                    and headers.get('X-Content-SHA256') == digest
                    and len(raw) == item['bytes'], 'artifact transport SHA256: '+name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
            downloaded.append({'uri': item['uri'], 'sha256': digest, 'bytes': len(raw)})
        save(out/'downloaded.json', downloaded)
        verify_pipeline(request, manifest, out, require)
        summary.update(status='SUCCEEDED', artifact_count=len(downloaded))
    except (ValueError, OSError, KeyError, TimeoutError) as error:
        summary.update(status='FAILED', error=str(error))
    save(out/'verification.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8080')
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--key', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=1200)
    parser.add_argument('--expected-deployment', help='Agreed implementation SHA256 from A11')
    args = parser.parse_args()
    result = run(args.url.rstrip('/'), json.loads(args.request.read_text()), args.key, args.out.resolve(), args.timeout,
                 args.expected_deployment)
    print(json.dumps({k:v for k,v in result.items() if k != 'checks'}, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'SUCCEEDED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
