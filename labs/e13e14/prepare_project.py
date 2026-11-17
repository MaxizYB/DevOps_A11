"""Create A11's independently maintained project, actual commits and offline bundle."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = Path(__file__).resolve().parent / 'projects/a11-config-probe'
BRANCH = 'feat/43-a11-exchange-project'
IMAGE = 'm.daocloud.io/docker.io/library/python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f'

def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def command(argv, cwd, log=None):
    p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=120)
    if log is not None:
        log.write_text(p.stdout + p.stderr, encoding='utf-8')
    if p.returncode:
        raise ValueError(f'Command failed: {argv[0]}; inspect {log or p.stderr}')
    return p.stdout.strip()

def prepare(out, image=IMAGE):
    out = out.resolve()
    if not out.is_relative_to((ROOT / 'data').resolve()) or out == (ROOT / 'data').resolve():
        raise ValueError('Use a new child directory in data/')
    if out.exists():
        raise ValueError('Preserve the previous project/commits; choose a new output directory')
    if not re.fullmatch(r'[^\s]+@sha256:[0-9a-f]{64}', image):
        raise ValueError('Digest-pinned base image required')
    out.mkdir(parents=True)
    repo = out / 'repo'
    shutil.copytree(TEMPLATES / 'base', repo)
    broken = f'FROM {image.split("@", 1)[0]}\nWORKDIR /work\nCOPY . .\nRUN make app\nCMD ["./app"]\n'
    (repo / 'Dockerfile.broken').write_text(broken)
    (repo / 'README.md').write_text('# A11 configuration probe\n\n'
        'Derived from the course C/Make fixture. Maintained by A11 (241880439), with AI assistance.\n'
        'C0 tests default configuration; C1 adds group-policy validation and boundary tests.\n'
        'The target intentionally omits policy.h from helper.o prerequisites; unused.h is redundant.\n'
        'These controlled defects are test inputs, not claims of a general production application.\n'
        'Run: python3 test_project.py; make clean && make app && ./app. Expected output: 1.\n')
    command(['git', 'init', '-b', BRANCH], repo)
    command(['git', 'config', 'user.name', '241880439'], repo)
    command(['git', 'config', 'user.email', '241880439@users.noreply.github.com'], repo)
    command(['python3', 'test_project.py'], repo, out / 'C0-functional-tests.log')
    command(['git', 'add', '.'], repo)
    command(['git', 'commit', '-m', 'feat(a11-project): initialize configuration probe\n\nRefs #43'], repo)
    base = command(['git', 'rev-parse', 'HEAD'], repo)
    for source in (TEMPLATES / 'target').iterdir():
        if source.is_file():
            shutil.copy2(source, repo / source.name)
    command(['python3', 'test_project.py'], repo, out / 'C1-functional-tests.log')
    command(['git', 'add', '.'], repo)
    command(['git', 'commit', '-m', 'feat(a11-project): validate group policy with boundary tests\n\nRefs #43'], repo)
    target = command(['git', 'rev-parse', 'HEAD'], repo)
    command(['git', 'bundle', 'create', str(out / 'a11-project.bundle'), '--all'], repo)
    command(['git', 'bundle', 'verify', str(out / 'a11-project.bundle')], repo, out / 'bundle-verification.log')
    install = ('RUN sed -i "s|http://deb.debian.org|https://mirrors.tuna.tsinghua.edu.cn|g" /etc/apt/sources.list.d/debian.sources'
               ' && apt-get -o Acquire::ForceIPv4=true -o Acquire::Retries=3 update'
               ' && apt-get -o Acquire::ForceIPv4=true -o Acquire::Retries=3 install -y --no-install-recommends build-essential'
               ' && rm -rf /var/lib/apt/lists/*\n')
    candidate = broken.replace('FROM ' + image.split('@', 1)[0], 'FROM ' + image).replace('RUN make app', install + 'RUN make app')
    (out / 'candidate.Dockerfile').write_text(candidate)
    folder = '/course/' + out.relative_to(ROOT).as_posix()
    common = {'repo': folder + '/repo', 'base': base, 'target': target, 'build_timeout': 600}
    save(out / 'e11-a.json', dict(mode='e11-a', **common))
    save(out / 'e12.json', dict(mode='e12', **common, candidate=folder + '/candidate.Dockerfile', expected_output='1'))
    manifest = {'group': 'A11', 'owner': '241880439', 'repo_url': 'https://github.com/MaxizYB/DevOps_A11.git',
                'project_branch': BRANCH, 'base': base, 'target': target, 'project_origin': 'Course C/Make fixture evolved by A11',
                'maintenance_scope': 'New configuration-probe functionality, group validation, positive/negative/configuration tests; commits created in this run, not historical upstream maintenance',
                'candidate_source': 'Course dependency-install pattern adapted by A11; manual replay, no live model/API call',
                'expected_output': '1', 'build_timeout': 600,
                'expected_findings': [{'type': 'MISSING', 'target': 'helper.o', 'dependency': 'policy.h'},
                                      {'type': 'REDUNDANT', 'target': 'main.o', 'dependency': 'unused.h'}],
                'support': 'Two C sources main.c/helper.c, explicit Make object rules, GCC, config.h VALUE changes output 1 to 2',
                'source_commit': command(['git', 'rev-parse', 'HEAD'], ROOT),
                'files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (out / 'a11-project.bundle', out / 'candidate.Dockerfile')}}
    save(out / 'dataset.json', manifest)
    return manifest

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, default=ROOT / 'data/e13-a11-project')
    p.add_argument('--image', default=IMAGE)
    args = p.parse_args()
    print(json.dumps(prepare(args.out, args.image), ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
