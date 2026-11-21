"""Assemble separately indexed A11 E11-A and E12 final submission materials."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import zipfile

from api_client import save
from audit_peer_return import safe_members
from package_submission import package

ROOT = Path(__file__).resolve().parents[2]


def copy_tree(source, target):
    shutil.copytree(source, target, ignore=shutil.ignore_patterns('.git', '__pycache__', '.pytest_cache'))


def b11_appendix(bundle, target):
    with zipfile.ZipFile(bundle) as archive:
        safe_members(archive)
        manifest = json.loads(archive.read('SHA256SUMS.json'))
        for name, digest in manifest.items():
            if hashlib.sha256(archive.read(name)).hexdigest() != digest:
                raise ValueError('Original B11 bundle checksum mismatch: '+name)
        prefixes = ('evidence/e11-b-241880100-02/', 'evidence/e11-extensions-241880100-02/')
        for item in archive.infolist():
            if not item.is_dir() and item.filename.startswith(prefixes):
                path = target/'b11-e11'/item.filename.removeprefix('evidence/')
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(archive.read(item))
        source = target/'b11-source'
        source.mkdir()
        for name in ('source/B11-source.tar.gz', 'provenance.json', 'README-B11交接.md', 'SHA256SUMS.json'):
            (source/Path(name).name).write_bytes(archive.read(name))
        with tarfile.open(fileobj=io.BytesIO(archive.read('source/B11-source.tar.gz'))) as snapshot:
            member = snapshot.getmember('docs/students/241880326/e11-e12/cjson-report.md')
            (source/'241880326-cjson-report.md').write_bytes(snapshot.extractfile(member).read())
    save(target/'b11-source/original-bundle-integrity.json', {
        'file': bundle.name, 'sha256': hashlib.sha256(bundle.read_bytes()).hexdigest(),
        'file_hashes_verified': len(manifest),
        'scope': 'Original B11 submission; historical PENDING statements are superseded by peer-audit/audit.json',
    })


def index(experiment):
    shared = """# A11 提交目录与复现

本包对应 EXPERIMENT。先看 DELIVERY_STATUS.json，再看 source/docs/e11-e12/最终验收与交付.md。
源码仓库为 MaxizYB/DevOps_A11，准确源码 SHA 见状态文件；实际部署 SHA 另列。

## 共同材料

- source/：本次准确 SHA 的源码快照，包含契约、Schema、新增测试、入口和 GitHub 工作流。
- source/docs/evidence/e11-e12/：A11 三位成员的报告/设计记录；组长报告在 241880439/，另两位在 231880027-independent-tests.md、231880027-ADR.md、241880411/。
- source/AI_USAGE.md、source/docs/AI使用说明.md、成员自己的 AI_USAGE：AI 使用记录；分工见 source/docs/e11-e12/最终分工与完成记录.md。
- leader/：此前组长课程样例原始运行、环境、请求、图/trace/缓存、参考 E11-B/E12 及 API 记录，保持历史来源。
- members/231880027/：成员原始刷新、复用、消费拒绝实验与 fixture.bundle；members/leader-member39-review/ 为组长后续独立复核，不能混同操作者。
- github/：本次实际 PR/CI/提交状态；github/historical/ 为原成员和课程回放 CI 的历史证据。241880411 的原始个人平台为 arm64，本包 CI/组长重跑为独立复核，不冒写成其原始本机资料。
- b11-e11/：B11 原始固定 MD 实验及扩展；b11-source/ 为原源码快照、来源清单和 241880326 的 cJSON 报告。对方原件不改写成 A11 成果。
- b11-personal/：B11 这次回传的回执、241880100 报告/ADR/CSV，保留原文；其中历史“待验收”不覆盖本次最终结论。
- peer-audit/audit.json：A11 对 B11 新版独立客户端与服务器的 228 项交叉审计；89 个文件逐字节相同，原客户端 210 项检查通过。
- tests/：本次本地单元测试、E2/E11-E12 契约结果，及实际部署时云端 61 项日志；不要把本地新增归档测试说成已在旧部署运行。
- SHA256SUMS.json：本包除清单自身之外的逐文件哈希。旧 B11 清单引用的 .o/app 是必要原始证据，保留但不执行；其他无引用编译缓存不打包。

## E11-A 复现

在独立 Linux 克隆中设置本地 git user.name 为本人数字学号，运行：

    python3 run_e11e12.py build
    python3 run_e11e12.py test
    python3 scripts/validate_contract.py
    python3 scripts/validate_e11e12_contract.py
    python3 run_e11e12.py prepare
    python3 run_e11e12.py run --request data/integration-sample/e11-a.json --out work/e11-a-new
    python3 scripts/verify_e11a_241880411.py --out work/e11-a-new

prepare 产生新内部提交/任务，SHA、job、trace 以新输出为准，不冒充原始证据；准确旧提交可从 leader/inputs/ 的 bundle 或成员 fixture.bundle 离线重建。详情见源码 README、个人报告和原始 commands/。

## 披露

cJSON 是第三方上游历史复现，不声称本组原本维护，亦不虚构教师认可该例外。服务器内存约 3.54 GiB，低于手册 4 GiB，已串行完成。
PR #42 是否已合并以 github/pr42.json 为准；材料打包不等于绕过 GitHub 批准。无需让 B11 再跑功能联调，更不需要另做压力测试。
密码、私钥、.git、旧私密交接包不在本包。不要将服务器访问凭据补进最终提交。
"""
    if experiment == 'E12':
        shared += """
## 本包 E12 主要验收入口

- peer/peer-client/b11-cjson-20261115T120834Z-fd0b8652/：B11 原始请求、健康检查、提交/重复/409、轮询、清单、下载和操作者记录。
- peer/original-return/：B11 本轮原始 ZIP、回执和报告，未改自动产物。
- server/state.json、server/evidence/：A11 独立取回同一 job 的状态和全部阶段原始记录。
- inputs/：实际请求、dataset、候选 Dockerfile、deployment.json 和 cjson.bundle；harness 不属于上游历史。
- cjson/cloud-direct/、cjson/api-client/：组长直接五阶段及跨机自验、原始失败重试，不代替 B11 运行。
- original-inputs/：B11 原始交接 ZIP 和本轮回传 ZIP，便于核对上游证据来源；不是旧含密码交接包。

离线 cJSON 准备（在新克隆中，输入目录路径按解压位置替换）：

    python3 scripts/e11e12/prepare_cjson.py --bundle /解压目录/evidence/inputs/cjson.bundle --dataset-name cjson-a11 --python-image m.daocloud.io/docker.io/library/python:3.13-slim@sha256:f82c96458eedc847b233e582eb31336f4954b39cae020b6dcf5b3ed0e5cbcd74 --debian-mirror https://mirrors.tuna.tsinghua.edu.cn
    python3 run_e11e12.py run --request data/cjson-a11-request.json --out work/e12-cjson-new
    python3 run_e11e12.py serve

用新 API 轮次须使用新幂等键和 work 目录。要离线核验本包已有联调，无需启动 Docker 或服务器：

    python3 scripts/e11e12/audit_peer_return.py --return-zip /解压目录/evidence/original-inputs/B11_cJSON正式联调.zip --handoff-zip /解压目录/evidence/original-inputs/A11-给B11-cJSON正式联调-20261115.zip --server /解压目录/evidence/server --out work/peer-audit-new

主要任务：job-80afbdd237724fd19cb49db9ec23b147；trace-7c270c4ae26845b7aeb7ce766b1fac9b。
五阶段均成功；repair 消费本轮增量报告；accepted=true，最终 findings=[]。
"""
    return shared.replace('EXPERIMENT', experiment)


def assemble(args):
    audit = json.loads((args.peer_audit/'audit.json').read_text())
    if audit['status'] != 'SUCCEEDED' or not all(item['passed'] for item in audit['checks']):
        raise ValueError('A successful independently audited B11 result is required')
    source_sha = subprocess.check_output(['git','rev-parse',args.source_sha], cwd=ROOT, text=True).strip()
    args.stage.mkdir(parents=True, exist_ok=False)
    outputs = []
    for experiment in ('E11-A', 'E12'):
        target = args.stage/experiment
        target.mkdir()
        copy_tree(args.a11_evidence/'leader', target/'leader')
        for member in ('231880027', 'leader-member39-review'):
            copy_tree(args.a11_evidence/member, target/'members'/member)
        copy_tree(args.github, target/'github')
        copy_tree(args.a11_evidence/'github', target/'github/historical')
        b11_appendix(args.b11_source_zip, target)
        personal = target/'b11-personal'
        personal.mkdir()
        original = args.peer_audit/'original-return'
        for path in original.iterdir():
            if path.is_file() and path.suffix != '.zip':
                shutil.copy2(path, personal/path.name)
        save(target/'peer-audit/audit.json', audit)
        copy_tree(args.tests, target/'tests')
        status = {
            'experiment': experiment, 'group': 'A11', 'paired_group': 'B11',
            'date': '2026-11-15', 'submission_materials_complete': True,
            'technical_acceptance': 'PASSED', 'peer_confirmation': audit['peer_confirmation'],
            'peer_job_id': audit['job_id'], 'peer_trace_id': audit['trace_id'],
            'peer_artifacts_verified': audit['artifacts_verified'],
            'peer_client_checks_passed': audit['original_client_checks_passed'],
            'independent_audit_checks_passed': audit['audit_checks_passed'],
            'deployed_source_commit': audit['deployment']['source_commit'],
            'implementation_sha256': audit['deployment']['implementation_sha256'],
            'b11_source_commit': audit['deployment']['b11_source_commit'],
            'base_commit': audit['base_commit'], 'target_commit': audit['target_commit'],
            'source_repository': 'https://github.com/MaxizYB/DevOps_A11.git',
            'github': json.loads((args.github/'pr42.json').read_text()),
            'exceptions': [
                'Third-party cJSON upstream history, not an originally group-maintained project; teacher approval not asserted',
                'Cloud visible memory approximately 3.54 GiB, below the 4 GiB handbook minimum; serial runs completed',
            ],
            'b11_rerun_required': False,
            'scope': 'A11 submission with relevant B11 originals, not all B11 members personal coursework',
        }
        if experiment == 'E12':
            copy_tree(args.peer_audit/'peer-client', target/'peer/peer-client')
            copy_tree(original, target/'peer/original-return')
            copy_tree(args.server, target/'server')
            copy_tree(args.cjson_evidence/'inputs', target/'inputs')
            for name in ('cloud-direct', 'api-client'):
                copy_tree(args.cjson_evidence/name, target/'cjson'/name)
            originals = target/'original-inputs'
            originals.mkdir()
            for path in (args.b11_source_zip, args.peer_return, args.handoff):
                shutil.copy2(path, originals/path.name)
        else:
            # The E11 accepted task uses its own teaching-history commits.
            baseline = json.loads((target/'leader/e11-a/result.json').read_text())
            status['base_commit'], status['target_commit'] = baseline['base_commit'], baseline['target_commit']
            status['e11_job_id'], status['e11_trace_id'] = baseline['job_id'], baseline['trace_id']
            status['data_provenance'] = 'Course-controlled history; member header/body reuse cases included'
        (target/'SUBMISSION_INDEX.md').write_text(index(experiment), encoding='utf-8')
        save(target/'DELIVERY_STATUS.json', status)
        filename = 'A11_'+('E11' if experiment == 'E11-A' else 'E12')+'_最终提交_20261115.zip'
        result = package(target, args.out_dir/filename, source_sha, status)
        outputs.append(result)
    save(args.stage/'package-results.json', outputs)
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('a11-evidence', 'b11-source-zip', 'peer-audit', 'peer-return', 'handoff',
                 'server', 'cjson-evidence', 'github', 'tests', 'stage'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--source-sha', default='HEAD')
    parser.add_argument('--out-dir', type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(assemble(args), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
