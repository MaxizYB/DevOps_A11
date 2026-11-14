"""Package reviewed source and collected evidence, keeping outstanding gates visible."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def allowed(name):
    parts = Path(name).parts
    return not any(part in {'.git', '__pycache__', '.pytest_cache', 'devops-auth'} for part in parts) and not (
        Path(name).name.startswith('.env') and Path(name).name != '.env.example'
        or Path(name).suffix in {'.pem', '.key', '.pyc', '.o'}
        or Path(name).name in {'app', 'source.bundle'})


def package(evidence, output, source_sha, status):
    entries = {}
    archive = subprocess.check_output(['git','archive','--format=tar',source_sha],cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(archive)) as snapshot:
        for member in snapshot.getmembers():
            if member.isfile() and allowed(member.name):
                entries['source/'+member.name] = snapshot.extractfile(member).read()
    for path in sorted(evidence.rglob('*')):
        name = path.relative_to(evidence).as_posix()
        if path.is_file() and not path.is_symlink() and allowed(name):
            entries['evidence/'+name] = path.read_bytes()
    entries['DELIVERY_STATUS.json'] = (json.dumps(dict(status,source_sha=source_sha),ensure_ascii=False,indent=2)+'\n').encode()
    entries['README-先读.md'] = (
        '# A11 E11/E12 交付材料\n\n'
        '源码在 source/，运行与 GitHub 证据在 evidence/，每个文件的哈希在 SHA256SUMS.json。\n\n'
        '先阅读 DELIVERY_STATUS.json 和 source/docs/e11-e12/最终交付检查.md。\n'
        'E12 的组长同机回放不构成 B11 分机访问确认；真实项目与课程生成样例单独验收。\n'
        '未完成项需要补齐后重新打包；不能把本包标成 E12 全部通过。\n'
    ).encode()
    entries['SHA256SUMS.json']=(json.dumps({name:hashlib.sha256(data).hexdigest()
        for name,data in sorted(entries.items())},ensure_ascii=False,indent=2)+'\n').encode()
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as bundle:
        for name,data in sorted(entries.items()):
            bundle.writestr(name,data)
    with zipfile.ZipFile(output) as bundle:
        assert bundle.testzip() is None
        hashes=json.loads(bundle.read('SHA256SUMS.json'))
        assert all(hashlib.sha256(bundle.read(name)).hexdigest()==digest for name,digest in hashes.items())
    return {'file':str(output),'files':len(entries),'sha256':hashlib.sha256(output.read_bytes()).hexdigest()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence',type=Path,required=True)
    parser.add_argument('--status',type=Path,required=True)
    parser.add_argument('--source-sha',default='HEAD')
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    sha=subprocess.check_output(['git','rev-parse',args.source_sha],cwd=ROOT,text=True).strip()
    status=json.loads(args.status.read_text())
    if not args.evidence.is_dir():
        parser.error('--evidence must exist')
    print(json.dumps(package(args.evidence,args.out,sha,status),ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
