"""Reproduce Issue #39 against the checked-out E11 public foundation."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PERSONAL_FILES = [
    'scripts/e11e12/run_issue39.py',
    'scripts/e11e12/verify_issue39_report.py',
    'tests/e11e12/test_231880027_refresh_reuse.py',
    'labs/e11e12/test_231880027_report_consumption.py',
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def container_path(path):
    return '/course/' + path.relative_to(ROOT).as_posix()


def findings(items):
    return sorted((x['type'], x['target'], x['dependency'])
                  for x in items if x['target'] in ('main.o', 'helper.o'))


def graph(path):
    edges = json.loads(path.read_text())
    return {target: sorted({edge['dependency'] for edge in edges
                            if edge['target'] == target})
            for target in ('main.o', 'helper.o')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if not (ROOT / 'run_e11e12.py').is_file():
        parser.error('E11 public foundation is required in this checkout')
    out = (ROOT / args.out).resolve()
    if not out.is_relative_to(ROOT / 'work') or out == ROOT / 'work':
        parser.error('--out must be a fresh directory under work/')
    if out.exists():
        parser.error('output already exists; preserve it and choose a new directory')
    dataset = ROOT / 'data' / ('issue39-' + out.name)
    if dataset.exists():
        parser.error('personal dataset already exists')
    out.mkdir(parents=True)
    dataset.mkdir(parents=True)

    def run(name, argv, expected=0):
        write(out / 'commands' / (name + '.command.json'),
              {'argv': argv, 'cwd': str(ROOT), 'expected_exit_code': expected})
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=300)
        (out / 'commands' / (name + '.stdout.log')).write_text(result.stdout)
        (out / 'commands' / (name + '.stderr.log')).write_text(result.stderr)
        write(out / 'commands' / (name + '.result.json'), {'exit_code': result.returncode})
        if result.returncode != expected:
            raise RuntimeError(name + ': unexpected exit code; see commands/')
        return result.stdout

    sid = subprocess.check_output(['git', 'config', '--local', 'user.name'],
                                  cwd=ROOT, text=True).strip()
    image = 'course-e11e12:' + sid
    docker = ['docker', 'run', '--rm', '--network', 'none', '--cap-add', 'SYS_PTRACE',
              '--user', f'{os.getuid()}:{os.getgid()}', '-e', 'HOME=/tmp',
              '-e', 'PYTHONDONTWRITEBYTECODE=1',
              '-e', 'PYTHONPATH=/course/labs/e11e12:/course/labs/e8e10:/app',
              '-v', str(ROOT) + ':/course', '-w', '/course', image]
    write(out / 'source.json', {
        'checked_out_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                   cwd=ROOT, text=True).strip(),
        'personal_files_sha256': {name: digest(ROOT / name) for name in PERSONAL_FILES},
    })
    for name in PERSONAL_FILES:
        target = out / 'source' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    run('image', ['docker', 'image', 'inspect', image])
    run('tools', docker + ['python3', '-c',
        "import platform,subprocess;print(platform.platform());"
        "[subprocess.run(c,check=True) for c in "
        "[['python3','--version'],['gcc','--version'],['make','--version'],"
        "['git','--version'],['strace','--version']]]"])
    run('contracts', ['python3', 'scripts/validate_e11e12_contract.py'])
    run('public-and-personal-tests', ['python3', 'run_e11e12.py', 'test'])
    run('e8e10-regression', docker + ['python3', '-m', 'unittest', 'discover',
                                     '-s', 'labs/e8e10', '-p', 'test_profile.py', '-v'])
    prepare = """
import hashlib,json,shutil,sys
from pathlib import Path
from lab import fixture,commit,run
p=Path(sys.argv[1]);out=Path(sys.argv[2]);fixture(p)
(p/'helper.c').write_text('#include "config.h"\\nint helper(void){return 0;}\\n')
def state(name):
    sha=commit(p,'student 231880027: E11 '+name)
    folder=out/'inputs'/name;folder.mkdir(parents=True)
    files=[x for x in p.iterdir() if x.is_file() and x.suffix in ['.c','.h']]
    files += [p/'Makefile',p/'.gitignore']
    for x in files: shutil.copyfile(x,folder/x.name)
    (folder/'sha256.json').write_text(json.dumps({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in files},indent=2))
    (folder/'commit.txt').write_text(sha+'\\n')
    return sha
base=state('base')
(p/'config.h').write_text('#include "extra.h"\\n#define VALUE 1\\n')
header=state('header')
(p/'helper.c').write_text('#include "config.h"\\nint helper(void){return 0+0;}\\n')
body=state('body')
(out/'dataset.json').write_text(json.dumps({'source':'personal course-generated shared-header fixture','base':base,'header':header,'body':body},indent=2))
(out/'fixture-history.log').write_text(run(['git','log','--format=fuller','--patch'],p))
run(['git','bundle','create',str(out/'fixture.bundle'),'--all'],p)
"""
    run('prepare', docker + ['python3', '-c', prepare,
                             container_path(dataset / 'repo'), container_path(out)])
    states = json.loads((out / 'dataset.json').read_text())
    requests = {
        'header': {'mode': 'e11-a', 'repo': container_path(dataset / 'repo'),
                   'base': states['base'], 'target': states['header']},
        'reuse': {'mode': 'e11-a', 'repo': container_path(dataset / 'repo'),
                  'base': states['header'], 'target': states['body']},
    }
    for name, request in requests.items():
        path = dataset / (name + '.json')
        write(path, request)
        run(name, ['python3', 'run_e11e12.py', 'run',
                   '--request', str(path.relative_to(ROOT)),
                   '--out', str((out / name).relative_to(ROOT))])

    declared = {'main.o': ['main.c', 'unused.h'], 'helper.o': ['helper.c']}
    base_actual = {'main.o': ['config.h', 'main.c'], 'helper.o': ['config.h', 'helper.c']}
    actual = {'main.o': ['config.h', 'extra.h', 'main.c'],
              'helper.o': ['config.h', 'extra.h', 'helper.c']}
    base_findings = sorted([('MISSING', 'main.o', 'config.h'),
                            ('MISSING', 'helper.o', 'config.h'),
                            ('REDUNDANT', 'main.o', 'unused.h')])
    expected = sorted(base_findings + [('MISSING', target, 'extra.h')
                                       for target in ('main.o', 'helper.o')])
    summaries = {}
    for name, request in requests.items():
        folder = out / name
        result = json.loads((folder / 'result.json').read_text())
        incremental = json.loads((folder / 'incremental-report.json').read_text())
        baseline = json.loads((folder / 'baseline-cache.json').read_text())
        assert result['status'] == 'SUCCEEDED', result
        assert (result['base_commit'], result['target_commit']) == (request['base'], request['target'])
        assert result['schema_version'] == 'e11e12-1'
        assert incremental['schema_version'] == 'e8e10-1'
        assert incremental['commit'] == request['target']
        assert baseline['commit'] == request['base']
        assert baseline['actual'] == (base_actual if name == 'header' else actual)
        assert findings(baseline['findings']) == (base_findings if name == 'header' else expected)
        assert incremental['actual'] == actual
        assert incremental['declared'] == declared
        assert findings(incremental['findings']) == expected
        assert graph(folder / 'baseline-full/actual-graph.json') == baseline['actual']
        assert graph(folder / 'target-full/actual-graph.json') == actual
        assert graph(folder / 'target-full/declared-graph.json') == declared
        reference = json.loads((folder / 'target-full/findings.json').read_text())
        assert reference['status'] == 'SUCCEEDED' and reference['build_exit_code'] == 0
        assert findings(reference['findings']) == expected
        assert incremental['refreshed'] == (['main.o', 'helper.o'] if name == 'header' else [])
        assert incremental['reused'] == ([] if name == 'header' else ['main.o', 'helper.o'])
        assert incremental['added'] == ([['MISSING', 'helper.o', 'extra.h'],
                                         ['MISSING', 'main.o', 'extra.h']] if name == 'header' else [])
        assert incremental['resolved'] == []
        for stage in result['stages']:
            envelope = json.loads((folder / stage['artifact']['artifact_id']).read_text())
            assert envelope['commit'] == (request['base'] if envelope['kind'] == 'full-check' else request['target'])
            for field in ['job_id', 'trace_id', 'configuration_id', 'schema_version']:
                assert envelope[field] == result[field]
            assert digest(folder / stage['artifact']['artifact_id']) == stage['artifact']['sha256']
        for artifact in result['artifacts']:
            path = folder / artifact['artifact_id']
            assert artifact['uri'] == f"artifact://{result['job_id']}/{artifact['artifact_id']}"
            assert digest(path) == artifact['sha256']
            assert path.stat().st_size == artifact['bytes']
            assert artifact['configuration_id'] == result['configuration_id']
        output = run(name + '-program', docker + [container_path(folder / 'target-full/project/app')])
        assert output.strip() == '1'
        summaries[name] = {key: result[key] for key in [
            'base_commit', 'target_commit', 'configuration_id', 'schema_version', 'job_id', 'trace_id']}
        summaries[name].update(refreshed=incremental['refreshed'], reused=incremental['reused'],
                               findings=incremental['findings'])

    before = json.loads((out / 'inputs/base/sha256.json').read_text())
    header = json.loads((out / 'inputs/header/sha256.json').read_text())
    body = json.loads((out / 'inputs/body/sha256.json').read_text())
    assert [x for x in before if before[x] != header[x]] == ['config.h']
    assert [x for x in header if header[x] != body[x]] == ['helper.c']
    original = out / 'header/incremental-check.json'
    tampered = out / 'tampered-incremental-check.json'
    tampered.write_bytes(original.read_bytes() + b'\n')
    cases = [
        ('current', original, digest(original), states['header'], 'incremental-check', None),
        ('stale', original, digest(original), states['body'], 'incremental-check', 'STALE_REPORT'),
        ('wrong-baseline', out / 'header/full-check.json', digest(out / 'header/full-check.json'),
         states['header'], 'full-check', 'STALE_REPORT'),
        ('tampered', tampered, digest(original), states['header'],
         'incremental-check', 'ARTIFACT_HASH_MISMATCH'),
    ]
    rejection = {}
    for name, path, sha, commit, kind, code in cases:
        response = out / 'consumption' / (name + '.json')
        run('consume-' + name, docker + [
            'python3', 'scripts/e11e12/verify_issue39_report.py',
            '--report', container_path(path), '--sha256', sha, '--commit', commit,
            '--kind', kind, '--out', container_path(response)], expected=1 if code else 0)
        value = json.loads(response.read_text())
        assert value['accepted'] == (code is None)
        assert value['status'] == ('FAILED' if code else 'SUCCEEDED')
        if code:
            assert value['error']['code'] == code
        rejection[name] = value
    write(out / 'verification.json', {'passed': True, 'scenarios': summaries,
          'consumption': rejection, 'scope': 'E11-A and personal consumer at recorded checkout SHA'})
    print(json.dumps({'out': str(out), 'passed': True}, indent=2))


if __name__ == '__main__':
    main()
