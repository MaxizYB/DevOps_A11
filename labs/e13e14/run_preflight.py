"""Leader-only reference preflight; never claims peer execution or final RC acceptance."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'labs/e11e12'), str(ROOT/'labs/e8e10')]
from handoff_a_to_b import make_handoff
from verify_evidence import verify

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class Run:
    def __init__(self, folder):
        if folder.exists() or not folder.resolve().is_relative_to((ROOT/'work').resolve()):
            raise ValueError('Use a new directory below work/')
        self.root = folder
        folder.mkdir(parents=True)
        self.events = []

    def cmd(self, name, argv, expected=0, timeout=1800):
        start = time.time()
        env = dict(os.environ, PYTHONPATH=':'.join(str(ROOT/p) for p in ('labs/e11e12','labs/e8e10','labs/e11e12/vendor','labs/e11e12/environment/services/buildchecker')))
        with (self.root/(name+'.stdout.log')).open('w') as out, (self.root/(name+'.stderr.log')).open('w') as err:
            p = subprocess.run(argv, cwd=ROOT, stdout=out, stderr=err, env=env, timeout=timeout)
        record = dict(name=name, argv=argv, exit_code=p.returncode, expected_exit=expected,
                      matched=p.returncode==expected, started_unix=start, elapsed_s=time.time()-start)
        self.events.append(record)
        save(self.root/'commands.json', self.events)
        print(json.dumps(record, ensure_ascii=False), flush=True)
        return p.returncode

    def task(self, name, request, expected=0):
        self.cmd(name, ['python3','run_e11e12.py','run','--request',str(request.relative_to(ROOT)),
                       '--out',str((self.root/name).relative_to(ROOT))], expected)
        folder = self.root/name
        if expected==0 and (folder/'result.json').is_file():
            try:
                save(self.root/(name+'-verification.json'), verify(folder))
            except (ValueError, KeyError) as exc:
                save(self.root/(name+'-verification.json'), dict(status='FAIL', error=str(exc)))
        return folder

def e13(run, project):
    inputs = ROOT/'data'/('e13-leader-preflight-inputs-'+run.root.name)
    if inputs.exists():
        raise ValueError('Preserve previous preflight inputs')
    inputs.mkdir()
    run.cmd('old-tests', ['python3','run_e11e12.py','test'])
    run.cmd('new-tests', ['python3','-m','unittest','discover','-s','labs/e13e14/tests','-v'])
    a = run.task('a11-a', project/'e11-a.json')
    run.task('a11-e12', project/'e12.json')
    for name in ('H1-jsmn','H2-inih','H3-tiny-aes'):
        run.task(name, ROOT/'data/e13-upstream-student'/name/'request-e12.json')
    req = json.loads((project/'e12.json').read_text())
    fixed = inputs/'fixed-md.json'
    save(fixed, make_handoff(a/'result.json', req['target']))
    b = dict(req, mode='e11-b', fixed_report='/course/'+fixed.relative_to(ROOT).as_posix(),
             fixed_report_sha256=digest(fixed))
    save(inputs/'local-b.json', b)
    run.task('local-b-consume', inputs/'local-b.json')
    stale = dict(b, base=b['target'], target=b['base'])
    save(inputs/'stale.json', stale)
    old = run.task('C2-stale', inputs/'stale.json', 1)
    tampered = inputs/'tampered-fixed-md.json'
    tampered.write_bytes(fixed.read_bytes()+b'\n')
    save(inputs/'tampered.json', dict(b, fixed_report='/course/'+tampered.relative_to(ROOT).as_posix()))
    changed = run.task('C3-tampered', inputs/'tampered.json', 1)
    save(inputs/'timeout.json', dict(req, build_timeout=0.01))
    timed = run.task('C4-timeout', inputs/'timeout.json', 1)
    # Real invalid patch, validated in a copied checkout; original source must not move.
    from lab import validate
    source = project/'repo'
    before = subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'], text=True).strip()
    original = (source/'Makefile').read_bytes()
    bad = inputs/'invalid.patch'
    bad.write_text('not a patch\n')
    verdict = validate(source, bad, run.root/'C5-validation')
    after = subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'], text=True).strip()
    save(run.root/'C5-summary.json', dict(verdict=verdict, before=before, after=after,
         unchanged=before==after and original==(source/'Makefile').read_bytes()))
    probe = run.root/'C6-probe.log'
    probe.write_text('api_key = "' + 'sk-' + 'a'*24 + '"\n')
    before_probe = digest(probe)
    run.cmd('C6-hit', ['python3','labs/e13e14/scan_runtime_logs.py',str(probe)], 1)
    probe.write_text('clean log\n')
    run.cmd('C6-clean', ['python3','labs/e13e14/scan_runtime_logs.py',str(probe)])
    save(run.root/'C6-content-sha.json', dict(before=before_probe, after=digest(probe)))
    a_request = json.loads((project/'e11-a.json').read_text())
    save(inputs/'bad-base.json', dict(a_request, base='0'*40))
    failed = run.task('C7-failed', inputs/'bad-base.json', 1)
    good = run.task('C7-normal', project/'e11-a.json')
    run.cmd('residual-processes', ['ps','-eo','pid,ppid,args'])
    run.cmd('residual-containers', ['docker','ps','--no-trunc'])
    c2=json.loads((old/'result.json').read_text())
    c3=json.loads((changed/'result.json').read_text())
    c4=json.loads((timed/'result.json').read_text())
    c4inner=json.loads((timed/'draft-build/result.json').read_text())
    fail=json.loads((failed/'result.json').read_text())
    normal=json.loads((good/'result.json').read_text())
    summary = dict(scope='A11 leader reference on A11 project; NOT B11 execution, member acceptance, or RC gate',
       C1='LOCAL_ONLY_PEER_PENDING', C2=c2.get('error'), C3=c3.get('error'),
       C4=dict(outer=c4['status'], inner=c4inner['status']), C5=verdict,
       C7=dict(failed=fail['status'], normal=normal['status'], distinct=fail['job_id']!=normal['job_id'] and fail['trace_id']!=normal['trace_id']),
       C8='Run separately against actual asynchronous API; formal peer input pending')
    save(run.root/'summary.json',summary)

def e14(run, project):
    env = dict(os.environ, E14_ROOT=str(ROOT), E14_IMAGE='course-e11e12:241880439')
    os.environ.update({k:env[k] for k in ('E14_ROOT','E14_IMAGE')})
    compose = ['docker','compose','-f','labs/e13e14/compose.yaml','-p','e14-241880439']
    run.cmd('compose-config',compose+['config'])
    run.cmd('compose-up',compose+['up','-d','--wait'])
    run.cmd('compose-ps',compose+['ps','--format','json'])
    run.cmd('a11-compose',['python3','labs/e13e14/orchestrate.py','--request',str(project/'e12.json'),'--out',str(run.root/'a11-compose')])
    if (run.root/'a11-compose/result.json').exists():
        try:
            save(run.root/'a11-compose-verification.json',verify(run.root/'a11-compose'))
        except (ValueError,KeyError) as exc:
            save(run.root/'a11-compose-verification.json',dict(status='FAIL',error=str(exc)))
    request=json.loads((project/'e12.json').read_text())
    timeout=project/'e14-timeout-preflight.json'
    if timeout.exists():
        raise ValueError('Do not overwrite timeout input')
    save(timeout,dict(request,build_timeout=0.01))
    run.cmd('timeout',['python3','labs/e13e14/orchestrate.py','--request',str(timeout),'--out',str(run.root/'timeout')],1)
    run.cmd('recovery',['python3','labs/e13e14/orchestrate.py','--request',str(project/'e12.json'),'--out',str(run.root/'recovery')])
    if (run.root/'recovery/result.json').exists():
        try:
            save(run.root/'recovery-verification.json',verify(run.root/'recovery'))
        except (ValueError,KeyError) as exc:
            save(run.root/'recovery-verification.json',dict(status='FAIL',error=str(exc)))
    for role in ('draft','buildchecker','echecker','mdfixer'):
        run.cmd(role+'-service-logs',compose+['logs','--no-color',role])
    run.cmd('compose-ps-after',compose+['ps','--format','json'])
    run.cmd('residual-containers',['docker','ps','--no-trunc'])
    run.cmd('runtime-scan',['python3','labs/e13e14/scan_runtime_logs.py',str(run.root)])
    save(run.root/'scope.json',dict(status='PREFLIGHT_ONLY', peer_project='PENDING', E13_GATE='PENDING', RC='NOT_PUBLISHED'))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('suite',choices=['e13','e14'])
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--project',type=Path,default=ROOT/'data/e13-a11-project-20261117-v2')
    args=p.parse_args()
    run=Run(args.out.resolve())
    (e13 if args.suite=='e13' else e14)(run,args.project.resolve())
