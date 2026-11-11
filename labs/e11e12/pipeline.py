"""Compose the existing E5-E10 teaching components using versioned artifacts."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'labs/e8e10'), str(ROOT / 'labs/e11e12/vendor'), '/app']
from lab import scan, patch, validate

COMMIT_RE = re.compile(r'^[0-9a-fA-F]{40}$')
MODES = {'e11-a', 'e11-b', 'e12'}

class Failure(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)

def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    temporary.replace(path)

def artifact(path, out, job_id):
    relative = path.relative_to(out).as_posix()
    if 'actual-graph' in relative:
        kind = 'ACTUAL_GRAPH'
    elif 'declared-graph' in relative:
        kind = 'DECLARED_GRAPH'
    elif relative.endswith('.patch'):
        kind = 'PATCH'
    elif relative.endswith('.log') or '/trace/' in relative:
        kind = 'BUILD_LOG'
    elif relative.endswith('.json'):
        kind = 'ERROR_REPORT'
    else:
        kind = 'TEST_RESULT'
    media_type = 'application/json' if relative.endswith('.json') else (
        'text/x-diff' if relative.endswith('.patch') else 'text/plain'
    )
    data = path.read_bytes()
    return {
        'artifact_id': relative,
        'type': kind,
        'uri': f'artifact://{job_id}/{relative}',
        'media_type': media_type,
        'producer_job_id': job_id,
        'sha256': hashlib.sha256(data).hexdigest(),
        'bytes': len(data),
    }


def configuration_id():
    """Fingerprint the locked container environment without leaking local paths."""
    lock = Path('/opt/toolchain.lock')
    if lock.is_file():
        material = lock.read_bytes()
    else:
        paths = [
            ROOT / 'labs/e11e12/environment/services/buildchecker/Dockerfile',
            ROOT / 'labs/e11e12/environment/requirements-dev.lock',
        ]
        material = b''.join(
            path.relative_to(ROOT).as_posix().encode() + b'\0' + path.read_bytes() + b'\0'
            for path in paths if path.is_file()
        )
    return 'cfg-e11e12-' + hashlib.sha256(material).hexdigest()[:16]


def data_path(value, field):
    if not isinstance(value, str) or not value:
        raise Failure('INVALID_REQUEST', f'{field} must be a non-empty path')
    data_root = ROOT / 'data'
    if data_root.is_symlink():
        raise Failure('INVALID_REQUEST', 'data/ must not be a symlink')
    path = Path(value).resolve()
    if not path.is_relative_to(data_root.resolve()):
        raise Failure('INVALID_REQUEST', f'{field} must be under data/')
    return path


def validate_request(request):
    if not isinstance(request, dict):
        raise Failure('INVALID_REQUEST', 'Request must be a JSON object')
    mode = request.get('mode')
    if mode not in MODES:
        raise Failure('INVALID_REQUEST', 'Unknown mode')
    if not all(isinstance(request.get(k), str) and request[k] for k in ('repo', 'base', 'target')):
        raise Failure('INVALID_REQUEST', 'repo, base and target are required')
    if not COMMIT_RE.fullmatch(request['base']) or not COMMIT_RE.fullmatch(request['target']):
        raise Failure('INVALID_REQUEST', 'base and target must be full 40-character commit SHAs')
    if request['base'].lower() == request['target'].lower():
        raise Failure('INVALID_REQUEST', 'base and target must identify different commits')
    repo = data_path(request['repo'], 'repo')
    if not repo.is_dir():
        raise Failure('INVALID_REQUEST', 'Repository does not exist')
    if mode in ('e11-b', 'e12'):
        candidate = data_path(request.get('candidate'), 'candidate')
        if not candidate.is_file():
            raise Failure('INVALID_REQUEST', 'candidate does not exist')
    if mode == 'e11-b':
        fixed = data_path(request.get('fixed_report'), 'fixed_report')
        if not fixed.is_file():
            raise Failure('INVALID_REQUEST', 'fixed_report does not exist')
    if mode == 'e12' and 'fixed_report' in request:
        raise Failure('INVALID_REQUEST', 'E12 must consume the current incremental report, not fixed_report')
    if 'expected_output' in request and (not isinstance(request['expected_output'], str) or not request['expected_output']):
        raise Failure('INVALID_REQUEST', 'expected_output must be a non-empty string')
    timeout = request.get('build_timeout', 600)
    if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout < 1:
        raise Failure('INVALID_REQUEST', 'build_timeout must be a positive integer')
    return request

def check_envelope(report, commit, kind=None):
    if report.get('schema_version') != 'e11e12-1':
        raise Failure('SCHEMA_MISMATCH', 'Expected e11e12-1')
    if report.get('commit') != commit:
        raise Failure('STALE_REPORT', 'Report belongs to another commit')
    if report.get('status') != 'SUCCEEDED':
        raise Failure('UPSTREAM_FAILED', 'Upstream stage did not succeed')
    if kind and report.get('kind') != kind:
        raise Failure('ARTIFACT_TYPE_MISMATCH', kind)

def load_artifact(path, expected_sha256):
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=expected_sha256:
        raise Failure('ARTIFACT_HASH_MISMATCH','Artifact content changed during transfer')
    return json.loads(data)

def command(argv, cwd, log):
    log.parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=120)
    log.write_text(p.stdout+p.stderr, encoding='utf-8')
    if p.returncode:
        raise Failure('COMMAND_FAILED', f'{argv[0]} failed; see {log.name}')
    return p.stdout.strip()

def snapshot(repo, revision, dest, logs):
    sha = command(['git','rev-parse','--verify',revision+'^{commit}'], repo, logs/(dest.name+'-resolve.log'))
    command(['git','clone','--no-hardlinks','--no-checkout',str(repo),str(dest)], repo, logs/(dest.name+'-clone.log'))
    command(['git','checkout','--detach',sha], dest, logs/(dest.name+'-checkout.log'))
    # E8-E10 profile; fail early instead of silently ignoring other targets.
    names = {p.name for p in dest.glob('*.c')}
    if names != {'main.c','helper.c'} or not (dest/'config.h').is_file():
        raise Failure('UNSUPPORTED_PROJECT', 'Expected main.c/helper.c/config.h and explicit Make rules')
    return sha

def full(project, folder, timeout=120):
    from buildchecker.fullcheck import full_check
    report = full_check(project, folder, timeout=timeout)
    if report.get('status') != 'SUCCEEDED':
        raise Failure('FULL_CHECK_FAILED', str(report.get('error', report.get('error_code'))))
    return report

def normalized(findings):
    return sorted((f['type'],f['target'],f['dependency']) for f in findings if f['target'] in ('main.o','helper.o'))

def execute(request, out, job_id=None, trace_id=None):
    job_id = job_id or 'job-'+uuid.uuid4().hex
    trace_id = trace_id or 'trace-'+uuid.uuid4().hex
    if out.exists() and any(out.iterdir()):
        raise Failure('OUTPUT_EXISTS', 'Use a fresh output directory')
    out.mkdir(parents=True, exist_ok=True)
    result = {'schema_version':'e11e12-1','job_id':job_id,'trace_id':trace_id,'status':'RUNNING','stages':[]}
    result['configuration_id'] = configuration_id()
    save(out/'request.json',request)
    def stage(name, commit, payload, files=()):
        envelope = {'schema_version':'e11e12-1','job_id':job_id,'trace_id':trace_id,'kind':name,
                    'commit':commit,'configuration_id':result['configuration_id'],
                    'status':'SUCCEEDED','data':payload,
                    'artifacts':[dict(artifact(p,out,job_id),commit=commit,
                                      configuration_id=result['configuration_id']) for p in files]}
        save(out/(name+'.json'),envelope)
        result['stages'].append({'name':name,'artifact':artifact(out/(name+'.json'),out,job_id)})
        return envelope
    try:
        validate_request(request)
        mode=request['mode']
        repo=data_path(request['repo'], 'repo')
        base=out/'base-project'; target=out/'target-project'
        base_sha=snapshot(repo,request['base'],base,out/'logs')
        target_sha=snapshot(repo,request['target'],target,out/'logs')
        result.update(base_commit=base_sha,target_commit=target_sha)
        if mode in ('e11-b','e12'):
            from draft.autobuild import auto_build
            candidate=data_path(request['candidate'], 'candidate')
            draft=auto_build(target,candidate,out/'draft-build',request.get('expected_output','1'),timeout=request.get('build_timeout',600))
            if draft['status']!='SUCCEEDED':
                raise Failure('DRAFT_FAILED',draft.get('error','Inspect draft-build logs'))
            stage('draft',target_sha,draft,[out/'draft-build/result.json'])
        if mode in ('e11-a','e12'):
            base_full=full(base,out/'baseline-full',request.get('build_timeout',600))
            old=scan(base)
            edges=json.loads((out/'baseline-full/actual-graph.json').read_text())
            projected={t:sorted({e['dependency'] for e in edges if e['target']==t}) for t in ('main.o','helper.o')}
            if projected != old['actual']:
                raise Failure('GRAPH_MISMATCH','BuildChecker baseline differs from GCC observations')
            old['actual']=projected
            save(out/'baseline-cache.json',old)
            baseline=stage('full-check',base_sha,base_full,[out/'baseline-full/actual-graph.json',out/'baseline-full/findings.json',out/'baseline-cache.json'])
            check_envelope(baseline,base_sha,'full-check')
            current=scan(target,old)
            save(out/'incremental-report.json',current)
            reference=full(target,out/'target-full',request.get('build_timeout',600))
            if normalized(reference['findings']) != normalized(current['findings']):
                raise Failure('FINDINGS_MISMATCH','Incremental/full object-target findings differ')
            md_envelope=stage('incremental-check',target_sha,current,[out/'incremental-report.json',out/'target-full/findings.json'])
        elif mode == 'e11-b':
            # E11-B still consumes a fixed MD input, separately from A's live output.
            fixed=data_path(request['fixed_report'], 'fixed_report')
            envelope=json.loads(fixed.read_text(encoding='utf-8'))
            check_envelope(envelope,target_sha,'fixed-md')
            current=envelope['data']
            if current.get('commit') != target_sha:
                raise Failure('STALE_REPORT','Fixed report data commit mismatch')
            save(out/'fixed-md-input.json',envelope)
            md_envelope=stage('fixed-md',target_sha,current,[out/'fixed-md-input.json'])
        if mode in ('e11-b','e12'):
            reference=result['stages'][-1]['artifact']
            md_envelope=load_artifact(out/(md_envelope['kind']+'.json'),reference['sha256'])
            check_envelope(md_envelope,target_sha)
            current=md_envelope['data']
            before=(target/'Makefile').read_bytes()
            diff,edits=patch(target,current)
            if not diff:
                raise Failure('NO_MISSING_DEPENDENCY','No MD to repair')
            patchfile=out/'candidate.patch';patchfile.write_text(diff,encoding='utf-8')
            save(out/'repair-plan.json',edits)
            stage('repair',target_sha,{'edits':edits,'input_report':artifact(out/(md_envelope['kind']+'.json'),out,job_id)},[patchfile,out/'repair-plan.json'])
            verdict=validate(target,patchfile,out/'validation')
            if not verdict['accepted']:
                raise Failure('REPAIR_REJECTED',str(verdict))
            final=full(target,out/'final-full')
            if any(f['type']=='MISSING' for f in final['findings']):
                (target/'Makefile').write_bytes(before)
                raise Failure('RECHECK_FAILED','MD remains; working-copy declaration restored')
            stage('recheck',target_sha,{'validation':verdict,'findings':final['findings'],'patched_makefile_sha256':hashlib.sha256((target/'Makefile').read_bytes()).hexdigest()},[out/'validation/validation.json',out/'final-full/findings.json'])
        result['status']='SUCCEEDED'
    except (Failure,ValueError,OSError,KeyError,subprocess.TimeoutExpired) as exc:
        result.update(status='TIMED_OUT' if isinstance(exc,subprocess.TimeoutExpired) else 'FAILED',error={'code':getattr(exc,'code','EXECUTION_FAILED'),'message':str(exc)})
    private_parts = {'base-project', 'target-project', 'sandbox', 'project'}
    result['artifacts'] = [
        dict(artifact(p, out, job_id),
             commit=result.get('base_commit') if (
                 # Snapshot logs describe the revision checked out for that side.
                 p.relative_to(out).parent == Path('logs')
                 and p.name.startswith('base-project-')
             ) or any(
                 part in {'baseline-full', 'base-project', 'baseline-cache.json', 'full-check.json'}
                 for part in p.relative_to(out).parts
             ) else result.get('target_commit'),
             configuration_id=result['configuration_id'])
        for p in sorted(out.rglob('*'))
        if p.is_file()
        and '.git' not in p.parts
        and not p.is_symlink()
        and p.name != 'request.json'
        and not any(part in private_parts for part in p.relative_to(out).parts)
    ]
    save(out/'result.json',result)
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();r=execute(json.loads(a.request.read_text(encoding='utf-8')),a.out.resolve());print(json.dumps(r,ensure_ascii=False,indent=2));return 0 if r['status']=='SUCCEEDED' else 1

if __name__=='__main__':raise SystemExit(main())
