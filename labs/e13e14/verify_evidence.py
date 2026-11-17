"""Independently recompute E11/E12/E14 artifact hashes and stage identities."""
import argparse
import hashlib
import json
from pathlib import Path

STAGES = ['draft', 'full-check', 'incremental-check', 'repair', 'recheck']

def verify(root):
    root = root.resolve()
    result = json.loads((root/'result.json').read_text())
    expected = STAGES if any(x['name']=='draft' for x in result['stages']) else ['full-check', 'incremental-check']
    if result['status'] != 'SUCCEEDED' or [x['name'] for x in result['stages']] != expected:
        raise ValueError('Task/stage status not a complete successful run')
    count = 0
    def path_for(item):
        uri = item['uri']
        prefix = 'artifact://' + result['job_id'] + '/'
        if uri.startswith('artifact://'):
            if not uri.startswith(prefix):
                raise ValueError('Artifact from another task')
            uri = uri[len(prefix):]
        path = (root/uri).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError('Artifact missing or outside run')
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Artifact hash mismatch: '+uri)
        if 'bytes' in item and path.stat().st_size != item['bytes']:
            raise ValueError('Artifact size mismatch')
        return path
    for item in result['artifacts']:
        path_for(item)
        count += 1
    for stage in result['stages']:
        envelope = json.loads(path_for(stage['artifact']).read_text())
        if (envelope['job_id'], envelope['trace_id'], envelope['status']) != (result['job_id'], result['trace_id'], 'SUCCEEDED'):
            raise ValueError('Stage identity mismatch')
        expected_commit = result['base_commit'] if stage['name']=='full-check' else result['target_commit']
        if envelope['commit'] != expected_commit:
            raise ValueError('Stage commit mismatch')
    if expected == STAGES:
        repair = json.loads((root/'repair.json').read_text())['data']
        recheck = json.loads((root/'recheck.json').read_text())['data']
        if result['schema_version']=='e14-compose-1':
            response = json.loads((root/'repair-response.json').read_text())
            increment = json.loads((root/'incremental-response.json').read_text())
            report = root/'incremental/incremental-check.json'
            if increment['sha256'] != hashlib.sha256(report.read_bytes()).hexdigest():
                raise ValueError('Repair transfer SHA mismatch')
            if response['validation']['accepted'] is not True or recheck['remaining_missing'] != 0:
                raise ValueError('Repair/recheck not accepted')
        else:
            if repair['input_report']['sha256'] != hashlib.sha256((root/'incremental-check.json').read_bytes()).hexdigest():
                raise ValueError('Repair did not consume the current report')
            if recheck['validation']['accepted'] is not True or any(x['type']=='MISSING' for x in recheck['findings']):
                raise ValueError('Missing dependencies remain')
    return dict(status='PASS', job_id=result['job_id'], trace_id=result['trace_id'], artifacts=count,
                target=result['target_commit'], scope='One actual run, not peer signoff or RC gate')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path)
    a=p.parse_args()
    print(json.dumps(verify(a.run),indent=2))
