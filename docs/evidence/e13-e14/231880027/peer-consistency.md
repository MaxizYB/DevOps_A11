# 231880027：E13 配对检测与 E14 证据关联核查

作者：@tongqianpolan / 231880027
日期：2026-11-19
关联：Refs #45

## 版本、输入与范围

- 独立目录：`/root/231880027/DevOps_A11-e13-e14`。
- 个人分支：`test/45-e13-peer-consistency`。
- 公共源码：`b5f66f3bc52ab20364141ce193cd873d2d653973`，包含组长 #49 的 cJSON 四服务适配，属于 PR #50 的代码基础；不是 main 已合并或 RC 已验收的声明。
- 被测 B11 cJSON base：`cf0d87a095becada87336ed786f11070e9a037b5`。
- 被测 B11 cJSON target：`f0c8fa4f812abe50964956cd0580ab963430ba35`。
- 服务镜像：`course-e11e12:231880027`，ID `sha256:128c5eb6d649dcfa9c07a3b186b49a817a2fccefee0c86e04e0ab9bfbacae7b6`；实际工具版本保存在下述 `tool-versions.stdout.log`。
- 检测范围：`make cJSON_Utils.o`；不扩大为整个 cJSON 所有目标。个人新增脚本尚未提交，执行时源码 SHA、个人文件哈希和副本见 `source.json` 与同目录 `.py`。

原始证据以下均相对本仓库根目录：

- E13 正式个人运行：`work/e13-45-231880027-20261119-validation/`。
- 回归、契约和独立核查日志：`work/issue45-checks-20261119/`。
- E14 个人重放：首次失败在 `work/e14-45-231880027-20261119/`；恢复成功在 `work/e14-45-231880027-20261119-recovery/`。
- 首次个人消费控制项因容器 UID 写入权限失败，保存在 `work/e13-45-231880027-20261119/`；仅在个人 Docker 启动命令加入当前 UID/GID 后以新目录完整重跑，没有修改公共实现。

## 独立预期与 C1

运行前保存 `expectations.json`。通过 Git diff 确认两提交仅 `test.c` 改变；`cJSON_Utils.c`/`cJSON_Utils.h` 的 include 和 Make 规则构成预期依据，保留两版本原文，不以被测工具输出生成预期。

- 实际依赖预期：`cJSON.h`、`cJSON_Utils.c`、`cJSON_Utils.h`。
- 声明依赖预期：`cJSON_Utils.c`、`cJSON_Utils.h`。
- 精确发现：`MISSING(cJSON_Utils.o, cJSON.h)`；没有 REDUNDANT、额外或重复发现。
- `refreshed=[]`，`reused=["cJSON_Utils.o"]`。仅测试函数体改变，不改变该目标的编译、头文件和预处理输入。

个人 C1 的公共 E11-A 命令退出 0。基线全量、目标全量和目标增量与上述预期一致；基线缓存 SHA、commit 和 key 已核对。MD 回溯到本次成功的只读 open/openat，声明回溯到本次 Make 数据库；真实 trace 文件名、行号、原文及声明行写入 `checks.json` 的 `C1_A.trace`，不照搬组长 PID。

个人运行的 job_id、trace_id、configuration_id、发现与产物数见 `checks.json/C1_A`；来源 SHA、bundle/candidate SHA 见 `source.json`。请求、命令、退出码、stdout/stderr、图、缓存、Make 数据库和 trace 均保留。

已通过公共 handoff 生成 `fixed-md-for-leader.json`（个人 E13 证据根目录，哈希及退出码见 `handoff-for-leader-command.json`），仅供组长领取，未发送。本轮个人报告尚未由组长发送给 B11，`C1_B` 标为 `PENDING_LEADER_RECEIPT`。组长文档已经记录 B11 对此前组长报告的消费，不能据此声称 B11 已消费本轮新 job/report。本人未联系、发送或催办 B11。

## C2、C3、C7、C8

| 用例 | 实际执行及判定 | 原始证据 |
| --- | --- | --- |
| C2 | 正确目标控制项退出 0；原报告配错误目标返回 STALE_REPORT、退出 1；公共 handoff 同样拒绝错误 target，未生成输出 | `C2-control*`、`C2*`、`commands.json` |
| C3 | 原报告副本追加换行，沿用原 SHA；返回 ARTIFACT_HASH_MISMATCH、退出 1；原件字节保持不变 | `C3-report.json`、`C3-consumption.json`、`checks.json/C3` 原/改后 SHA、日志 |
| C7 | 错误 base 的实际任务 FAILED/COMMAND_FAILED、退出 1；之后正常请求 SUCCEEDED、退出 0；job/trace 不同，成功清单逐文件核验，失败目录前后哈希不变 | `C7-failed/`、`C7-recovered/`、独立请求、`C7-failed-file-hashes.json` |
| C8 | 个人 loopback 18445 端口启动真实公共异步 API；同键同输入两次 HTTP 202、同 job；同键异 target HTTP 409/IDEMPOTENCY_CONFLICT；正常 job 最终成功且只新增一个任务 | `C8-first.json`、`C8-repeat.json`、`C8-conflict.json`、原始响应、轮询、任务清单、state 与容器日志 |

C2/C3 使用已有 #39 CLI 调用公共 `pipeline.load_artifact` / `check_envelope`，不是模拟错误码，也不是 B11 HTTP 消费实测。C8 使用实际 HTTP，不以单元测试代替。本人的 API 容器已按名称停止并移除；原项目文件、HEAD、工作区、bundle/candidate 哈希前后不变，见 `input-before.json`、`input-after.json`、`input-git.json`。

## E14：独立核查与个人重放分开记录

已独立读取、重算组长以下成功预检原件：

`/root/241880439/DevOps_A11-e14-issue49-20261119/work/e14-issue49-cloud-20261119-mirror/success/`

核查结果保存在 `work/issue45-checks-20261119/e14-audit.json`，退出 0：1659 项清单产物 SHA/字节数、五阶段顺序与成功状态、base/target、同轮 job/trace、基线图与缓存、目标全量/增量、报告与补丁 SHA、验证接受及最终发现均已核对。

- 原运行者：241880439；本次核查者：231880027。
- job：`job-c4c2d0a813084df999f1e310bacf7dc1`。
- trace：`trace-41d995e5af7d43f8b0793f62c7097a29`。
- 增量报告 SHA：`44f69ec354e5814b24b86186a5335b72fd868abede5d5796a737df37e4293645`。
- 补丁 SHA：`a481b9a52f7e07d9369bc67cf80a1ff5f703b21781f2fb13791f78713c21dbf0`。
- 最终 MD/RD 均为空，符合本 cJSON 检测目标；没有将 RD 强行过滤为成功。

证据限制：公共 Compose 结果保存了响应，但未单独保存 MDFixer 请求原文；已有报告 SHA 与公共编排调用代码能关联，不能声称已独立取得该 HTTP 请求字节。

为补齐这一直接证据，另写个人 `run_e14_audit.py`，以独立项目 `e14-45-231880027`、loopback 18541–18544 重放公共编排，逐次保存 HTTP payload；未编辑公共 Compose、service 或 orchestrate。B11 原候选保持不变，执行副本仅改 registry 来源，固定 digest 保留，差异见 `input-provenance.json`。

首次个人重放在 DRAFT 阶段失败：外层 FAILED / HTTP 422，内层 TIMED_OUT，`Docker client command exceeded 600.0s`。请求、候选、构建日志、服务日志、退出记录及清理记录保留在个人 E14 目录。没有将环境超时记作受控故障测试通过，也没有据组长成功结果改写本次状态。本次 Compose 四容器及网络已执行 down。

个人四服务已在相同 B11 base/target、相同候选字节及原 600 秒时限下恢复成功；前次失败原件保留。


### 本人恢复重放：五阶段及直接请求绑定通过

恢复证据：`work/e14-45-231880027-20261119-recovery/`。由 231880027 独立启动四服务并执行，非复制组长结果。

- 公共流程依次为 DRAFT → full-check → incremental-check → repair → recheck，全部 SUCCEEDED；`run-exit.json` 退出码 0。
- job：`job-0e61317ef48548a8b27c807dcd732e03`；trace：`trace-3fb39c2d0e0049fc8a008c07d0a5d1a1`；个人核查 1665 项产物的 URI、字节数和 SHA，通过。
- 实际增量报告 SHA：`12b1245b23ca52a9720b6557d2460227a38423f99b66a4ebf144c0029c79ddb1`；补丁 SHA：`a481b9a52f7e07d9369bc67cf80a1ff5f703b21781f2fb13791f78713c21dbf0`。
- `run/repair-response.request.json` 保存实际 MDFixer HTTP payload；其中报告 URI/SHA、target、job/trace 及处理目录均与本轮产物一致，`repair_request_recorded=true`。
- 验证接受、五项验证检查通过；最终 `final-full/findings.json` 与 recheck 一致，MD/RD 均为空。
- 恢复使用同一项目、相同候选及故障 Dockerfile 的字节 SHA、相同 600 秒 build_timeout 和公共 HTTP 时限；没有放宽状态、发现集合或哈希判定。环境下载探测及恢复构建原始日志保留。
- 前次超时在下载 Debian 依赖期间；本轮真实完成缺 make 的初始构建失败、候选依赖安装、构建/运行与其余四阶段，不把缓存或容器 healthy 代替端到端运行。
- 原项目 HEAD/工作区前后不变；本次四个服务容器及独立网络均已关闭，清理记录见 `commands.json` 和 `compose-down.*.log`。

本轮个人 E14 重放和证据关联核查完成。公共分支合并后候选版本的最终复验、B11 本轮新报告消费、PR CI 与组员评审仍需另行完成。

## 测试、个人贡献与后续

- E11/E12：68 项通过；E13/E14：42 项通过（含本人新增 8 项）。日志在 `work/issue45-checks-20261119/`。
- 两套契约校验通过；提交前仍需 `git diff --check` 和 PR CI、真实非作者评审。
- 个人新增：`scripts/e13e14/run_peer.py`、`verify_peer.py`、`run_e14_audit.py`、`labs/e13e14/tests/test_peer.py`。不修改检测算法、公共契约、编排或发布脚本。
- 自主测试检查重复/额外发现、错误刷新、错误缓存、跨任务产物、篡改字节，以及重新签哈希仍属于错误提交的报告，防止核查器假通过。
- AI 使用记录：[AI_USAGE.md](../../../../AI_USAGE.md)。

重放命令（每次替换为新输出目录）：

```bash
python3 scripts/e13e14/run_peer.py --out work/e13-45-231880027-new --port 18445
python3 scripts/e13e14/verify_peer.py a work/e13-45-231880027-20261119-validation/C1
python3 -m unittest discover -s labs/e13e14/tests -p test_peer.py -v
python3 run_e11e12.py test
python3 scripts/validate_contract.py
python3 scripts/validate_e11e12_contract.py
python3 scripts/e13e14/run_e14_audit.py --out work/e14-45-231880027-new
git diff --check
```

待办：组长协调本轮报告交接/消费证据；公共代码合并后同步重跑、完成 PR CI 与组员评审。