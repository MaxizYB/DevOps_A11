"""Run Issue #45 on the fixed B11 cJSON input without modifying public code."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from verify_peer import BASE, TARGET, EXPECTED, ACTUAL, DECLARED, read, sha, require, verify_a

ROOT = Path(__file__).resolve().parents[2]
IMAGE = 'course-e11e12:231880027'


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def snapshot(folder):
    return {str(p.relative_to(folder)): sha(p) for p in sorted(folder.rglob('*'))
            if p.is_file() and '.git' not in p.parts and not p.is_symlink()}


def execute(out, port):
    require(out.resolve().is_relative_to(ROOT / 'work') and not out.exists(), 'Choose a fresh work/ directory')
    out.mkdir(parents=True)
    commands = []
    checks = {}

    def command(name, argv, expected=0, timeout=600):
        start = time.monotonic()
        with (out / (name + '.stdout.log')).open('w') as stdout, (out / (name + '.stderr.log')).open('w') as stderr:
            try:
                process = subprocess.run(argv, cwd=ROOT, stdout=stdout, stderr=stderr, timeout=timeout)
                code = process.returncode
            except subprocess.TimeoutExpired:
                code = 124
        commands.append(dict(name=name, argv=argv, cwd=str(ROOT), exit_code=code,
                             elapsed_s=time.monotonic() - start, expected_exit=expected))
        save(out / 'commands.json', commands)
        print(name, 'exit=', code, flush=True)
        require(code == expected, name + ' unexpected exit; inspect preserved logs')
        return (out / (name + '.stdout.log')).read_text().strip()

    def container(argv):
        return ['docker', 'run', '--rm', '--network', 'none', '--cap-add', 'SYS_PTRACE',
                '--user', str(os.getuid()) + ':' + str(os.getgid()),
                '-e', 'HOME=/tmp', '-e', 'PYTHONPATH=/course/labs/e11e12:/course/labs/e8e10:/course/labs/e11e12/vendor:/app',
                '-v', str(ROOT) + ':/course', '-w', '/course', IMAGE, 'python3', *argv]

    def inside(path):
        return '/course/' + str(path.resolve().relative_to(ROOT))

    project = ROOT / 'data/issue45-cjson'
    repo = project / 'repo'
    source = dict(operator='231880027', issue=45,
                  source_sha=command('source-sha', ['git', 'rev-parse', 'HEAD']),
                  branch=command('source-branch', ['git', 'branch', '--show-current']),
                  base=BASE, target=TARGET, bundle_sha256=sha(project / 'cjson-b-e13.bundle'),
                  candidate_sha256=sha(project / 'candidate.Dockerfile'),
                  started_utc=datetime.now(timezone.utc).isoformat(),
                  personal_sources={str(p.relative_to(ROOT)): sha(p) for p in Path(__file__).parent.glob('*.py')})
    save(out / 'source.json', source)
    for p in Path(__file__).parent.glob('*.py'):
        shutil.copyfile(p, out / p.name)
    command('source-status', ['git', 'status', '--short', '--branch'])
    command('image-inspect', ['docker', 'image', 'inspect', IMAGE])
    command('tool-versions', ['docker', 'run', '--rm', '--network', 'none', IMAGE, 'sh', '-c',
                             'python3 --version; gcc --version; make --version; strace --version; git --version'])
    command('host', ['uname', '-a'])
    command('memory', ['free', '-b'])
    command('bundle-verify', ['git', '-C', str(repo), 'bundle', 'verify', str(project / 'cjson-b-e13.bundle')])
    command('ancestry', ['git', '-C', str(repo), 'merge-base', '--is-ancestor', BASE, TARGET])
    changed = command('project-changed-files', ['git', '-C', str(repo), 'diff', '--name-only', BASE, TARGET])
    require(changed == 'test.c', 'Independent reuse premise changed')
    command('project-diff', ['git', '-C', str(repo), 'diff', BASE, TARGET])
    for label, revision in [('base', BASE), ('target', TARGET)]:
        command(label + '-makefile', ['git', '-C', str(repo), 'show', revision + ':Makefile'])
        command(label + '-utils-source', ['git', '-C', str(repo), 'show', revision + ':cJSON_Utils.c'])
        command(label + '-utils-header', ['git', '-C', str(repo), 'show', revision + ':cJSON_Utils.h'])
    save(out / 'expectations.json', dict(base=BASE, target=TARGET, actual=ACTUAL, declared=DECLARED,
         findings=EXPECTED, reused=['cJSON_Utils.o'], refreshed=[],
         rationale='Only test.c body changes; Utils compilation/header/preprocessor inputs unchanged. Source includes cJSON.h; Make Utils rule omits it.',
         C2='STALE_REPORT exit 1', C3='ARTIFACT_HASH_MISMATCH exit 1',
         C7='failed task followed by successful task, distinct jobs/traces, immutable failed evidence',
         C8='same key/input 202 same job; same key/different target 409'))
    input_before = snapshot(repo)
    git_before = dict(head=command('input-head-before', ['git', '-C', str(repo), 'rev-parse', 'HEAD']),
                      status=command('input-status-before', ['git', '-C', str(repo), 'status', '--porcelain']))
    require(git_before['head'] == TARGET and not git_before['status'], 'Input Git state is not clean target')
    save(out / 'input-before.json', input_before)
    request = dict(mode='e11-a', project_profile='cjson', repo=inside(repo), base=BASE, target=TARGET,
                   candidate=inside(project / 'candidate.Dockerfile'), expected_output='1', build_timeout=600)

    def run_case(name, payload, expected=0):
        path = project / (out.name + '-' + name + '.json')
        require(not path.exists(), 'Request already exists')
        save(path, payload)
        save(out / (name + '-request.json'), payload)
        directory = out / name
        command(name, ['python3', 'run_e11e12.py', 'run', '--request', str(path.relative_to(ROOT)),
                       '--out', str(directory.relative_to(ROOT))], expected)
        return directory

    try:
        c1 = run_case('C1', request)
        checks['C1_A'] = verify_a(c1)
        checks['C1_B'] = dict(status='PENDING_LEADER_RECEIPT', reason='New personal report has not been delivered to B11; no peer communication performed')
        save(out / 'checks.json', checks)
        # Use the existing public validators, not a substitute implementation.
        report = c1 / 'incremental-check.json'
        digest = sha(report)

        def consume(name, path, expected_hash, expected_commit, code, error=None):
            result = out / (name + '-consumption.json')
            argv = ['scripts/e11e12/verify_issue39_report.py', '--report', inside(path),
                    '--sha256', expected_hash, '--commit', expected_commit, '--kind', 'incremental-check',
                    '--out', inside(result)]
            command(name, container(argv), code)
            data = read(result)
            if error:
                require(not data['accepted'] and data['error']['code'] == error, name + ' wrong rejection')
            else:
                require(data['accepted'] is True, name + ' valid report rejected')
            return data

        consume('C2-control', report, digest, TARGET, 0)
        checks['C2'] = consume('C2', report, digest, BASE, 1, 'STALE_REPORT')
        handoff = out / 'C2-invalid-handoff.json'
        command('C2-public-handoff', ['python3', 'labs/e13e14/handoff_a_to_b.py', '--a-result', str(c1 / 'result.json'),
                                    '--target-sha', BASE, '--out', str(handoff)], 1)
        require(not handoff.exists(), 'Rejected handoff still produced output')
        changed_report = out / 'C3-report.json'
        changed_report.write_bytes(report.read_bytes() + b'\n')
        checks['C3'] = consume('C3', changed_report, digest, TARGET, 1, 'ARTIFACT_HASH_MISMATCH')
        checks['C3'].update(original_sha256=digest, changed_sha256=sha(changed_report), original=str(report), modified=str(changed_report))
        require(sha(report) == digest and sha(changed_report) != digest, 'Tamper did not preserve original')
        bad = run_case('C7-failed', dict(request, base='0' * 40), 1)
        bad_result = read(bad / 'result.json')
        require(bad_result['status'] == 'FAILED' and bad_result['error']['code'] == 'COMMAND_FAILED', 'Unexpected failure injection')
        failed_before = snapshot(bad)
        good = run_case('C7-recovered', request)
        good_check = verify_a(good)
        require(bad_result['job_id'] != good_check['job_id'] and bad_result['trace_id'] != good_check['trace_id'], 'Task identities reused')
        require(snapshot(bad) == failed_before, 'Normal job changed failed evidence')
        checks['C7'] = dict(status='PASS', failed_job=bad_result['job_id'], failed_trace=bad_result['trace_id'],
                            recovered=good_check, failed_evidence_unchanged=True)
        save(out / 'C7-failed-file-hashes.json', failed_before)
        save(out / 'checks.json', checks)
        name = 'e13-45-api-231880027-' + str(os.getpid())
        launched = False
        existing_jobs = sorted(p.name for p in (ROOT / 'work/api-jobs').glob('job-*'))
        save(out / 'C8-jobs-before.json', existing_jobs)
        try:
            command('C8-start-api', ['docker', 'run', '-d', '--name', name, '--network', 'bridge',
                    '--user', str(os.getuid()) + ':' + str(os.getgid()),
                    '-p', '127.0.0.1:' + str(port) + ':8080', '--cap-add', 'SYS_PTRACE', '-e', 'HOME=/tmp',
                    '-e', 'PYTHONPATH=/course/labs/e11e12:/course/labs/e8e10:/course/labs/e11e12/vendor:/app',
                    '-v', str(ROOT) + ':/course', '-w', '/course', IMAGE,
                    'python3', 'labs/e11e12/server.py', '--host', '0.0.0.0', '--port', '8080'])
            launched = True
            url = 'http://127.0.0.1:' + str(port)
            deadline = time.monotonic() + 45
            while True:
                try:
                    with urllib.request.urlopen(url + '/health', timeout=2) as response:
                        save(out / 'C8-health.json', json.load(response))
                    break
                except (OSError, ValueError):
                    if time.monotonic() > deadline:
                        raise RuntimeError('Private API did not become healthy')
                    time.sleep(0.5)

            def http(label, method, path, payload=None):
                req = urllib.request.Request(url + path, method=method,
                     data=json.dumps(payload).encode() if payload is not None else None,
                     headers={'Content-Type': 'application/json'})
                try:
                    response = urllib.request.urlopen(req, timeout=20)
                except urllib.error.HTTPError as error:
                    response = error
                with response:
                    raw = response.read()
                    record = dict(method=method, url=url + path, request=payload, http=response.code,
                                  headers=dict(response.headers), body=json.loads(raw), response_sha256=hashlib.sha256(raw).hexdigest())
                save(out / (label + '.json'), record)
                (out / (label + '.response')).write_bytes(raw)
                return record

            key = 'issue45-' + out.name
            body = dict(input=request, idempotency_key=key)
            first = http('C8-first', 'POST', '/v1/jobs', body)
            second = http('C8-repeat', 'POST', '/v1/jobs', body)
            conflict = http('C8-conflict', 'POST', '/v1/jobs', dict(body, input=dict(request, target='0' * 40)))
            require(first['http'] == second['http'] == 202 and first['body']['job_id'] == second['body']['job_id'], 'Same-input job not reused')
            require(conflict['http'] == 409 and conflict['body']['code'] == 'IDEMPOTENCY_CONFLICT', 'Conflict not HTTP409')
            job = first['body']['job_id']
            deadline = time.monotonic() + 300
            polls = 0
            while True:
                state = http('C8-poll-' + str(polls), 'GET', '/v1/jobs/' + job)
                polls += 1
                if state['body']['status'] in ('SUCCEEDED', 'FAILED', 'TIMED_OUT'):
                    break
                require(time.monotonic() < deadline, 'C8 task timeout')
                time.sleep(1)
            require(state['body']['status'] == 'SUCCEEDED', 'Idempotent task did not succeed')
            evidence = ROOT / 'work/api-jobs' / job / 'evidence'
            api_check = verify_a(evidence)
            require((api_check['job_id'], api_check['trace_id']) == (job, state['body']['trace_id']), 'HTTP/artifact identity mismatch')
            jobs_after = sorted(p.name for p in (ROOT / 'work/api-jobs').glob('job-*'))
            save(out / 'C8-jobs-after.json', jobs_after)
            save(out / 'C8-state.json', read(evidence.parent / 'state.json'))
            require(set(jobs_after) - set(existing_jobs) == {job}, 'Duplicate job created')
            checks['C8'] = dict(status='PASS', http=[first['http'], second['http'], conflict['http']],
                                job_id=job, trace_id=state['body']['trace_id'], evidence=str(evidence), check=api_check)
        finally:
            if launched:
                command('C8-api-logs', ['docker', 'logs', name])
                command('C8-stop-api', ['docker', 'stop', '--time', '10', name])
                command('C8-remove-api', ['docker', 'rm', name])
        require(snapshot(repo) == input_before, 'Original project changed')
        git_after = dict(head=command('input-head-after', ['git', '-C', str(repo), 'rev-parse', 'HEAD']),
                         status=command('input-status-after', ['git', '-C', str(repo), 'status', '--porcelain']))
        require(git_before == git_after, 'Input Git state changed')
        require(source['bundle_sha256'] == sha(project / 'cjson-b-e13.bundle') and
                source['candidate_sha256'] == sha(project / 'candidate.Dockerfile'), 'Bundle/candidate changed')
        save(out / 'input-git.json', dict(before=git_before, after=git_after,
                                        bundle_sha256=source['bundle_sha256'], candidate_sha256=source['candidate_sha256']))
        save(out / 'input-after.json', snapshot(repo))
        checks['source_unchanged'] = True
        checks['status'] = 'PERSONAL_E13_CHECKS_PASS_C1_B_PENDING'
        return checks
    finally:
        save(out / 'checks.json', checks)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--port', type=int, default=18445)
    args = parser.parse_args()
    result = execute((ROOT / args.out).resolve(), args.port)
    print(json.dumps(result, indent=2))
