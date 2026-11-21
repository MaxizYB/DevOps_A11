"""Exercise secret scanner workspace/history/image coverage with a fake credential only."""
import argparse
import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def run(argv,cwd,expected):
    result=subprocess.run(argv,cwd=cwd,text=True,capture_output=True,timeout=600)
    return dict(exit_code=result.returncode,expected_exit=expected,passed=result.returncode==expected,
                stdout=result.stdout,stderr=result.stderr)

def execute(out,image):
    out=out.resolve()
    if not out.is_relative_to((ROOT/'work').resolve()) or out.exists():
        raise ValueError('Use one new dedicated directory under work/')
    out.mkdir(parents=True)
    repo=out/'isolated-repo'
    subprocess.run(['git','clone','--no-hardlinks',str(ROOT),str(repo)],check=True,timeout=300,
                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    fake='sk-'+('a'*24)
    checks={}
    checks['clean_source_history']=run(['python3','scripts/secret_scan.py','.','--history'],repo,0)
    probe=repo/'fake-probe.txt'
    probe.write_text('api_key = "'+fake+'"\n')
    checks['workspace_fake']=run(['python3','scripts/secret_scan.py','.'],repo,1)
    probe.unlink()
    subprocess.run(['git','-C',str(repo),'config','user.name','E13-Isolated-C6'],check=True)
    subprocess.run(['git','-C',str(repo),'config','user.email','c6@example.invalid'],check=True)
    # Re-create only inside this disposable clone so the secret becomes history data.
    probe.write_text('api_key = "'+fake+'"\n')
    subprocess.run(['git','-C',str(repo),'add','fake-probe.txt'],check=True,stdout=subprocess.DEVNULL)
    subprocess.run(['git','-C',str(repo),'commit','-m','isolated fake-key scanner probe'],check=True,
                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    probe.unlink()
    checks['history_fake']=run(['python3','scripts/secret_scan.py','.','--history'],repo,1)
    image_tag='e13-c6-fake-'+uuid.uuid4().hex[:12]
    dockerfile=out/'Dockerfile.image-probe'
    # scratch keeps the disposable credential only in one config-only image,
    # with no shared base layers; removing its image removes the test artifact.
    dockerfile.write_text('FROM scratch\nARG A11_C6_KEY\nENV API_KEY=$A11_C6_KEY\n')
    built=run(['docker','build','--quiet','-f',str(dockerfile),'-t',image_tag,
               '--build-arg','A11_C6_KEY='+fake,str(out)],ROOT,0)
    if not built['passed']:
        raise ValueError('Could not build isolated scanner test image')
    image_id=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',image_tag],text=True).strip()
    checks['image_fake']=run(['python3','scripts/secret_scan.py','.','--image',image_tag],ROOT,1)
    if checks['image_fake']['stdout'].find(fake) >= 0 or any(
            checks[name]['stdout'].find(fake)>=0 for name in ('workspace_fake','history_fake')):
        raise ValueError('Scanner output leaked the complete fake value')
    removed=run(['docker','image','rm',image_id],ROOT,0)
    if not removed['passed']:
        raise ValueError('Isolated test image cleanup failed')
    shutil.rmtree(repo)
    checks['clean_after_disposal']=run(['python3','scripts/secret_scan.py','.','--history'],ROOT,0)
    for name,item in checks.items():
        if not item['passed']:
            raise ValueError('Secret scanner scope check failed: '+name)
    result=dict(status='PASS',scope='A11 isolated scanner probe; fake value never entered shared Git, reports contain only redacted output',
                checks={k:{'exit_code':v['exit_code'],'expected_exit':v['expected_exit'],'stdout':v['stdout'],
                           'stderr':v['stderr']} for k,v in checks.items()},
                image_id=image_id,image_removed=True,isolated_repo_removed=True)
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=ROOT/'work/e13-c6-security-20261117')
    parser.add_argument('--image',default='course-e11e12:241880439')
    args=parser.parse_args()
    print(json.dumps(execute(args.out,args.image),ensure_ascii=False,indent=2))
