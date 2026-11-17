"""Package the complete B11 cJSON A-run, keeping raw evidence immutable."""
import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path

from handoff_a_to_b import make_handoff
from verify_evidence import verify

ROOT = Path(__file__).resolve().parents[2]
KIT = Path(__file__).resolve().parent
BASE = 'cf0d87a095becada87336ed786f11070e9a037b5'
TARGET = 'f0c8fa4f812abe50964956cd0580ab963430ba35'

def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def security_review(run, repo):
    """Review exact upstream fixture bytes; never suppress arbitrary token findings."""
    copies = ('A-result/base-project', 'A-result/target-project',
              'A-result/baseline-full/project', 'A-result/target-full/project',
              'base-functional', 'target-functional')
    expected = {}
    prefix = 'tests/unity/test/testdata/'
    request_id = '768c7149-c3fb-f704-71a2-63918d9195b2'
    example_field = 'Postman-' + 'Token: ' + request_id
    for name, linenos in [('testRunnerGenerator.c', (115, 127)), ('testRunnerGeneratorWithMocks.c', (116, 128))]:
        upstream = prefix + name
        raw = subprocess.check_output(['git', 'show', TARGET + ':' + upstream], cwd=repo)
        if raw != subprocess.check_output(['git', 'show', BASE + ':' + upstream], cwd=repo):
            raise ValueError('Fixture changed between peer commits; review again')
        lines = raw.decode().splitlines()
        for lineno in linenos:
            if example_field not in lines[lineno - 1]:
                raise ValueError('Unexpected fixture token')
        for copy in copies:
            relative = copy + '/' + upstream
            if (run / relative).read_bytes() != raw:
                raise ValueError('Received source differs from fixed Git fixture')
            for lineno in linenos:
                expected[(relative, lineno)] = dict(path=relative, line=lineno, sha256=digest(raw),
                    classification='UPSTREAM_STATIC_HTTP_TEST_FIXTURE_NOT_CONFIGURED_CREDENTIAL')
    received = []
    for line in (run / 'runtime-scan.stdout.log').read_text().splitlines():
        if not line.startswith('FOUND '):
            continue
        match = re.fullmatch(r'FOUND (.+):(\d+) secret assignment 768c\*\*\*', line)
        if not match:
            raise ValueError('Unreviewed security finding')
        # Original evidence records the cloud prefix. Match only this exact run basename.
        marker = '/' + run.name + '/'
        if marker not in match[1]:
            raise ValueError('Security finding outside the received run')
        relative = match[1].split(marker, 1)[1]
        key = (relative, int(match[2]))
        if key not in expected or key in received:
            raise ValueError('Unreviewed or repeated finding')
        received.append(key)
    if set(received) != set(expected) or not (run / 'runtime-scan.stdout.log').read_text().rstrip().endswith('hits=24 errors=0'):
        raise ValueError('Security findings not completely accounted for')
    return dict(status='REVIEWED_KNOWN_UPSTREAM_FIXTURE_HITS', raw_scan_exit_code=1, raw_hits=24,
        scope='Only this received run and the two unchanged fixed Git fixture files; no global allowlist',
        reviewed_by='A11 leader task with AI assistance; no B11 attestation',
        findings=[expected[key] for key in sorted(expected)])

def package(run, project, archive, out):
    run, project = run.resolve(), project.resolve()
    verified = verify(run / 'A-result')
    summary = json.loads((run / 'summary.json').read_text())
    if (summary['base'], summary['target']) != (BASE, TARGET) or summary['input_archive_sha256'] != digest(archive.read_bytes()):
        raise ValueError('Peer input/run identity mismatch')
    fixed = make_handoff(run / 'A-result/result.json', TARGET)
    if json.loads((run / 'fixed-md.json').read_text()) != fixed:
        raise ValueError('Handoff source mismatch')
    review = security_review(run, project / 'repo')
    entries = {}
    for path in sorted(run.rglob('*')):
        if path.is_symlink():
            raise ValueError('Do not package symlinks')
        if path.is_file():
            entries['evidence/' + path.relative_to(run).as_posix()] = path.read_bytes()
    entries['fixed-md.json'] = (run / 'fixed-md.json').read_bytes()
    entries['verification.json'] = encoded(verified)
    entries['security/review.json'] = encoded(review)
    entries['received/' + archive.name] = archive.read_bytes()
    for name, key in [('cjson-b-e13.bundle', 'bundle_sha256'), ('cjson-b-e13.Dockerfile', 'candidate_sha256')]:
        raw = (project / name).read_bytes()
        if digest(raw) != summary[key]:
            raise ValueError('Original peer file changed')
        entries['received/' + name] = raw
    # Scan actual command logs, reports and trace, separately from copied upstream source.
    paths = [p for p in run.iterdir() if p.is_file()]
    result = json.loads((run / 'A-result/result.json').read_text())
    paths += [run / 'A-result/result.json', run / 'A-result/request.json']
    for item in result['artifacts']:
        prefix = 'artifact://' + result['job_id'] + '/'
        if not item['uri'].startswith(prefix):
            raise ValueError('Unexpected report URI')
        paths.append(run / 'A-result' / item['uri'][len(prefix):])
    argv = ['python3', str(KIT / 'scan_runtime_logs.py'), *[str(p) for p in sorted(set(paths))]]
    scan = subprocess.run(argv, capture_output=True, text=True, check=False)
    entries['security/runtime-logs.stdout.log'] = scan.stdout.encode()
    entries['security/runtime-logs.stderr.log'] = scan.stderr.encode()
    entries['security/runtime-logs-command.json'] = encoded(dict(argv=argv, exit_code=scan.returncode,
        scope='Actual outer command logs, reports and the manifest artifacts; not copied source directories'))
    if scan.returncode != 0:
        raise ValueError('Actual log/report scan requires review')
    entries['USAGE.md'] = (ROOT / 'docs/e13-e14/B11-cJSON当次结果回传说明.md').read_bytes()
    entries['AI_USAGE.md'] = (ROOT / 'AI_USAGE.md').read_bytes()
    entries['分工与完成记录.md'] = (ROOT / 'docs/e13-e14/分工与完成记录.md').read_bytes()
    for name in ('verify_package.py', 'verify_evidence.py', 'handoff_a_to_b.py', 'run_peer_a.py', 'scan_runtime_logs.py'):
        entries[name] = (KIT / name).read_bytes()
    entries['SHA256SUMS.json'] = encoded({name: digest(raw) for name, raw in sorted(entries.items())})
    with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED) as output:
        for name, raw in sorted(entries.items()):
            output.writestr(name, raw)
    with zipfile.ZipFile(out) as output:
        if output.testzip() is not None or any(output.read(name) != raw for name, raw in entries.items()):
            raise ValueError('Written ZIP differs from source evidence')
    return dict(file=str(out), bytes=out.stat().st_size, entries=len(entries), sha256=digest(out.read_bytes()), verification=verified)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--received-archive', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(package(args.run, args.project, args.received_archive, args.out), ensure_ascii=False, indent=2))
