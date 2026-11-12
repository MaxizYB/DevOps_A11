# 231880027：E11-A 个人实验与测试记录

学号/小组/轨道：231880027 / A11 / A。
作者：@tongqianpolan。关联任务：Refs #39。
实验日期：2026-11-12。
仓库：`/root/231880027/DevOps_A11-e8-e10`。
个人分支：`feat/39-e11a-refresh-reuse`。
当前个人分支接入的公共基础 SHA：`effafdaa51f56c0291802b06f16f3ebb37e2cc1d`。
个人代码执行时尚未提交，实际文件哈希及源码副本见原始证据 `source.json` 和 `source/`，不能将基础 SHA 当作已包含个人修改。

本轮基于上述公共基础，在个人分支仓库根目录完成代码、测试与云端验证。公共 #37 尚未合并 main；合并后仍须同步最新 main 重跑，并取得本 PR 的 CI 与非作者评审，才满足 #39 的最终验收条件。

## E11 轨道集成

复用公共 `run_e11e12.py`、`pipeline.execute` 与本组既有 `scan`，没有修改公共契约、算法、入口、API、workflow 或他人测试。
本轮执行目录：`/root/231880027/DevOps_A11-e8-e10`。
本轮证据根：`/root/231880027/DevOps_A11-e8-e10/work/e11-a-231880027-validation-20261112-root`。下文相对证据路径均以此为根。

个人文件：
- `tests/e11e12/test_231880027_refresh_reuse.py`：无变化复用、函数体变化跨提交复用、共享头文件变化刷新。
- `scripts/e11e12/verify_issue39_report.py`：个人报告消费者，依次调用公共 `load_artifact` 和 `check_envelope`，记录公共异常码并返回非零退出码。
- `labs/e11e12/test_231880027_report_consumption.py`：四项消费测试，并通过自身 load_tests 将前三项 scan 测试接入公共测试发现，不改公共测试命令。
- `scripts/e11e12/run_issue39.py`：创建个人受测提交，调用公共 E11-A 入口，校验固定完整集合、任务字段、产物哈希并运行消费拒绝实验。

### 输入、独立预期与实际结果

个人受测项目先使 main.c/helper.c 共同包含 config.h，Makefile 仍只声明 main.c/unused.h 和 helper.c。仅改变头文件中的 include，再仅改变 helper.c 函数体，形成三个真实提交。

|状态|完整内部提交 SHA|输入变化|
|---|---|---|
|C0|9d888ea1ab18f1f2ba402467ab895097047b4272|共享 config.h 基线|
|C1|dd686efce61d81ad6d6a792310ecf19a41f81e28|仅 config.h 增加 include extra.h|
|C2|abe5651624ded00e336167b9a777b16be8b4e141|仅 helper.c 函数体 return 0 改为 return 0+0|

输入快照及逐文件哈希在 `inputs/base/`、`inputs/header/`、`inputs/body/`，内部历史在 `fixture-history.log`、`fixture.bundle`。项目为本人课程生成的受控样例，非真实外部项目；TeachingFixture 是参考工具设置的内部作者身份。

- C0 固定 actual：main.o→[config.h, main.c]；helper.o→[config.h, helper.c]。
- C1/C2 固定 actual：main.o→[config.h, extra.h, main.c]；helper.o→[config.h, extra.h, helper.c]。
- 三状态 declared 均为 main.o→[main.c, unused.h]；helper.o→[helper.c]。
- C0 精确三条发现：MD(main.o, config.h)、MD(helper.o, config.h)、RD(main.o, unused.h)。
- C1/C2 精确五条发现：上述三条加 MD(main.o, extra.h)、MD(helper.o, extra.h)，无其他对象发现。

|实验|base→target|刷新/复用|发现差量|实际结果|
|---|---|---|---|---|
|header|C0→C1|刷新 main.o/helper.o；复用为空|added 精确两条 extra.h MD，resolved=[]|SUCCEEDED，退出0，程序输出1|
|reuse|C1→C2|复用 main.o/helper.o；刷新为空|added=[]、resolved=[]|SUCCEEDED，退出0，程序输出1|
|unchanged 单测|同一提交无变化|两目标复用，未调用 gcc -MM|无新增/消除|通过|

两次 E11-A 均由真实 BuildChecker baseline 实际图投影建立历史缓存；增量 actual/declared/findings 分别满足固定独立预期，且与同一 target 的真实 BuildChecker 对象图、声明图及发现一致。原始 strace、Make 数据库、进程及构建日志在 `header/baseline-full/`、`header/target-full/`、`reuse/baseline-full/`、`reuse/target-full/`。
复用场景使用不同的真实提交，符合公共请求对 base/target 不同的要求。图复用不等于 Make 不重新编译；当前 scan 的依赖敏感 key 失效时保守刷新两个目标。

### 版本、任务与产物

环境镜像：`course-e11e12:231880027`。
实际镜像 ID：`sha256:128c5eb6d649dcfa9c07a3b186b49a817a2fccefee0c86e04e0ab9bfbacae7b6`。
系统/工具：Linux 5.15.0-191-generic x86_64；Python 3.13.14、GCC 14.2.0、Make 4.4.1、Git 2.47.3、strace 6.13。
实际 argv 与镜像 inspect 见 `commands/`；A11 运行容器禁用网络，使用 SYS_PTRACE、当前 root UID/GID，未挂载 Docker socket。

两任务 configuration_id 均为 `cfg-e11e12-bc70f4e9e436d256`；外层 schema_version 为 `e11e12-1`，内层 scan 报告为 `e8e10-1`，不混用两个版本。
full-check.commit 对应各自 base，incremental-check.commit 及其 data.commit 对应各自 target。同任务阶段共享 job_id/trace_id/configuration_id。

|实验|job_id|trace_id|
|---|---|---|
|header|job-4bee3d55254c4f5fa5f1fa5dd0e78db1|trace-5d44648ab1d045cb92ae038c75dcf9e1|
|reuse|job-5b9692395f3f46dd8d19c1a686e29a57|trace-c272f13653b24fa68eb6359e0966f90c|

|产物 URI|SHA256|
|---|---|
|`artifact://job-4bee3d55254c4f5fa5f1fa5dd0e78db1/full-check.json`|`82303bbbed23780bba3815115b69b122369935c8d5531fb7343883f6dbcfed55`|
|`artifact://job-4bee3d55254c4f5fa5f1fa5dd0e78db1/incremental-check.json`|`57272079d725d8d668d1d4a2e647b1b2313c9b925920a39cae3e071deadeb36d`|
|`artifact://job-5b9692395f3f46dd8d19c1a686e29a57/full-check.json`|`687a8637c39b2aa516fb223796595c275e9e88b668cbcf6faba051c38f4316c3`|
|`artifact://job-5b9692395f3f46dd8d19c1a686e29a57/incremental-check.json`|`83019868a0499312de2403a7a008ba031b9d39cf91d13e491ef8b870ed6c5ec7`|

完整产物清单分别在 `header/result.json` 和 `reuse/result.json`，各46项。已逐项核对 URI、SHA256、字节数及配置标识，阶段封装哈希亦一致。

### 新增测试与重放

公共测试入口实际运行21项（公共14项、本人消费4项和scan3项），全部 OK，无跳过，退出0；E8–E10 原有25项回归全部 OK、退出0。
测试不仅比较增量/全量彼此相等，还固定断言完整 actual/declared/findings 和精确差量；复用测试监测真实调用，确认不执行 gcc -MM。

个人分支现已接入公共基础，`run_e11e12.py` 可直接在个人仓库根目录执行。以下使用本轮已保存的个人请求，输出目录每次更换。Issue 中 `<个人请求>` 是占位符，不能原样输入。

```bash
cd /root/231880027/DevOps_A11-e8-e10

python3 scripts/validate_e11e12_contract.py
python3 run_e11e12.py test

ISSUE39_HEADER_OUT="work/e11-a-231880027-header-$(date +%Y%m%d-%H%M%S)-$$"
python3 run_e11e12.py run \
  --request data/issue39-e11-a-231880027-validation-20261112-root/header.json \
  --out "$ISSUE39_HEADER_OUT"
printf 'HEADER_EXIT_CODE=%s\n' "$?"
python3 -m json.tool "$ISSUE39_HEADER_OUT/result.json"

ISSUE39_REUSE_OUT="work/e11-a-231880027-reuse-$(date +%Y%m%d-%H%M%S)-$$"
python3 run_e11e12.py run \
  --request data/issue39-e11-a-231880027-validation-20261112-root/reuse.json \
  --out "$ISSUE39_REUSE_OUT"
printf 'REUSE_EXIT_CODE=%s\n' "$?"
python3 -m json.tool "$ISSUE39_REUSE_OUT/result.json"
git diff --check
```

正常 run 使用当前报告，预期为 SUCCEEDED；STALE_REPORT 由拒绝用例触发，公共 test 入口已包含本人的拒绝测试。本次保存的实际拒绝结果为 `work/e11-a-231880027-validation-20261112-root/consumption/stale.json`（相对于上述个人仓库）。新运行的结果使用新 OUT，不能直接套用旧 job_id、trace_id 或哈希。

本次精确执行为个人分支仓库根目录中的：
`python3 scripts/e11e12/run_issue39.py --out work/e11-a-231880027-validation-20261112-root`。
命令、stdout、stderr、退出码在 `commands/*.command.json`、`*.stdout.log`、`*.stderr.log`、`*.result.json`。
整体实验退出0，`verification.json.passed=true`。本次公共 test 入口已发现全部本人测试，无跳过。公共基础合并 main 后仍须同步并复核。

## 真实数据

本轮使用上述个人受控 Git 样例；完整 SHA、输入原件、哈希、请求、内部历史及真实动态检测证据均保留。
真实外部项目适配不在 #39 范围，未将课程样例称为真实项目验收。

## 故障与处理

消费验证使用本轮真实封装报告，没有篡改原始成功结果。个人消费者实际调用公共校验函数，错误码来自其 Failure 异常。

|消费场景|输入与消费上下文|实际结果|命令退出码|
|---|---|---|---|
|合法报告|C1 incremental-check，原哈希，预期C1|SUCCEEDED、accepted=true|0|
|旧提交报告|同一C1报告、同一原哈希，预期C2|FAILED、STALE_REPORT、accepted=false|1|
|错用基线报告|C0 full-check 被用于预期C1的基线消费上下文|FAILED、STALE_REPORT、accepted=false|1|
|篡改产物|C1报告副本追加换行，继续使用原哈希|FAILED、ARTIFACT_HASH_MISMATCH、accepted=false|1|

响应位于 `consumption/current.json`、`stale.json`、`wrong-baseline.json`、`tampered.json`。精确 argv 和退出码在 `commands/consume-*`。负向结果没有成功接受记录。
“错用基线”只证明基线报告的 commit 绑定拒绝，不声称覆盖任意错误缓存或 configuration_id 不匹配；公共 check_envelope 不承担这些额外检查。
以上为个人管线消费者复用公共校验函数的证据，未声称公共 E11-A execute 已新增外部报告输入或服务 API 已返回这些响应。

## 交付索引

|任务|文件/位置|结果|
|---|---|---|
|个人测试及复现|本文列出的四个Python文件|已实现|
|契约、公共与个人测试|commands/contracts.*、public-and-personal-tests.*、e8e10-regression.*|通过|
|自主刷新与复用|header/、reuse/、inputs/、dataset.json|通过|
|报告消费拒绝|consumption/、commands/consume-*|预期拒绝|
|综合校验|verification.json|passed=true|
|最终main、PR、CI、非作者评审|公共基础合并后补充|尚未完成|

原始 data/work、压缩包和 .git 不进入提交。本次未进行外层 commit/push 或 GitHub 变更。

AI 使用记录：[AI_USAGE.md](../../../AI_USAGE.md)。
