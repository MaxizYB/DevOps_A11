"""Identify the actual component bytes, including an uncommitted deployment."""
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
B11_SOURCE = '7b45b9c04686f3aefe861bb1d8a17aa63c969f23'
IMPLEMENTATION_FILES = (
    'labs/e11e12/pipeline.py', 'labs/e11e12/server.py',
    'labs/e11e12/deployment.py', 'labs/e11e12/cjson_profile.py',
    'labs/e11e12/vendor/draft/autobuild.py', 'labs/e8e10/lab.py',
    'labs/e11e12/environment/services/buildchecker/buildchecker/fullcheck.py',
    'contracts/schemas/e12-orchestration-request.schema.json',
)


def metadata():
    digest = hashlib.sha256()
    for name in IMPLEMENTATION_FILES:
        digest.update(name.encode() + b'\0' + (ROOT/name).read_bytes() + b'\0')
    try:
        commit = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        dirty = bool(subprocess.check_output(
            ['git', 'status', '--porcelain', '--untracked-files=normal', '--', *IMPLEMENTATION_FILES],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip())
    except (OSError, subprocess.CalledProcessError):
        commit, dirty = None, None
    return {'source_commit': commit, 'implementation_sha256': digest.hexdigest(),
            'implementation_differs_from_commit': dirty,
            'b11_source_commit': B11_SOURCE,
            'scope': 'Integrated A11/B11 implementation bytes; not an upstream cJSON commit'}
