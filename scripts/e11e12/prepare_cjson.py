"""Prepare B11's unchanged upstream cJSON history and experiment-owned inputs."""
import argparse
import hashlib
import json
from pathlib import Path
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


def prepare(bundle, data):
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
    for name in ['cjson.Dockerfile.broken', 'cjson.Dockerfile.candidate']:
        write_once(data/name, (examples/name).read_bytes())
    request = {'mode':'e12', 'project_profile':'cjson', 'repo':'/course/data/real-project',
               'base':BASE, 'target':TARGET, 'broken_dockerfile':'/course/data/cjson.Dockerfile.broken',
               'candidate':'/course/data/cjson.Dockerfile.candidate', 'expected_output':'1', 'build_timeout':600}
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
        'commands':{'clean':'make clean','build':'make cJSON_Utils.o','test':'make test',
                    'image_verify':'./cJSON_test >/dev/null && echo 1'},
        'harness':{name:hashlib.sha256((data/name).read_bytes()).hexdigest() for name in
                   ['cjson.Dockerfile.broken','cjson.Dockerfile.candidate']},
    }
    for name, obj in [('cjson-request.json',request), ('cjson-dataset.json',dataset)]:
        write_once(data/name, (json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
    return {'request':str(data/'cjson-request.json'), 'dataset':str(data/'cjson-dataset.json'),
            'target':TARGET, 'repo_clean':not bool(git(repo,'status','--porcelain'))}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(prepare(args.bundle,ROOT/'data'),ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
