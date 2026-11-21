"""Issue #45 personal E14 replay with recorded HTTP payloads; public code unchanged."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time

from verify_peer import BASE, TARGET, read, require, sha, verify_e14

ROOT = Path(__file__).resolve().parents[2]


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def execute(out):
    require(out.is_relative_to(ROOT / 'work') and not out.exists(), 'Fresh work/ directory required')
    out.mkdir(parents=True)
    save(out / 'personal-sources.json', {str(p.relative_to(ROOT)): sha(p)
         for p in Path(__file__).parent.glob('*.py')})
    env = dict(os.environ, E14_ROOT=str(ROOT), E14_IMAGE='course-e11e12:231880027')
    project = 'e14-45-231880027'
    events = []

    def command(name, argv, timeout=600):
        start = time.monotonic()
        with (out / (name + '.stdout.log')).open('w') as stdout, (out / (name + '.stderr.log')).open('w') as stderr:
            p = subprocess.run(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr, timeout=timeout)
        events.append(dict(name=name, argv=argv, exit_code=p.returncode, elapsed_s=time.monotonic() - start))
        save(out / 'commands.json', events)
        require(p.returncode == 0, name + ' failed; inspect raw logs')
        return (out / (name + '.stdout.log')).read_text()

    config = json.loads(command('public-compose-config', ['docker', 'compose', '-f', 'labs/e13e14/compose.yaml', 'config', '--format', 'json']))
    ports = dict(buildchecker=18541, echecker=18542, draft=18543, mdfixer=18544)
    for role, port in ports.items():
        config['services'][role]['ports'] = [dict(target=8080, published=str(port), host_ip='127.0.0.1', protocol='tcp')]
    config['name'] = project
    config['networks']['default']['name'] = project + '_default'
    save(out / 'compose.json', config)
    compose = ['docker', 'compose', '-f', str(out / 'compose.json'), '-p', project]
    inputs = ROOT / 'data/issue45-cjson'
    provenance = {}
    for name in ('candidate.Dockerfile', 'Dockerfile.broken'):
        source = inputs / name
        target = inputs / (out.name + '-' + name)
        require(not target.exists(), 'Preserve earlier input')
        content = source.read_text().replace('FROM python:', 'FROM m.daocloud.io/docker.io/library/python:', 1)
        target.write_text(content)
        provenance[name] = dict(original_sha256=sha(source), replay_sha256=sha(target),
                                original=str(source), replay=str(target),
                                change='Registry mirror only; pinned digest retained')
    save(out / 'input-provenance.json', provenance)
    request = dict(mode='e12', project_profile='cjson', repo='/course/data/issue45-cjson/repo',
                   base=BASE, target=TARGET, candidate='/course/data/issue45-cjson/' + out.name + '-candidate.Dockerfile',
                   broken_dockerfile='/course/data/issue45-cjson/' + out.name + '-Dockerfile.broken',
                   expected_output='1', build_timeout=600)
    save(out / 'request.json', request)
    command('source-sha', ['git', 'rev-parse', 'HEAD'])
    command('source-status', ['git', 'status', '--short', '--branch'])
    before = command('input-status-before', ['git', '-C', str(inputs / 'repo'), 'status', '--porcelain'])
    head = command('input-head-before', ['git', '-C', str(inputs / 'repo'), 'rev-parse', 'HEAD'])
    require(not before.strip() and head.strip() == TARGET, 'Dirty/wrong source input')
    command('image', ['docker', 'image', 'inspect', 'course-e11e12:231880027'])
    spec = importlib.util.spec_from_file_location('issue45_public_orchestrate', ROOT / 'labs/e13e14/orchestrate.py')
    public = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(public)
    public.PORTS = ports  # Personal loopback ports, no edit to the shared entry.
    original = public.call

    def recorded_call(role, payload, evidence):
        save(evidence.with_suffix('.request.json'), dict(role=role, url='http://127.0.0.1:' + str(ports[role]) + '/v1/run', payload=payload))
        return original(role, payload, evidence)

    public.call = recorded_call
    attempted = False
    try:
        attempted = True
        command('compose-up', compose + ['up', '-d', '--wait'], 90)
        command('compose-health', compose + ['ps', '--format', 'json'])
        result = public.execute(request, out / 'run')
        save(out / 'run-exit.json', dict(exit_code=0 if result['status'] == 'SUCCEEDED' else 1, status=result['status']))
        require(result['status'] == 'SUCCEEDED', 'Public E14 run failed; preserve result')
        verdict = verify_e14(out / 'run', operator='231880027')
        require(verdict['repair_request_recorded'] is True, 'Personal run omitted repair request')
        save(out / 'association-check.json', verdict)
        require(command('input-head-after', ['git', '-C', str(inputs / 'repo'), 'rev-parse', 'HEAD']) == head, 'Input HEAD changed')
        require(command('input-status-after', ['git', '-C', str(inputs / 'repo'), 'status', '--porcelain']) == before, 'Input changed')
        print(json.dumps(verdict, indent=2), flush=True)
    finally:
        if attempted:
            try:
                command('service-logs', compose + ['logs', '--no-color'])
            finally:
                command('compose-down', compose + ['down'], 90)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    execute((ROOT / args.out).resolve())
