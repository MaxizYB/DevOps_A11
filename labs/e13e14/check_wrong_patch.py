"""C5 preflight with an applicable patch that fails the real build, not just syntax."""
import argparse
import difflib
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'labs/e8e10'))
from lab import validate

def execute(project,out):
    project=project.resolve();out=out.resolve()
    if not project.is_relative_to((ROOT/'data').resolve()) or not out.is_relative_to((ROOT/'work').resolve()) or out.exists():
        raise ValueError('Use existing data project and new work child directory')
    out.mkdir(parents=True)
    def snapshot():
        names=subprocess.check_output(['git','ls-files','-z'],cwd=project).split(b'\0')
        return dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=project,text=True).strip(),
                    files={n.decode():hashlib.sha256((project/n.decode()).read_bytes()).hexdigest() for n in names if n},
                    status=subprocess.check_output(['git','status','--porcelain'],cwd=project,text=True))
    before=snapshot()
    original=(project/'Makefile').read_text()
    changed=original.replace('gcc $(CFLAGS) -c main.c -o main.o','false # C5 injected build failure',1)
    if original==changed:raise ValueError('Unsupported fixture for controlled wrong patch')
    candidate=out/'applicable-wrong.patch'
    candidate.write_text(''.join(difflib.unified_diff(original.splitlines(True),changed.splitlines(True),fromfile='a/Makefile',tofile='b/Makefile')))
    verdict=validate(project,candidate,out/'validation')
    after=snapshot()
    result=dict(scope='A11 project local preflight, not B11 independent execution',before=before,after=after,
                source_unchanged=before==after,validation=verdict,
                passed=before==after and verdict['accepted'] is False and verdict['checks'].get('patch_applies') is True and verdict['rollback'] is True)
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    if not result['passed']:raise ValueError('C5 actual build failure/rollback not demonstrated')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(execute(args.project,args.out),ensure_ascii=False,indent=2))
