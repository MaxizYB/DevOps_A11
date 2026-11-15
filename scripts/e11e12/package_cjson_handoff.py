"""Build a small, credential-free B11 client package from deployed inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]

RECEIPT = """# B11 → A11：cJSON 正式联调回执

- 实际操作者姓名/学号：
- 操作时间与时区：
- 本轮结果 ZIP 文件名及 SHA256：
- job_id / trace_id：
- verification.json 的 status：
- 实际服务 implementation_sha256：
- 实际服务 source_commit / B11 来源 source_commit：
- 本轮是否对约定 cJSON base/target 完成了独立 API 提交、查询与下载：
- 结果为失败时，完整错误及原始 ZIP 是否一并保留：
- E11-B 个人报告 / ADR / AI 使用记录：已有交接包中的具体路径；未包含则补发文件：
- 其他问题：

本轮是第三方 cJSON 上游历史缺陷的功能/接口复现，不是压力测试，
也不声明 A11/B11 原本维护 cJSON。请按实际操作填写，不改写自动生成的证据。
请仅回传结果 ZIP 与本回执，不要回传账号密码或旧私密交接包。
"""


def package(request_path, dataset_path, deployment_path, output):
    request = json.loads(request_path.read_text(encoding='utf-8'))
    dataset = json.loads(dataset_path.read_text(encoding='utf-8'))
    deployment = json.loads(deployment_path.read_text(encoding='utf-8'))
    if request.get('mode') != 'e12' or request.get('project_profile') != 'cjson':
        raise ValueError('Only the agreed cjson/e12 request can be packaged')
    if (dataset.get('maintenance_claim') is not False
            or dataset['commits']['base']['sha'] != request['base']
            or dataset['commits']['target']['sha'] != request['target']):
        raise ValueError('Dataset commits/provenance disagree with the request')
    if (not deployment.get('source_commit') or deployment.get('implementation_differs_from_commit') is not False
            or len(deployment.get('implementation_sha256', '')) != 64):
        raise ValueError('A clean, versioned deployed implementation is required')
    # Explicit allowlist: never recurse into the old credential-bearing ZIP.
    entries = {
        'api_client.py': (ROOT/'scripts/e11e12/api_client.py').read_bytes(),
        'run_peer_client.py': (ROOT/'scripts/e11e12/run_peer_client.py').read_bytes(),
        'README-联调操作.md': (ROOT/'docs/e11-e12/B11-cJSON正式联调.md').read_bytes(),
        '联调全景与提交材料.md': (ROOT/'docs/e11-e12/联调全景与提交材料.md').read_bytes(),
        'cjson-request.json': request_path.read_bytes(),
        'dataset.json': dataset_path.read_bytes(),
        'deployment.json': deployment_path.read_bytes(),
        'B11回执模板.md': RECEIPT.encode('utf-8'),
    }
    for key in ('broken_dockerfile', 'candidate'):
        name = Path(request[key]).name
        path = request_path.parent/name
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != dataset['harness'].get(name):
            raise ValueError('Dockerfile differs from agreed dataset: '+name)
        entries[name] = raw
    entries['SHA256SUMS.json'] = (json.dumps({name: hashlib.sha256(raw).hexdigest()
        for name, raw in sorted(entries.items())}, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(entries.items()):
            archive.writestr(name, raw)
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert all(hashlib.sha256(archive.read(name)).hexdigest() == digest
                   for name, digest in json.loads(archive.read('SHA256SUMS.json')).items())
    return {'file': str(output), 'files': len(entries),
            'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
            'implementation_sha256': deployment['implementation_sha256']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--deployment', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(package(args.request, args.dataset, args.deployment, args.out), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
