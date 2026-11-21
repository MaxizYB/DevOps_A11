"""Consume a verified A11 handoff into a fresh directory of B11's own checkout."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from handoff_a_to_b import make_handoff
from verify_package import verify

PACKAGE = Path(__file__).resolve().parent

def prepare(root, folder):
    verify(PACKAGE)
    root=root.resolve()
    if not (root/'run_e11e12.py').is_file():
        raise ValueError('Use B11 existing E11/E12 checkout root')
    if not folder or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in folder):
        raise ValueError('Use one safe data directory name')
    out=root/'data'/folder
    if out.exists():
        raise ValueError('Refusing to overwrite an earlier project/request')
    dataset=json.loads((PACKAGE/'dataset.json').read_text())
    out.mkdir(parents=True)
    repo=out/'repo'
    subprocess.run(['git','clone','-b',dataset['project_branch'],str(PACKAGE/'a11-project.bundle'),str(repo)],check=True)
    subprocess.run(['git','-C',str(repo),'checkout','--detach',dataset['target']],check=True)
    for revision in (dataset['base'],dataset['target']):
        found=subprocess.check_output(['git','-C',str(repo),'rev-parse','--verify',revision+'^{commit}'],text=True).strip()
        if found!=revision:
            raise ValueError('Bundle commit does not match exchange manifest')
    subprocess.run(['git','-C',str(repo),'merge-base','--is-ancestor',dataset['base'],dataset['target']],check=True)
    subprocess.run(['python3','test_project.py'],cwd=repo,check=True)
    shutil.copy2(PACKAGE/'candidate.Dockerfile',out/'candidate.Dockerfile')
    # Source evidence stays in the package: preserve the exact received A bytes.
    handoff=make_handoff(PACKAGE/'A-result/result.json',dataset['target'])
    fixed=out/'fixed-md.json'
    fixed.write_text(json.dumps(handoff,ensure_ascii=False,indent=2)+'\n')
    common=dict(repo='/course/data/'+folder+'/repo',base=dataset['base'],target=dataset['target'],
                candidate='/course/data/'+folder+'/candidate.Dockerfile',expected_output=dataset['expected_output'],build_timeout=600)
    request=dict(mode='e11-b',**common,fixed_report='/course/data/'+folder+'/fixed-md.json',
                 fixed_report_sha256=hashlib.sha256(fixed.read_bytes()).hexdigest())
    for name,value in [('request-e11-b.json',request),('request-e12.json',dict(mode='e12',**common))]:
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    receipt=dict(status='PREPARED_NOT_EXECUTED',base=dataset['base'],target=dataset['target'],
                 source_report=handoff['source_report'],fixed_report_sha256=request['fixed_report_sha256'])
    (out/'received.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(output=str(out),**receipt),ensure_ascii=False,indent=2))
    print('Run in B11 checkout: python3 run_e11e12.py run --request data/'+folder+'/request-e11-b.json --out work/e13-from-a11-01')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo-root',type=Path,required=True)
    p.add_argument('--data-name',default='e13-from-a11')
    args=p.parse_args()
    prepare(args.repo_root,args.data_name)
