"""Package reviewed source and collected evidence, keeping outstanding gates visible."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import zipfile

from api_client import artifact_name

ROOT = Path(__file__).resolve().parents[2]


def allowed(name):
    parts = Path(name).parts
    return not any(part in {'.git', '__pycache__', '.pytest_cache', 'devops-auth'} for part in parts) and not (
        Path(name).name.startswith('.env') and Path(name).name != '.env.example'
        or Path(name).suffix in {'.pem', '.key', '.pyc', '.o'}
        or Path(name).name in {'app', 'source.bundle'})


def package(evidence, output, source_sha, status):
    entries = {}
    # Old B11 manifests also reference compiled outputs. Keep those exact
    # evidence bytes rather than silently creating a broken artifact manifest.
    required_binaries = set()
    for result_path in evidence.rglob('result.json'):
        value = json.loads(result_path.read_text(encoding='utf-8'))
        if not isinstance(value, dict) or value.get('schema_version') != 'e11e12-1':
            continue
        for item in value.get('artifacts', []):
            name = artifact_name(item, value['job_id'])
            path = result_path.parent/name
            if not path.resolve().is_relative_to(evidence.resolve()) or path.is_symlink():
                raise ValueError('Evidence artifact escaped its source directory: '+name)
            raw = path.read_bytes()
            if len(raw) != item['bytes'] or hashlib.sha256(raw).hexdigest() != item['sha256']:
                raise ValueError('Evidence manifest mismatch: '+str(path))
            if path.suffix == '.o' or path.name == 'app':
                required_binaries.add(path.resolve())
    archive = subprocess.check_output(['git','archive','--format=tar',source_sha],cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(archive)) as snapshot:
        for member in snapshot.getmembers():
            if member.isfile() and allowed(member.name):
                entries['source/'+member.name] = snapshot.extractfile(member).read()
    for path in sorted(evidence.rglob('*')):
        name = path.relative_to(evidence).as_posix()
        if path.is_file() and not path.is_symlink() and (allowed(name) or path.resolve() in required_binaries):
            entries['evidence/'+name] = path.read_bytes()
    entries['DELIVERY_STATUS.json'] = (json.dumps(dict(status,source_sha=source_sha),ensure_ascii=False,indent=2)+'\n').encode()
    peer_verified = str(status.get('peer_confirmation', '')).startswith('VERIFIED_')
    experiment = status.get('experiment', 'E11/E12')
    entries['README-先读.md'] = (
        '# A11 '+experiment+' 交付材料\n\n'
        '源码在 source/，运行与 GitHub 证据在 evidence/，每个文件的哈希在 SHA256SUMS.json。\n\n'
        '先阅读 DELIVERY_STATUS.json 和 source/docs/e11-e12/最终交付检查.md。\n'
        + ('B11 独立 cJSON API 访问及服务器原始记录已交叉核验，详见 evidence/ 中的 peer-audit 与报告。\n'
           if peer_verified else 'E12 的组长同机回放不构成 B11 分机访问确认。\n')
        + '课程生成样例与第三方上游历史复现分开归档；选题、资源及 GitHub 状态以实际记录为准。\n'
        + ('本包为材料收齐后的提交整理版，保留明确披露的偏差，不代表教师已认可选题例外或 GitHub 已合并。\n'
           if status.get('submission_materials_complete') is True
           else '未完成项需要补齐后重新打包；不能把本包标成 E12 全部通过。\n')
    ).encode()
    if (evidence/'SUBMISSION_INDEX.md').is_file():
        entries['交付目录与复现.md'] = (evidence/'SUBMISSION_INDEX.md').read_bytes()
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
