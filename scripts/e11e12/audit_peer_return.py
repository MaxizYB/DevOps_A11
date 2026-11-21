"""Re-verify a B11 return against the agreed handoff and server-side job files.

No archive code is executed. Original receipt/report bytes are preserved.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile

from api_client import artifact_name, verify_pipeline, save


def safe_members(archive):
    names = set()
    total = 0
    for item in archive.infolist():
        name = item.filename
        parts = name.rstrip('/').split('/')
        if (not name or PurePosixPath(name).is_absolute() or chr(92) in name
                or any(part in ('', '.', '..', '.git') for part in parts)
                or any(':' in part for part in parts) or name in names
                or stat.S_ISLNK(item.external_attr >> 16)):
            raise ValueError('Unsafe/duplicate archive member: '+name)
        names.add(name)
        total += item.file_size
        if total > 200 * 1024 * 1024 or item.file_size > 50 * 1024 * 1024:
            raise ValueError('Archive exceeds evidence size limit')
    return names


def extract(archive, destination):
    safe_members(archive)
    for item in archive.infolist():
        if item.is_dir():
            continue
        path = destination/item.filename
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(archive.read(item))


def audit(return_path, handoff_path, server_root, output):
    output.mkdir(parents=True, exist_ok=False)
    checks = []

    def require(condition, label):
        checks.append({'check': label, 'passed': bool(condition)})
        if not condition:
            raise ValueError(label)

    with zipfile.ZipFile(handoff_path) as handoff:
        safe_members(handoff)
        hashes = json.loads(handoff.read('SHA256SUMS.json'))
        require(set(hashes) == set(handoff.namelist())-{'SHA256SUMS.json'},
                'local agreed handoff has a complete manifest')
        for name, digest in hashes.items():
            require(hashlib.sha256(handoff.read(name)).hexdigest() == digest,
                    'local handoff SHA256: '+name)
        request_raw = handoff.read('cjson-request.json')
        expected_request = json.loads(request_raw)
        expected_deployment = json.loads(handoff.read('deployment.json'))
        expected_client_sha = hashlib.sha256(handoff.read('api_client.py')).hexdigest()
    with zipfile.ZipFile(return_path) as returned:
        names = safe_members(returned)
        clients = [name for name in names if name.endswith('.zip')]
        require(len(clients) == 1, 'one original peer client ZIP')
        require({'B11回执-cJSON正式联调.md', 'report.md', 'ADR.md', '数据与联调记录.csv'} <= names,
                'peer receipt, report, ADR and data record are attached')
        original_client = returned.read(clients[0])
        client_sha = hashlib.sha256(original_client).hexdigest()
        receipt = returned.read('B11回执-cJSON正式联调.md').decode('utf-8')
        require(client_sha in receipt, 'receipt identifies the exact original client ZIP')
        extract(returned, output/'original-return')
    with zipfile.ZipFile(io.BytesIO(original_client)) as client:
        names = safe_members(client)
        roots = {name.split('/')[0] for name in names}
        require(len(roots) == 1, 'peer client ZIP has one run directory')
        extract(client, output/'peer-client')
        client_root = output/'peer-client'/next(iter(roots))
    read = lambda name: json.loads((client_root/name).read_text(encoding='utf-8'))
    body, verification, operator = read('request.json'), read('verification.json'), read('operator-record.json')
    require(body['input'] == expected_request, 'peer used the exact agreed project request')
    require(operator['request_file_sha256'] == hashlib.sha256(request_raw).hexdigest(),
            'peer records the agreed request file bytes')
    require(operator['api_client_sha256'] == expected_client_sha, 'peer records the agreed client bytes')
    require(verification['status'] == 'SUCCEEDED' and bool(verification['checks'])
            and all(item['passed'] is True for item in verification['checks']),
            'all original client checks passed')
    job, trace = verification['job_id'], verification['trace_id']
    for value in (job, trace, expected_deployment['implementation_sha256']):
        require(value in receipt, 'receipt binds agreed job/trace/deployment: '+value)
    require(bool(operator.get('operator_self_declared')) and operator['status'] == 'SUCCEEDED'
            and operator['job_id'] == job and operator['trace_id'] == trace,
            'operator record matches the successful task')
    require(operator['agreed_deployment'] == expected_deployment
            and operator['actual_server_deployment'] == expected_deployment
            and verification['deployment'] == expected_deployment,
            'peer and agreed deployment metadata match exactly')
    require(read('health.json')['response']['deployment'] == expected_deployment,
            'peer health response identifies the agreed deployment')
    submitted, replay = read('submit.json'), read('same-key.json')
    require(submitted['http_status'] == replay['http_status'] == 202
            and submitted['response']['job_id'] == replay['response']['job_id'] == job,
            'same-key replay reused the peer task')
    conflict, changed = read('conflict.json'), read('conflict-request.json')
    require(changed['idempotency_key'] == body['idempotency_key']
            and changed['input']['target'] != body['input']['target']
            and {k:v for k,v in changed['input'].items() if k != 'target'}
                == {k:v for k,v in body['input'].items() if k != 'target'}
            and conflict['http_status'] == 409
            and conflict['response']['code'] == 'IDEMPOTENCY_CONFLICT',
            'same key with a different target returned 409')
    manifest_response = read('manifest.json')
    require(manifest_response['http_status'] == 200, 'peer fetched task artifacts successfully')
    manifest = manifest_response['response']
    state = json.loads((server_root/'state.json').read_text())
    server_manifest = json.loads((server_root/'evidence/result.json').read_text())
    canonical_hash = hashlib.sha256(json.dumps(body['input'], sort_keys=True).encode()).hexdigest()
    require(state['status'] == 'SUCCEEDED' and state['job_id'] == job and state['trace_id'] == trace
            and state['idempotency_key'] == body['idempotency_key']
            and state['request_hash'] == canonical_hash,
            'server state independently binds peer key, request, job and trace')
    require(manifest == server_manifest and manifest['deployment'] == expected_deployment,
            'peer manifest equals the independently collected server manifest')
    require(manifest['job_id'] == job and manifest['trace_id'] == trace
            and manifest['status'] == 'SUCCEEDED', 'successful result identity')
    seen = set()
    for descriptor in manifest['artifacts']:
        name = artifact_name(descriptor, job)
        require(name not in seen, 'unique artifact URI: '+name)
        seen.add(name)
        raw = (client_root/'downloads'/name).read_bytes()
        server_raw = (server_root/'evidence'/name).read_bytes()
        require(len(raw) == descriptor['bytes']
                and hashlib.sha256(raw).hexdigest() == descriptor['sha256']
                and raw == server_raw, 'peer/server bytes and manifest SHA256: '+name)
    downloaded = read('downloaded.json')
    require(len(seen) == verification['artifact_count'] == len(downloaded)
            and {item['uri']: (item['sha256'],item['bytes']) for item in downloaded}
            == {item['uri']: (item['sha256'],item['bytes']) for item in manifest['artifacts']},
            'all artifacts are present in the original downloaded record')
    verify_pipeline(expected_request, manifest, client_root, require)
    final = read('downloads/recheck.json')['data']
    result = {
        'status': 'SUCCEEDED', 'scope': 'Independent audit of B11 client and server evidence',
        'operator_self_declared': operator['operator_self_declared'],
        'started_at_utc': operator['started_at_utc'], 'finished_at_utc': operator['finished_at_utc'],
        'job_id': job, 'trace_id': trace, 'configuration_id': manifest['configuration_id'],
        'base_commit': manifest['base_commit'], 'target_commit': manifest['target_commit'],
        'deployment': expected_deployment, 'artifacts_verified': len(seen),
        'original_client_checks_passed': len(verification['checks']),
        'audit_checks_passed': len(checks), 'validation': final['validation'],
        'final_findings': final['findings'],
        'return_zip_sha256': hashlib.sha256(return_path.read_bytes()).hexdigest(),
        'original_client_zip_sha256': client_sha,
        'patch_sha256': hashlib.sha256((client_root/'downloads/candidate.patch').read_bytes()).hexdigest(),
        'repair_input_sha256': read('downloads/repair.json')['data']['input_report']['sha256'],
        'peer_confirmation': 'VERIFIED_B11_INDEPENDENT_CJSON_API_RUN',
        'selection_exception': 'Third-party upstream history, not a previously group-maintained project',
        'handoff_transport_note': 'B11 reports a missing explanatory Markdown in its received copy; original receipt preserved. Local agreed ZIP has the file and all executable/input hashes match.',
        'checks': checks,
    }
    save(output/'audit.json', result)
    return {key:value for key,value in result.items() if key != 'checks'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--return-zip', type=Path, required=True)
    parser.add_argument('--handoff-zip', type=Path, required=True)
    parser.add_argument('--server', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.return_zip, args.handoff_zip, args.server, args.out), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
