"""Run A11's E13 checks on B11's fixed cJSON bundle, without running B's repair."""
import argparse
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from handoff_a_to_b import make_handoff
from verify_evidence import verify

ROOT = Path(__file__).resolve().parents[2]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def execute(project, out, base, target, archive_sha):
    project, out = project.resolve(), out.resolve()
    if not project.is_relative_to(ROOT / 'data') or not out.is_relative_to(ROOT / 'work'):
        raise ValueError('Use data/ for input and work/ for fresh evidence')
    if out.exists():
        raise ValueError('Preserve earlier output; choose a fresh directory')
    out.mkdir(parents=True)
    events = []

    def cmd(name, argv, cwd=ROOT, timeout=600):
        start = datetime.now(timezone.utc).isoformat()
        tick = time.monotonic()
        with (out / (name + '.stdout.log')).open('w') as stdout, (out / (name + '.stderr.log')).open('w') as stderr:
            process = subprocess.run(argv, cwd=cwd, stdout=stdout, stderr=stderr, timeout=timeout)
        events.append(dict(name=name, argv=argv, cwd=str(cwd), started_utc=start,
                           elapsed_s=time.monotonic() - tick, exit_code=process.returncode))
        save(out / 'commands.json', events)
        print(json.dumps(events[-1], ensure_ascii=False), flush=True)
        if process.returncode:
            raise RuntimeError(name + ' failed; preserve its original logs')
        return (out / (name + '.stdout.log')).read_text().strip()

    repo = project / 'repo'
    bundle = project / 'cjson-b-e13.bundle'
    candidate = project / 'cjson-b-e13.Dockerfile'
    if not repo.exists():
        cmd('clone', ['git', 'clone', '--no-checkout', str(bundle), str(repo)])
    cmd('bundle-verification', ['git', 'bundle', 'verify', str(bundle)], repo)
    for name, revision in [('base', base), ('target', target)]:
        if cmd(name + '-resolve', ['git', 'rev-parse', '--verify', revision + '^{commit}'], repo) != revision:
            raise ValueError('Received commit mismatch')
    cmd('ancestry', ['git', 'merge-base', '--is-ancestor', base, target], repo)
    cmd('checkout', ['git', 'checkout', '--detach', target], repo)
    cmd('project-status-before', ['git', 'status', '--porcelain'], repo)
    if (out / 'project-status-before.stdout.log').read_text().strip():
        raise ValueError('Project input must be clean')
    cmd('project-change', ['git', 'diff', '--no-ext-diff', base, target], repo)
    cmd('target-commit', ['git', 'show', '--no-patch', '--format=fuller', target], repo)
    system = cmd('system-source', ['git', 'rev-parse', 'HEAD'])
    cmd('system-status', ['git', 'status', '--short', '--branch'])
    student = cmd('operator', ['git', 'config', '--local', 'user.name'])
    if not student.isdigit():
        raise ValueError('Expected operator student ID')
    image = 'course-e11e12:' + student
    image_info = json.loads(cmd('image-inspect', ['docker', 'image', 'inspect', image]))[0]
    cmd('host', ['uname', '-a'])
    cmd('resources', ['free', '-b'])
    for name, revision in [('base', base), ('target', target)]:
        sandbox = out / (name + '-functional')
        cmd(name + '-functional-clone', ['git', 'clone', '--no-hardlinks', '--no-checkout', str(repo), str(sandbox)])
        cmd(name + '-functional-checkout', ['git', 'checkout', '--detach', revision], sandbox)
        container = ['docker', 'run', '--rm', '--network', 'none', '--user', str(os.getuid()) + ':' + str(os.getgid()),
                     '-e', 'HOME=/tmp', '-v', str(sandbox) + ':/project', '-w', '/project', image]
        cmd(name + '-make-clean', container + ['make', 'clean'])
        cmd(name + '-make-test', container + ['make', 'test'])
        actual = cmd(name + '-expected-output', container + ['sh', '-c', './cJSON_test >/dev/null && echo 1'])
        if actual != '1':
            raise ValueError(name + ' output differs from the supplied candidate CMD')

    request = dict(mode='e11-a', project_profile='cjson',
                   repo='/course/' + repo.relative_to(ROOT).as_posix(), base=base, target=target,
                   candidate='/course/' + candidate.relative_to(ROOT).as_posix(),
                   expected_output='1', build_timeout=600)
    request_path = project / 'request-e11-a.json'
    if request_path.exists():
        raise ValueError('Refusing to overwrite an earlier request')
    save(request_path, request)
    save(out / 'request-e11-a.json', request)
    result_dir = out / 'A-result'
    cmd('e11-a', ['python3', 'run_e11e12.py', 'run', '--request', str(request_path.relative_to(ROOT)),
                  '--out', str(result_dir.relative_to(ROOT))], timeout=1800)
    check = verify(result_dir)
    save(out / 'verification.json', check)
    result = json.loads((result_dir / 'result.json').read_text())
    if (result['base_commit'], result['target_commit']) != (base, target):
        raise ValueError('Result commit mismatch')
    fixed = make_handoff(result_dir / 'result.json', target)
    save(out / 'fixed-md.json', fixed)
    incremental = json.loads((result_dir / 'incremental-check.json').read_text())['data']
    cmd('project-status-after', ['git', 'status', '--porcelain'], repo)
    if (out / 'project-status-after.stdout.log').read_text().strip():
        raise ValueError('Read-only source was modified')
    cmd('post-containers', ['docker', 'ps', '--no-trunc'])
    summary = dict(group='A11', peer='B11', operator=student, status='A_CHECKS_COMPLETE_B_CONSUMPTION_PENDING',
        system_source_commit=system, input_archive_sha256=archive_sha, bundle_sha256=sha(bundle),
        candidate_sha256=sha(candidate), image_id=image_info['Id'], repo_digests=image_info.get('RepoDigests', []),
        base=base, target=target, expected_output='1', base_make_test='PASS', target_make_test='PASS',
        functional_output='PASS: exact supplied CMD, ./cJSON_test >/dev/null && echo 1; not raw executable stdout',
        result=check, findings=incremental['findings'], reused=incremental['reused'], refreshed=incremental['refreshed'],
        fixed_md_sha256=sha(out / 'fixed-md.json'), source_report=fixed['source_report'], source_unchanged=True,
        scope='A11 leader real run on B11 received project; cJSON_Utils.o profile only; no B repair or signoff',
        candidate_executed=False, candidate_note='Received bytes preserved; DRAFT is B11 responsibility this round',
        pending=['B11 consume this current report and return repair/validation/recheck',
                 'B11 execute previous A11 project handoff', 'Member independent checks', 'E13 complete matrix and final gate', 'E14 merged-candidate acceptance'])
    save(out / 'summary.json', summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    cmd('runtime-scan', ['python3', 'labs/e13e14/scan_runtime_logs.py', str(out)])
    return summary

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--base', required=True)
    parser.add_argument('--target', required=True)
    parser.add_argument('--archive-sha256', required=True)
    args = parser.parse_args()
    execute(args.project, args.out, args.base, args.target, args.archive_sha256)
