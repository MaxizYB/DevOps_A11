"""Prepare B11's unchanged upstream cJSON history and experiment-owned inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = '359567fdde253f311545a6c80b0fa6fb62e8ff09'
TARGET = 'cf0d87a095becada87336ed786f11070e9a037b5'
REFERENCE_FIX = '20cffa37a8f2d5d4811bb1dbba693c35c0d7f4a6'
BUNDLE_SHA256 = 'b83f63991d7020fd900fc7f675b9f476280d5ad96140bab64b273ce4cdcdea73'


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


def write_once(path, raw):
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError('Refusing to overwrite different input: ' + str(path))
        return
    path.write_bytes(raw)


def prepare(bundle, data, name='cjson', python_image=None, debian_mirror=None):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}',name):
        raise ValueError('dataset name must be a simple lowercase name')
    if python_image and not re.fullmatch(r'[^\s]+@sha256:[0-9a-f]{64}',python_image):
        raise ValueError('python_image must be digest-pinned')
    if debian_mirror and not re.fullmatch(r'https://[A-Za-z0-9.-]+(?::[0-9]+)?',debian_mirror):
        raise ValueError('debian_mirror must be a plain HTTPS origin')
    bundle, data = bundle.resolve(), data.resolve()
    if hashlib.sha256(bundle.read_bytes()).hexdigest() != BUNDLE_SHA256:
        raise ValueError('B11 cjson.bundle SHA256 mismatch')
    data.mkdir(parents=True, exist_ok=True)
    repo = data/'real-project'
    if not repo.exists():
        subprocess.run(['git', 'clone', str(bundle), str(repo)], check=True)
    if git(repo, 'rev-parse', 'HEAD') != TARGET or git(repo, 'status', '--porcelain'):
        raise ValueError('Existing real-project must be clean and at the agreed target; not overwritten')
    commits = {}
    for name, sha in [('base', BASE), ('target', TARGET)]:
        if git(repo, 'rev-parse', sha+'^{commit}') != sha:
            raise ValueError('Missing upstream commit: '+sha)
        commits[name] = {'sha': sha, 'description': git(repo, 'show', '-s', '--format=%s', sha)}
    commits['reference_fix'] = {'sha':REFERENCE_FIX, 'included_in_bundle':False,
                              'role':'Upstream answer reference only; not needed to execute the experiment'}
    examples = ROOT/'labs/e11e12/examples'
    broken=(examples/'cjson.Dockerfile.broken').read_text()
    candidate=(examples/'cjson.Dockerfile.candidate').read_text()
    if python_image:
        broken='FROM '+python_image.split('@',1)[0]+'\n'+broken.split('\n',1)[1]
        candidate='FROM '+python_image+'\n'+candidate.split('\n',1)[1]
    if debian_mirror:
        lines=candidate.splitlines()
        lines=[line for line in lines if not line.startswith('RUN sed ') and not line.startswith('RUN apt-get ')]
        index=lines.index('RUN make cJSON_Utils.o')
        lines.insert(index,"RUN sed -i -e 's|http://deb.debian.org/debian-security|"+debian_mirror+
                     "/debian-security|g' -e 's|http://deb.debian.org/debian|"+debian_mirror+
                     "/debian|g' /etc/apt/sources.list.d/debian.sources && "
                     "apt-get -o Acquire::ForceIPv4=true -o Acquire::Retries=3 update && "
                     "apt-get -o Acquire::ForceIPv4=true -o Acquire::Retries=3 install -y --no-install-recommends build-essential && "
                     "rm -rf /var/lib/apt/lists/*")
        candidate='\n'.join(lines)+'\n'
    broken_name=name+'.Dockerfile.broken'
    candidate_name=name+'.Dockerfile.candidate'
    write_once(data/broken_name,broken.encode())
    write_once(data/candidate_name,candidate.encode())
    request = {'mode':'e12', 'project_profile':'cjson', 'repo':'/course/data/real-project',
               'base':BASE, 'target':TARGET, 'broken_dockerfile':'/course/data/'+broken_name,
               'candidate':'/course/data/'+candidate_name, 'expected_output':'1', 'build_timeout':600}
    dataset = {
        'project':'DaveGamble/cJSON', 'upstream_repository':'https://github.com/DaveGamble/cJSON.git',
        'input_provenance':'third-party-upstream-history-replay',
        'maintenance_claim':False,
        'selection':'A11 leader selected an existing open-source history because the group has no maintained C/Make application',
        'course_requirement_note':'This is not evidence that A11/B11 originally maintained cJSON; disclose the selection exception',
        'commits':commits, 'bundle_sha256':BUNDLE_SHA256,
        'b11_source_commit':'7b45b9c04686f3aefe861bb1d8a17aa63c969f23',
        'fault':{'target':'cJSON_Utils.o','missing_dependency':'cJSON.h',
                 'upstream_history_preserved':True, 'reference_fix_is_input':False},
        'scope':'Only cJSON_Utils.o dependency analysis, plus upstream make test for functionality',
        'candidate_source':'B11 recorded candidate; A11 mirror overrides if specified; no runtime model/API generation',
        'mirror_overrides':{'python_image':python_image,'debian_mirror':debian_mirror},
        'commands':{'clean':'make clean','build':'make cJSON_Utils.o','test':'make test',
                    'image_verify':'./cJSON_test >/dev/null && echo 1'},
        'harness':{filename:hashlib.sha256((data/filename).read_bytes()).hexdigest()
                   for filename in [broken_name,candidate_name]},
    }
    for filename, obj in [(name+'-request.json',request), (name+'-dataset.json',dataset)]:
        write_once(data/filename, (json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
    return {'request':str(data/(name+'-request.json')), 'dataset':str(data/(name+'-dataset.json')),
            'target':TARGET, 'repo_clean':not bool(git(repo,'status','--porcelain'))}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--dataset-name',default='cjson')
    parser.add_argument('--python-image')
    parser.add_argument('--debian-mirror')
    args=parser.parse_args()
    print(json.dumps(prepare(args.bundle,ROOT/'data',args.dataset_name,args.python_image,args.debian_mirror),ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
