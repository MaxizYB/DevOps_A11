import argparse
import json
import re
from pathlib import Path
from pipeline import ROOT, save
from lab import fixture,commit,scan

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--dataset-name',default='integration-sample')
    parser.add_argument('--python-image',default='python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f')
    args=parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*',args.dataset_name):
        parser.error('dataset-name must be one safe directory name')
    if not re.fullmatch(r'[^\s]+@sha256:[0-9a-f]{64}',args.python_image):
        parser.error('python-image must be digest-pinned')
    root=ROOT/'data'/args.dataset_name
    if root.exists():raise SystemExit(str(root)+' already exists; preserve it and choose a new dataset name')
    project=root/'repo';fixture(project)
    tag=args.python_image.split('@',1)[0]
    broken='FROM '+tag+'\nWORKDIR /work\nCOPY main.c helper.c config.h extra.h unused.h Makefile ./\nRUN make app\nCMD ["./app"]\n'
    (project/'Dockerfile.broken').write_text(broken,encoding='utf-8')
    base=commit(project,'integration C0')
    (project/'main.c').write_text('#include "extra.h"\n'+(project/'main.c').read_text(),encoding='utf-8')
    target=commit(project,'integration C1 add project include')
    candidate=broken.replace('FROM '+tag,'FROM '+args.python_image).replace('RUN make app','RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*\nRUN make app')
    (root/'candidate.Dockerfile').write_text(candidate,encoding='utf-8')
    fixed=scan(project)
    save(root/'fixed-md.json',{'schema_version':'e11e12-1','kind':'fixed-md','status':'SUCCEEDED','commit':target,'data':fixed})
    common={'repo':str(project),'base':base,'target':target,'build_timeout':600}
    save(root/'e11-a.json',dict(mode='e11-a',**common))
    save(root/'e11-b.json',dict(mode='e11-b',**common,candidate=str(root/'candidate.Dockerfile'),fixed_report=str(root/'fixed-md.json'),expected_output='1'))
    save(root/'e12.json',dict(mode='e12',**common,candidate=str(root/'candidate.Dockerfile'),expected_output='1'))
    save(root/'dataset.json',{'source':'course-generated controlled C/Make project','base_commit':base,'target_commit':target,'python_image':args.python_image,'candidate_source':'recorded dependency-install pattern adapted to the two-source-file project','expected_output':'1','purpose':'classroom baseline; replace request paths with your own project for real-data integration'})
    print(root)

if __name__=='__main__':main()
