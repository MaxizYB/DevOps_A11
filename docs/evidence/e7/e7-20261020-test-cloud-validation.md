# E7 云端验证记录：231880027（2026-10-20）

关联任务：Refs #22。负责人：@tongqianpolan（231880027）。

## 范围与个人贡献

本分支交付 BuildChecker 的云端场景验证、自主判定测试和运行证据。检测器、云端入口、门禁及既有测试来自公共基础提交 `41cc04da58911a8017fc2838471e15e7df5b95ef`；不是本人从零实现。E6 检测实现由 #21 负责人主维护，本次没有修改服务实现、服务测试或 Dockerfile。

本人交付的 AI 辅助修改为 `tests/e7/test_e7_a_gate.py` 中的 `test_original_rejects_missing_extra_and_duplicate_findings`。在正确两条发现的基础上构造少一条、多一条和重复一条三个子场景，均要求 `evaluate` 抛出包含 `Oracle mismatch` 的 ValueError。该测试验证精确集合与数量，防止宽松判定吞掉多余或重复结果；没有放宽参考预期。本次独立判定测试在 ECS 宿主执行，当前服务镜像不包含 `tests/e7/`。若验收要求本人测试本身进入镜像，仍需协调测试打包方式。

## 本次版本与环境

- ECS：`47.110.157.207`；独立克隆：`/root/231880027/DevOps_A11`。
- 分支：`test/22-e7-gate-validation`。
- 运行记录中的基础源码 SHA：`41cc04da58911a8017fc2838471e15e7df5b95ef`。
- 运行时尚有未提交的 E7 测试和 AI 记录修改。必须结合 `source-changes.patch` 还原；不能称基础 SHA 已包含个人测试。补丁记录的是运行时状态，后续整理的本文档不属于当时快照。
- 镜像标签：`course1020-buildchecker:231880027`。
- 构建与门禁保存的镜像 ID 一致：`sha256:b1677429ab19917bad50adbfe68f463ab2c802612a1af344eeba3c3abf99d8f8`。
- 构建开始时间：2026-10-20 14:07:55（Asia/Shanghai）；门禁开始时间：14:09:28，依据各自 `invocation.json` 的 UTC 时间换算。
- 容器测试日志：Linux、Python 3.13.14、pytest 8.4.2、pluggy 1.6.0；检测报告版本：`0.2.0-teaching`。
- 场景容器实际参数：`--rm --network none --user 0:0 -e HOME=/tmp --cap-add SYS_PTRACE`；输入只读挂载到 `/fixture`，输出挂载到 `/evidence`。本次记录真实使用 root UID，不宣称采用 E4 非 root、只读根文件系统或资源限制参数。
- GCC、Make、strace、Docker 和宿主 Python 的实际版本未在本次索引中独立核对，后续补充环境记录；不把 Dockerfile 声明版本当作已核实的运行值。

## 证据根目录与索引

以下路径均相对于服务器上的真实根目录：

```text
/root/231880027/DevOps_A11/work/e7-validation-231880027-20261020-140239/
```

| 相对路径 | 内容 |
| --- | --- |
| `source-sha.txt`、`git-status.txt`、`source-changes.patch` | 基础版本、分支及运行时未提交修改 |
| `oracle-tests.log`、`oracle-exit-code.txt` | 独立判定测试日志与退出码 |
| `build-console.log`、`build-exit-code.txt` | 构建入口输出与退出码 |
| `build/invocation.json` | 构建时间、镜像和入口信息 |
| `build/build/` | 实际构建命令、stdout/stderr、退出码 |
| `build/image/stdout.log` | 构建后镜像 inspect 记录 |
| `build/unit-tests/` | 镜像服务测试命令、日志、退出码 |
| `gate-console.log`、`gate-exit-code.txt` | 完整门禁入口输出与退出码 |
| `full-gate/invocation.json`、`full-gate/driver/` | 门禁入口信息、驱动命令、日志与退出码 |
| `full-gate/gate/gate-result.json`、`full-gate/gate/results.csv` | 八项判定结果，逐项对应 |
| `full-gate/gate/image/stdout.log` | 门禁使用的镜像 inspect 记录 |
| `full-gate/gate/unit-tests/` | 门禁内服务测试命令和日志 |
| `full-gate/gate/<场景>/command.json`、`stdout.log`、`stderr.log` | 每个检测场景的实际命令与输出 |
| `full-gate/gate/<场景>/fixture/` | 各场景输入副本 |
| `full-gate/gate/<场景>/evidence/` | 报告、输入哈希及该场景保存的 trace/构建日志等 |
| `evidence-check.json`、`evidence-check-exit-code.txt` | 原始/修复报告及输入哈希校验 |

场景为 `original-1`、`original-2`、`original-3`、`fixed`、`build-failed`、`unsupported`、`timeout`。成功场景还保存 `actual-graph.json`、`declared-graph.json`、`processes.json`、`make-db.txt` 和 `trace/t.*`；失败场景不要求具有成功分析的全部图产物。单场景命令退出码汇总于 JSON/CSV，外层入口另有退出码文件。

## 实际结果与判定依据

独立判定测试为 7 个方法（新增方法含 3 个子场景），结果 `OK`、退出 0。镜像构建退出 0，构建后的服务测试 15 项通过。完整门禁退出 0，八项全部 `passed=true`，JSON 与 CSV 的场景、状态、退出码及 trace ID 一致。

| 门禁项 | 工具状态 | 命令退出码 | 核对内容 | 场景结果 |
| --- | --- | --- | --- | --- |
| unit-tests | 不适用 | 0 | 15 passed | PASS |
| original-1 | SUCCEEDED | 1 | 精确 MD(main.o, config.h)、RD(main.o, unused.h) | PASS |
| original-2 | SUCCEEDED | 1 | 同上，两条发现 | PASS |
| original-3 | SUCCEEDED | 1 | 同上，两条发现 | PASS |
| fixed | SUCCEEDED | 0 | findings=[]，clean/build 均退出 0 | PASS |
| build-failed | FAILED | 1 | CHECK_FAILED，build_exit_code=2 | PASS |
| unsupported | FAILED | 1 | UNSUPPORTED，build_exit_code=0 | PASS |
| timeout | TIMED_OUT | 1 | TIMEOUT，真实超时报告及 trace | PASS |

工具状态描述检测过程，命令退出码控制调用方行为，场景 PASS/FAIL 表示是否符合预设 oracle。原始检测在构建成功且发现依赖错误时因 `--fail-on-findings` 退出 1；这不是检测崩溃。故障场景被正确识别也判 PASS，不能以网络或镜像失败替代。

原始三次均 clean/build 退出 0，每次精确两条发现；修复后为空。`verify_e6_evidence.py` 退出 0，报告 `passed=true`、`changed_inputs=["Makefile"]`。该校验验证保存报告及其哈希字段，不独立重验全部 trace。

真实证据锚点（相对于证据根目录）：

- 原始第一次 MD：`full-gate/gate/original-1/evidence/trace/t.14:579` 成功以 O_RDONLY 打开 `config.h`；报告的另一锚点 `trace/t.15:23` 是以 O_RDWR|O_CREAT|O_TRUNC 打开输出 `main.o`，用于关联输出，不能当作读取 config.h 的证据。进程关系见同目录 `processes.json`。
- RD 声明：`full-gate/gate/original-1/evidence/make-db.txt:1041`，`main.o: main.c unused.h`；其含义限于本次配置中未观察到该任务读取 unused.h。
- 构建失败：`full-gate/gate/build-failed/evidence/build-stderr.log`，实际报 `main.c:2:10: fatal error: config.h: No such file or directory`。
- 超时：`full-gate/gate/timeout/command.json` 设置 `--timeout 1`；`evidence/trace/t.13:1` 执行 `sleep 10`；`evidence/findings.json` 记录 `elapsed_ms=1005` 及 `Command exceeded 1s; process group was killed`。进程组被杀是工具报告，容器清理尚待独立核对。

## 重放命令

在本学号克隆中执行，先确保新增测试存在。每次换用新的输出目录；下面路径为重放示例，不是上述已运行目录。原始副本保留，修复由门禁在独立副本中进行。

```bash
cd /root/231880027/DevOps_A11
REPLAY="work/e7-replay-231880027-$(date +%Y%m%d-%H%M%S)"
mkdir "$REPLAY"
git rev-parse HEAD > "$REPLAY/source-sha.txt"
git status --short --branch > "$REPLAY/git-status.txt"
git diff > "$REPLAY/source-changes.patch"

python3 -m unittest discover -s tests/e7 -v > "$REPLAY/oracle-tests.log" 2>&1
echo $? > "$REPLAY/oracle-exit-code.txt"

python3 scripts/lab_cloud.py build --image course1020-buildchecker:231880027 \
  --out "$REPLAY/build" > "$REPLAY/build-console.log" 2>&1
echo $? > "$REPLAY/build-exit-code.txt"

python3 scripts/lab_cloud.py gate --image course1020-buildchecker:231880027 \
  --out "$REPLAY/full-gate" > "$REPLAY/gate-console.log" 2>&1
echo $? > "$REPLAY/gate-exit-code.txt"

python3 scripts/verify_e6_evidence.py \
  --before "$REPLAY/full-gate/gate/original-1/evidence/findings.json" \
  --after "$REPLAY/full-gate/gate/fixed/evidence/findings.json" \
  > "$REPLAY/evidence-check.json" 2>&1
echo $? > "$REPLAY/evidence-check-exit-code.txt"
```

逐段执行并读取退出码及日志；任何一步不符合预期时先保留日志排查，不把后续输出当作已验收。

## 本分支交接与验证边界

1. 补容器清理核对和完整实际工具版本记录；若要求自主测试进入服务镜像，先协调最小打包方式。
2. 提交本次测试与说明，普通 PR 使用 `Refs #22`，至少获得一名非作者组员评审。当前无本次 PR/Review 链接，不虚构链接。

本记录的验证结论适用于上述源码版本及补丁、镜像和输入配置。范围限于单 Make、每任务一个最终输出的教学样例，不等同论文完整基准。本次采用上列新目录的成功记录。

原始 `work/` 和压缩备份不纳入 Git。备份排除真实 .env、令牌、私钥及登录文件。
