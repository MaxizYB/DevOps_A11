"""Verify complete final ZIP hashes and every included run artifact reference."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

from api_client import artifact_name


def verify(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or archive.testzip() is not None:
            raise ValueError('Duplicate names or corrupt ZIP')
        if any(PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts
               or '.git' in PurePosixPath(name).parts or chr(92) in name for name in names):
            raise ValueError('Unsafe archive path')
        manifest = json.loads(archive.read('SHA256SUMS.json'))
        if set(manifest) != set(names)-{'SHA256SUMS.json'}:
            raise ValueError('Incomplete package hash manifest')
        for name, digest in manifest.items():
            if hashlib.sha256(archive.read(name)).hexdigest() != digest:
                raise ValueError('Package file checksum mismatch: '+name)
        count, runs = 0, 0
        for name in names:
            if not name.startswith('evidence/') or not name.endswith('/result.json'):
                continue
            value = json.loads(archive.read(name))
            if not isinstance(value, dict) or value.get('schema_version') != 'e11e12-1':
                continue
            if not value.get('artifacts'):
                continue
            runs += 1
            parent = PurePosixPath(name).parent
            for item in value['artifacts']:
                relative = artifact_name(item, value['job_id'])
                raw = archive.read(str(parent/relative))
                if len(raw) != item['bytes'] or hashlib.sha256(raw).hexdigest() != item['sha256']:
                    raise ValueError('Included run manifest mismatch: '+str(parent/relative))
                count += 1
        state = json.loads(archive.read('DELIVERY_STATUS.json'))
        if state.get('submission_materials_complete') is not True:
            raise ValueError('Not marked as collected final materials')
        return {'file': str(path), 'status': 'VERIFIED', 'files_hashed': len(manifest),
                'run_manifests_verified': runs, 'artifact_references_verified': count,
                'source_sha': state['source_sha'], 'experiment': state['experiment'],
                'peer_confirmation': state['peer_confirmation'],
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('zip', type=Path, nargs='+')
    args = parser.parse_args()
    print(json.dumps([verify(path) for path in args.zip], ensure_ascii=False, indent=2))
