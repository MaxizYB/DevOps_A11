"""Explicit-allowlist A11 to B11 exchange ZIP; no secrets or whole-work recursion."""
import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path
from handoff_a_to_b import make_handoff
from verify_evidence import verify

ROOT=Path(__file__).resolve().parents[2]
KIT=Path(__file__).resolve().parent

USAGE = '''# A11 → B11：先读这里

本包是E13项目交换输入及A当次报告，不是E13/E14最终提交包。统一联系A11组长241880439。

## 在你们Linux机器上操作

1. 解压到新目录（不要覆盖你们仓库）。在包目录运行：

    python3 verify_package.py

2. 确保已有E11/E12环境、Git、GCC。用你们仓库的实际绝对路径运行：

    python3 prepare_b11.py --repo-root /你们的E11E12仓库

这会离线克隆a11-project.bundle并核对固定base/target，运行项目功能测试，校验A-result及其引用文件，生成你们仓库data/e13-from-a11内的请求和fixed-md。不会替你们运行服务，不会覆盖已有目录；操作后不要随意重命名数据目录。

3. 在你们的pipeline.py补齐外来fixed_report_sha256读取前校验。compat/fixed-report-sha256.patch提供参考，先在你们仓库git apply --check；不兼容时对照说明最小接入，不盲目覆盖自有实现。旧fixed_report请求仍可兼容，本次交换请求必须携带哈希。

4. 在你们仓库根目录执行：

    python3 run_e11e12.py run --request data/e13-from-a11/request-e11-b.json --out work/e13-from-a11-01

保存退出码及完整stdout/stderr。成功后核对fixed-md-input.json/source_report与A-result一致、validation接受、recheck无MISSING；REDUNDANT如实保留。失败也保留原始目录，不修改报告伪造通过。每次重跑用新的work目录。

## 请回传给A11组长

- 完整work/e13-from-a11-01及日志的ZIP，填写B11回执模板.md。
- 你们自己维护的项目：URL或bundle、base/target完整SHA、候选、行为/运行方式/限制/来源及真实修改测试记录。
- 最终系统已合并SHA、镜像ID/digest、CI、联系人及已知问题。系统SHA与项目SHA分开写。

镜像拉取与apt安装需要网络；失败记录为基础设施故障，不能算功能通过。所有测试在独立目录，只有DRAFT需要Docker socket。无账号密码/令牌随包提供。跨机接口沿用SSH隧道，不开放公网Docker API。

项目是2026-11-17新维护的课程演进项目，不声称长期维护第三方项目；本包不替代B11实际执行、E13完整矩阵、成员个人验收或v0.9-rc发布。
'''

RECEIPT='''# B11 → A11：E13项目与实时报告消费回执

- 实际执行者/学号、时间与时区：
- B11系统仓库URL、执行代码完整SHA、工作区状态：
- 项目base/target（须与dataset.json一致）：
- A来源job_id/trace_id/报告SHA：
- B实际job_id/trace_id：
- fixed-md-input.json/source_report核对：
- 请求、退出码、状态与错误码：
- validation accepted、recheck发现：
- 完整原始结果ZIP名称、SHA256：
- C2–C8已做项目、原始证据、阻断Issue/修复PR及同输入复测：
- 镜像ID/digest与CI链接（未完成请写待完成）：
- B11自己的项目输入包及来源/改动记录：
- 已知问题、需要A11协助的事项：

如实填写；失败结果一并回传，不填教师或A11自测为B11实测，不含密码/令牌。
'''

def package(project,a_result,out,extra=None):
    project=project.resolve();a_result=a_result.resolve()
    dataset=json.loads((project/'dataset.json').read_text())
    result=json.loads((a_result/'result.json').read_text())
    verified=verify(a_result)
    if result['target_commit']!=dataset['target'] or result['base_commit']!=dataset['base']:
        raise ValueError('A run does not belong to the fixed exchange project')
    make_handoff(a_result/'result.json',dataset['target'])
    entries={}
    for name in ('a11-project.bundle','candidate.Dockerfile','dataset.json','e11-a.json','e12.json','C0-functional-tests.log','C1-functional-tests.log','bundle-verification.log'):
        entries[name]=(project/name).read_bytes()
    for name in ('verify_package.py','prepare_b11.py','handoff_a_to_b.py'):
        entries[name]=(KIT/name).read_bytes()
    entries['USAGE.md']=USAGE.encode()
    entries['B11回执模板.md']=RECEIPT.encode()
    entries['交接说明.md']=(ROOT/'docs/e13-e14/B11交接说明.md').read_bytes()
    entries['AI_USAGE.md']=(ROOT/'AI_USAGE.md').read_bytes()
    entries['分工与完成记录.md']=(ROOT/'docs/e13-e14/分工与完成记录.md').read_bytes()
    entries['A-result/result.json']=(a_result/'result.json').read_bytes()
    entries['A-result/request.json']=(a_result/'request.json').read_bytes()
    prefix='artifact://'+result['job_id']+'/'
    for item in result['artifacts']:
        if not item['uri'].startswith(prefix):
            raise ValueError('Artifact from a different job')
        name=item['uri'][len(prefix):]
        path=(a_result/name).resolve()
        if not path.is_relative_to(a_result) or path.is_symlink() or '.git' in path.parts:
            raise ValueError('Unsafe artifact path')
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=item['sha256']:
            raise ValueError('Source artifact changed')
        entries['A-result/'+name]=raw
    diff=subprocess.check_output(['git','diff','0cbbe9e7562b565f23070180f155adf8df36aa3b','HEAD','--','labs/e11e12/pipeline.py'],cwd=ROOT)
    entries['compat/fixed-report-sha256.patch']=diff
    entries['compat/README.md']=('Patch source: A11 E11/E12 baseline to E13 foundation. Adds optional fixed_report_sha256, verifies bytes via load_artifact before JSON parse; finite positive fractional timeout.\n'
        'This reference may not apply to your divergent B11 source. Use git apply --check first; manually port equivalent checks if necessary.\n'
        'A missing hash preserves old requests, but this exchange request includes it and MUST reject changed bytes with ARTIFACT_HASH_MISMATCH.\n').encode()
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    entries['交接清单.json']=(json.dumps(dict(group='A11',receiver='B11',owner='241880439',
        system_source_commit=commit,project=dataset,a_run_verification=verified,
        status='READY_FOR_B11_EXECUTION_NOT_FINAL_GATE',credentials_included=False,
        excluded='Private snapshots and .git are omitted; all public manifest artifacts are included',
        waiting=['B11 own project','B11 actual report consumption result','Member independent checks','E13 gate and merged candidate','E14 final validation/release']),ensure_ascii=False,indent=2)+'\n').encode()
    if extra:
        entries['A11自验摘要.json']=extra.read_bytes()
    manifest={name:hashlib.sha256(raw).hexdigest() for name,raw in sorted(entries.items())}
    entries['SHA256SUMS.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
    out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,raw in sorted(entries.items()):archive.writestr(name,raw)
    with zipfile.ZipFile(out) as archive:
        if archive.testzip() is not None or any(hashlib.sha256(archive.read(n)).hexdigest()!=v for n,v in manifest.items()):
            raise ValueError('ZIP verification failed')
    return dict(file=str(out),files=len(entries),bytes=out.stat().st_size,sha256=hashlib.sha256(out.read_bytes()).hexdigest())

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--a-result',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--summary',type=Path)
    a=p.parse_args()
    print(json.dumps(package(a.project,a.a_result,a.out,a.summary),ensure_ascii=False,indent=2))
