"""Verify all handoff files before reading project/report inputs."""
import argparse
import hashlib
import json
from pathlib import Path

def verify(root):
    root = root.resolve()
    manifest = json.loads((root/'SHA256SUMS.json').read_text())
    if not isinstance(manifest, dict) or not manifest:
        raise ValueError('Empty or invalid file manifest')
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and p.name!='SHA256SUMS.json'}
    if actual != set(manifest):
        raise ValueError('Package has missing or unexpected files')
    for name, expected in manifest.items():
        path = root/name
        if path.is_symlink() or not path.resolve().is_relative_to(root) or not path.is_file():
            raise ValueError('Unsafe/missing package file: '+name)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            raise ValueError('Package file hash mismatch: '+name)
    return dict(status='PASS', files=len(manifest))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('root',nargs='?',type=Path,default=Path(__file__).resolve().parent)
    a=p.parse_args()
    print(json.dumps(verify(a.root)))
