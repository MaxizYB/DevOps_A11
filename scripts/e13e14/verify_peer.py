"""Issue #45 independent cJSON oracle and E14 evidence association checks."""
import argparse
import hashlib
import json
import re
from pathlib import Path

BASE = 'cf0d87a095becada87336ed786f11070e9a037b5'
TARGET = 'f0c8fa4f812abe50964956cd0580ab963430ba35'
OBJECT = 'cJSON_Utils.o'
EXPECTED = [('MISSING', OBJECT, 'cJSON.h')]
ACTUAL = ['cJSON.h', 'cJSON_Utils.c', 'cJSON_Utils.h']
DECLARED = ['cJSON_Utils.c', 'cJSON_Utils.h']


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def findings(items):
    # Keep duplicates: a duplicate finding must fail the independent oracle.
    return sorted((f['type'], f['target'], f['dependency']) for f in items)


def checked(root, item, job, compose=False):
    uri = item['uri']
    prefix = 'artifact://' + job + '/'
    if not compose or uri.startswith('artifact://'):
        require(uri.startswith(prefix), 'Artifact belongs to another job')
        relative = uri[len(prefix):]
    else:
        relative = uri
    require(not Path(relative).is_absolute(), 'Absolute artifact path')
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()) and path.is_file(), 'Missing/escaping artifact')
    require(sha(path) == item['sha256'], 'Artifact SHA mismatch: ' + relative)
    if 'bytes' in item:
        require(path.stat().st_size == item['bytes'], 'Artifact size mismatch')
    return path


def manifest(root, stages, compose=False):
    root = Path(root).resolve()
    result = read(root / 'result.json')
    require(result['status'] == 'SUCCEEDED', 'Run failed')
    require((result['base_commit'], result['target_commit']) == (BASE, TARGET), 'Wrong project commit')
    require([s['name'] for s in result['stages']] == stages, 'Incomplete/unexpected stages')
    require(bool(result['artifacts']), 'Empty manifest')
    uris = [x['uri'] for x in result['artifacts']]
    require(len(uris) == len(set(uris)), 'Duplicate manifest URI')
    for item in result['artifacts']:
        checked(root, item, result['job_id'], compose)
    for stage in result['stages']:
        require(stage['artifact']['uri'] in uris, 'Stage absent from manifest')
        descriptor = next(x for x in result['artifacts'] if x['uri'] == stage['artifact']['uri'])
        require(descriptor['sha256'] == stage['artifact']['sha256'], 'Stage/manifest SHA mismatch')
        if 'bytes' in stage['artifact']:
            require(descriptor['bytes'] == stage['artifact']['bytes'], 'Stage/manifest size mismatch')
        stage_path = checked(root, stage['artifact'], result['job_id'], compose)
        require(stage_path == root / (stage['name'] + '.json'), 'Unexpected stage report path')
        envelope = read(stage_path)
        require((envelope['job_id'], envelope['trace_id'], envelope['status']) ==
                (result['job_id'], result['trace_id'], 'SUCCEEDED'), 'Stage identity mismatch')
        commit = BASE if stage['name'] == 'full-check' else TARGET
        require(envelope['commit'] == commit, 'Stage commit mismatch')
        if not compose:
            require(envelope['configuration_id'] == result['configuration_id'], 'Configuration mismatch')
            for item in envelope['artifacts']:
                checked(root, item, result['job_id'])
    return result


def oracle(data):
    require(data['commit'] == TARGET, 'Incremental data target mismatch')
    require(data['actual'] == {OBJECT: ACTUAL}, 'Actual graph differs from source oracle')
    require(data['declared'] == {OBJECT: DECLARED}, 'Declared graph differs from Make oracle')
    require(findings(data['findings']) == EXPECTED, 'Missing/extra/duplicate findings')
    require(data['reused'] == [OBJECT] and data['refreshed'] == [], 'Unexpected reuse/refresh')
    require(data['cache_source_commit'] == BASE, 'Wrong cache source commit')


def full_oracle(root, folder):
    directory = Path(root) / folder
    report = read(directory / 'findings.json')
    require(report['status'] == 'SUCCEEDED' and report['build_exit_code'] == 0, 'Full build failed')
    require(findings(report['findings']) == EXPECTED, 'Full findings differ from oracle')
    actual = read(directory / 'actual-graph.json')
    declared = read(directory / 'declared-graph.json')
    require(sorted(e['dependency'] for e in actual if e['target'] == OBJECT) == ACTUAL, 'Full actual graph')
    require(sorted(e['dependency'] for e in declared if e['target'] == OBJECT) == DECLARED, 'Full declared graph')
    edge = next(e for e in actual if e['target'] == OBJECT and e['dependency'] == 'cJSON.h')
    evidence = edge['evidence']
    trace = directory / 'trace' / evidence['trace_file']
    line = trace.read_text().splitlines()[evidence['line'] - 1]
    require('cJSON.h' in line and re.search(r'open(?:at)?\(.*O_RDONLY.*\)\s*=\s*\d+', line), 'No successful MD trace read')
    database = (directory / 'make-db.txt').read_text().splitlines()
    entry = next(e for e in declared if e['target'] == OBJECT)['evidence']
    require(database[entry['line'] - 1] == entry['declaration'], 'Make declaration line mismatch')
    return {'trace_file': str(trace), 'line': evidence['line'], 'text': line,
            'make_database_line': entry['line'], 'declaration': entry['declaration']}


def verify_a(root):
    root = Path(root).resolve()
    result = manifest(root, ['full-check', 'incremental-check'])
    require(result['schema_version'] == 'e11e12-1', 'A schema mismatch')
    current = read(root / 'incremental-check.json')['data']
    oracle(current)
    require(current == read(root / 'incremental-report.json'), 'Envelope/report mismatch')
    require(current['baseline_commit'] == BASE, 'Wrong baseline')
    require(current['baseline_cache_sha256'] == sha(root / 'baseline-cache.json'), 'Cache SHA mismatch')
    cache = read(root / 'baseline-cache.json')
    require(cache['commit'] == BASE and cache['key'] == current['key'], 'Cache identity/key mismatch')
    trace = {name: full_oracle(root, name) for name in ('baseline-full', 'target-full')}
    return dict(status='PASS', job_id=result['job_id'], trace_id=result['trace_id'],
                configuration_id=result['configuration_id'], artifacts=len(result['artifacts']),
                findings=current['findings'], reused=current['reused'], refreshed=current['refreshed'], trace=trace)


def verify_e14(root, operator='241880439'):
    root = Path(root).resolve()
    result = manifest(root, ['draft', 'full-check', 'incremental-check', 'repair', 'recheck'], True)
    require(result['schema_version'] == 'e14-compose-1' and result['project_profile'] == 'cjson', 'E14 profile/schema')
    request = read(root / 'request.json')
    require((request['base'], request['target'], request['project_profile']) == (BASE, TARGET, 'cjson'), 'Request identity')
    increment = read(root / 'incremental/incremental-check.json')
    require((increment['schema_version'], increment['kind'], increment['status']) ==
            ('e11e12-1', 'incremental-check', 'SUCCEEDED'), 'Incremental envelope mismatch')
    require((increment['commit'], increment['data']['commit'], increment['job_id'], increment['trace_id']) ==
            (TARGET, TARGET, result['job_id'], result['trace_id']), 'Incremental identity')
    oracle(increment['data'])
    cache = read(root / 'incremental/baseline-cache.json')
    require(cache['commit'] == BASE and cache['actual'] == {OBJECT: ACTUAL}, 'Baseline cache identity')
    for name in ('baseline-full', 'target-full'):
        full_oracle(root, name)
    response = read(root / 'incremental-response.json')
    stage = read(root / 'incremental-check.json')['data']
    require(stage == response, 'Incremental response/stage mismatch')
    require(response['status'] == 'SUCCEEDED', 'Incremental response failed')
    require(response['sha256'] == sha(root / 'incremental/incremental-check.json'), 'Repair input report SHA')
    require(response['report'].endswith('/' + root.name + '/incremental/incremental-check.json'), 'Repair input path')
    repair = read(root / 'repair-response.json')
    require(repair == read(root / 'repair.json')['data'], 'Repair response/stage mismatch')
    require(repair['status'] == 'SUCCEEDED', 'Repair response failed')
    require(repair['sha256'] == sha(root / 'repair-work/candidate.patch'), 'Patch SHA')
    checks = repair['validation']['checks']
    require(repair['validation']['accepted'] is True and all(checks[k] is True for k in
            ('patch_applies', 'build', 'test', 'header_change', 'no_missing')), 'Patch rejected')
    require(repair['validation'] == read(root / 'repair-work/validation/validation.json'), 'Validation mismatch')
    plan = read(root / 'repair-work/repair-plan.json')
    require([(e['target'], e['dependency']) for e in plan] == [(OBJECT, 'cJSON.h')], 'Wrong repair plan')
    final = read(root / 'final-full/findings.json')
    require(final['status'] == 'SUCCEEDED' and final['build_exit_code'] == 0, 'Final build failed')
    require(final['findings'] == [], 'Expected no final MD/RD for cJSON target')
    recheck = read(root / 'recheck.json')['data']
    require(recheck['remaining_missing'] == 0 and recheck['result']['result'] == final, 'Recheck result mismatch')
    drafted = read(root / 'draft-response.json')
    require(drafted == read(root / 'draft.json')['data'], 'DRAFT response/stage mismatch')
    require(drafted['status'] == drafted['result']['status'] == 'SUCCEEDED', 'DRAFT inner failure')
    require(drafted['result'] == read(root / 'draft-build/result.json'), 'DRAFT result mismatch')
    binding = root / 'repair-response.request.json'
    binding_limit = 'Compose stores responses, not the MDFixer HTTP request. Public orchestrator passes this report URI/SHA; request bytes are not independently persisted.'
    if binding.exists():
        record = read(binding)
        require(record['role'] == 'mdfixer', 'Wrong consuming role')
        payload = record['payload']
        require((payload['report'], payload['report_sha256'], payload['target_commit'], payload['job_id'], payload['trace_id']) ==
                (response['report'], response['sha256'], TARGET, result['job_id'], result['trace_id']), 'MDFixer request binding mismatch')
        run_prefix = response['report'].removesuffix('/incremental/incremental-check.json')
        require((payload['project'], payload['out']) == (run_prefix + '/target-project', run_prefix + '/repair-work'), 'Repair processing directory mismatch')
        binding_limit = None
    return dict(status='PASS', source_run=str(root), run_operator=operator,
                check_operator='231880027', job_id=result['job_id'], trace_id=result['trace_id'],
                artifacts=len(result['artifacts']), report_sha256=response['sha256'],
                patch_sha256=repair['sha256'], final_findings=final['findings'],
                scope='Independent evidence association check; final merged RC still requires rerun',
                repair_request_recorded=binding.exists(), repair_binding_limit=binding_limit)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['a', 'e14'])
    parser.add_argument('run', type=Path)
    args = parser.parse_args()
    print(json.dumps((verify_a if args.mode == 'a' else verify_e14)(args.run), indent=2))
