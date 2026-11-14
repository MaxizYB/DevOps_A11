"""Check recorded cloud runs and emit a compact, provenance-aware delivery summary."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess

ROOT=Path(__file__).resolve().parents[2]


def read(path):
    return json.loads(path.read_text())


def summarize(out):
    expected={
        'e11-a':['full-check','incremental-check'],
        'reference-e11-b-mirror':['draft','fixed-md','repair','recheck'],
        'reference-e12-mirror':['draft','full-check','incremental-check','repair','recheck'],
    }
    result={'scope':'A11 leader cloud replay of course-generated fixtures; not B11 attestation',
            'source_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'kernel':platform.release(),'runs':{},'peer_confirmation':'PENDING',
            'real_project_acceptance':'PENDING','resources':{
                'visible_memory_gib':round(int(Path('/proc/meminfo').read_text().split('MemTotal:')[1].split()[0])/1024/1024,2),
                'exception':'Below the 4 GiB course minimum; previously accepted by group leader; serial replay'},
            'image_id':(out/'image-id.txt').read_text().strip()}
    for name,stages in expected.items():
        folder=out/name
        run=read(folder/'result.json')
        assert run['status']=='SUCCEEDED',name
        assert [s['name'] for s in run['stages']]==stages,name
        for item in run['artifacts']:
            relative=item['artifact_id']
            path=(folder/relative).resolve()
            assert path.is_relative_to(folder.resolve()) and path.is_file(),relative
            assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'],relative
        for stage in run['stages']:
            envelope=read(folder/stage['artifact']['artifact_id'])
            assert envelope['job_id']==run['job_id'] and envelope['trace_id']==run['trace_id']
            assert envelope['commit']==(run['base_commit'] if stage['name']=='full-check' else run['target_commit'])
        if 'repair' in stages:
            recheck=read(folder/'recheck.json')['data']
            assert recheck['validation']['accepted'] and not any(f['type']=='MISSING' for f in recheck['findings'])
            assert read(folder/'draft-build/result.json')['verification']['output_matches']
        if 'incremental-check' in stages and 'repair' in stages:
            consumed=read(folder/'repair.json')['data']['input_report']
            assert consumed['artifact_id']=='incremental-check.json'
            assert consumed['sha256']==hashlib.sha256((folder/'incremental-check.json').read_bytes()).hexdigest()
        result['runs'][name]={k:run[k] for k in ['status','schema_version','job_id','trace_id',
            'configuration_id','base_commit','target_commit']}
        result['runs'][name].update(stages=stages,artifacts_verified=len(run['artifacts']))
    client=read(out/'api-client/verification.json')
    assert client['status']=='SUCCEEDED' and all(c['passed'] for c in client['checks'])
    result['api']={k:v for k,v in client.items() if k!='checks'}
    result['api']['checks_passed']=len(client['checks'])
    verifier=read(out/'e11-a/verifier.json')
    assert verifier['status']=='SUCCEEDED' and all(check['passed'] for check in verifier['checks'])
    result['independent_e11a_verifier']={k:v for k,v in verifier.items() if k!='checks'}
    result['independent_e11a_verifier']['checks_passed']=len(verifier['checks'])
    result['status']='LOCAL_REFERENCE_ACCEPTED_PEER_AND_REAL_PROJECT_PENDING'
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True,help='Cloud evidence directory to inspect')
    args=parser.parse_args()
    value=summarize(args.out.resolve())
    (args.out/'run-summary.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(value,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
