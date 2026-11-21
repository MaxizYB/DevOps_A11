"""Safely import the nested teacher projects without overwriting existing inputs."""
import argparse
import hashlib
import io
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def prepare(archive, data):
    if not data.resolve().is_relative_to((ROOT / 'data').resolve()):
        raise ValueError('Import into this repository data/')
    target = data / 'e13-upstream-student'
    if target.exists():
        raise ValueError('Project directory exists; preserve previous inputs')
    with zipfile.ZipFile(archive) as outer:
        matches = [i for i in outer.infolist() if i.filename.endswith('e13-upstream-student.zip')]
        if len(matches) != 1:
            raise ValueError('Expected one teacher project package')
        raw = outer.read(matches[0])
    with zipfile.ZipFile(io.BytesIO(raw)) as nested:
        if nested.testzip() is not None:
            raise ValueError('Invalid nested ZIP CRC')
        for item in nested.infolist():
            path = data / item.filename
            if not path.resolve().is_relative_to(target.resolve()) or item.external_attr >> 16 & 0o170000 == 0o120000:
                raise ValueError('Unsafe archive path')
        nested.extractall(data)
    entries = []
    for name in ('H1-jsmn', 'H2-inih', 'H3-tiny-aes'):
        folder = target / name
        target_sha, base_sha = subprocess.check_output(
            ['git', '-C', str(folder / 'repo'), 'rev-list', '--max-count=2', 'HEAD'], text=True).splitlines()
        prefix = '/course/' + folder.relative_to(ROOT).as_posix()
        request = dict(mode='e12', repo=prefix+'/repo', base=base_sha, target=target_sha,
                       candidate=prefix+'/candidate.Dockerfile', expected_output='1', build_timeout=600)
        (folder / 'request-e12.json').write_text(json.dumps(request, indent=2)+'\n')
        entries.append(dict(name=name, base=base_sha, target=target_sha,
                            upstream=(folder/'repo/UPSTREAM.md').read_text()))
    result = dict(archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                  nested_sha256=hashlib.sha256(raw).hexdigest(), projects=entries)
    (target / 'import-provenance.json').write_text(json.dumps(result, indent=2)+'\n')
    return result

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('archive', type=Path)
    args = p.parse_args()
    print(json.dumps(prepare(args.archive, ROOT/'data'), ensure_ascii=False, indent=2))
