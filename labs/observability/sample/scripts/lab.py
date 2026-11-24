"""Collect evidence and check the expected result of each sample run."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import uuid


ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / '.env'
TERMINAL = {'SUCCEEDED', 'FAILED', 'TIMED_OUT'}


def init():
    try:
        fd = os.open(ENV, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        print('.env already exists')
        return
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(f'GRAFANA_ADMIN_PASSWORD={secrets.token_urlsafe(20)}\n')
        f.write('LAB_API_PORT=18080\nLAB_PROM_PORT=19090\nLAB_GRAFANA_PORT=13000\n')
    print('Created .env')


def port(name, default):
    settings = {}
    if ENV.is_file():
        for line in ENV.read_text(encoding='utf-8').splitlines():
            key, sep, value = line.strip().partition('=')
            if sep and not key.startswith('#'):
                settings[key] = value.strip().strip('"\'')
    return int(os.environ.get(name, settings.get(name, default)))


def url(port_num, path):
    return f'http://127.0.0.1:{port_num}{path}'


def read(address, body=None):
    request = Request(address, data=None if body is None else json.dumps(body).encode(),
                      headers={'Content-Type': 'application/json'})
    with urlopen(request, timeout=6) as response:
        return response.read()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def check(condition, message):
    if not condition:
        raise ValueError(message)


def target(expected):
    prom = port('LAB_PROM_PORT', 19090)
    path = '/api/v1/query?' + urlencode({'query': 'up{job="lab-worker"}'})
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        try:
            data = json.loads(read(url(prom, path)))['data']['result']
            if len(data) == 1 and int(data[0]['value'][1]) == expected:
                print(f'lab-worker up={expected}')
                return
        except OSError:
            pass
        time.sleep(1)
    raise ValueError(f'Prometheus did not report lab-worker up={expected}')


def run(case):
    api = port('LAB_API_PORT', 18080)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = ROOT / 'work' / f'{case}-{stamp}-{uuid.uuid4().hex[:6]}'
    out.mkdir(parents=True)
    print(f'EVIDENCE_DIR={out.relative_to(ROOT)}', flush=True)
    body = {'idempotency_key': uuid.uuid4().hex, 'sample': 'slow' if case == 'timeout' else 'dependencies'}
    write(out/'request.json', body)
    first = json.loads(read(url(api, '/v1/jobs'), body))
    write(out/'submitted.json', first)
    duplicate = json.loads(read(url(api, '/v1/jobs'), body))
    write(out/'repeated.json', duplicate)
    check((first['job_id'], first['trace_id']) == (duplicate['job_id'], duplicate['trace_id']), 'Duplicate job')
    address = url(api, '/v1/jobs/' + first['job_id'])
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        result = json.loads(read(address))
        write(out/'status.json', result)
        if result['status'] in TERMINAL:
            break
        time.sleep(0.3)
    else:
        raise ValueError('Job did not finish within 30 seconds')
    (out/'metrics.txt').write_bytes(read(url(api, '/metrics')))
    expected = {'normal': ('SUCCEEDED', None, 1), 'down': ('FAILED', 'DOWNSTREAM_UNAVAILABLE', 3),
                'recovered': ('SUCCEEDED', None, 1), 'timeout': ('TIMED_OUT', 'DOWNSTREAM_TIMEOUT', 3)}[case]
    observed = (result['status'], result['error_code'], result['attempts'])
    check(observed == expected, f'Expected {expected}; observed {observed}')
    if expected[0] == 'SUCCEEDED':
        content = read(url(api, result['artifact']['path']))
        (out/'report.json').write_bytes(content)
        check(hashlib.sha256(content).hexdigest() == result['artifact']['sha256'], 'Artifact SHA256 mismatch')
        report = json.loads(content)
        check(report == {'target': 'main.o', 'missing': ['config.h'], 'redundant': ['unused.h']}, 'Unexpected dependency findings')
    else:
        check('artifact' not in result, 'Failed job must not have a success artifact')
    write(out/'check.json', {'passed': True, 'case': case, 'status': result['status'], 'job_id': result['job_id'],
                            'trace_id': result['trace_id'], 'attempts': result['attempts'], 'duration_ms': result['duration_ms']})
    print(f"PASS {case} {result['status']} attempts={result['attempts']} job_id={result['job_id']}")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('init')
    wait = sub.add_parser('target')
    wait.add_argument('expected', type=int, choices=(0, 1))
    job = sub.add_parser('run')
    job.add_argument('case', choices=('normal', 'down', 'recovered', 'timeout'))
    args = p.parse_args()
    try:
        if args.command == 'init':
            init()
        elif args.command == 'target':
            target(args.expected)
        else:
            run(args.case)
    except (OSError, ValueError, KeyError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
