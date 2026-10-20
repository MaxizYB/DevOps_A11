# E7 测试与验收记录：231880027（2026-10-20）

关联任务：Refs #22。负责人：@tongqianpolan（231880027）。

## 范围与个人贡献

本分支交付 BuildChecker 场景验证、自主判定测试、测试镜像配置与运行证据。检测器、云端入口、门禁及既有测试来自公共基础提交 `41cc04da58911a8017fc2838471e15e7df5b95ef`。检测实现由 #21 负责人主维护。

本人新增 `tests/e7/test_e7_a_gate.py` 中的 `test_original_rejects_missing_extra_and_duplicate_findings`：构造少一条、多一条、重复一条发现三个子场景，均要求判定器抛出包含 `Oracle mismatch` 的 ValueError，验证精确集合与数量。Dockerfile 增加两条 COPY，将该测试目录及依赖的 `scripts/run_e7_a_gate.py` 打包进服务镜像。未修改检测算法、服务测试、门禁预期、默认启动命令或依赖锁。AI 辅助范围及验证情况见 `AI_USAGE.md`。

## 版本与实际环境

- ECS：`47.110.157.207`；独立克隆：`/root/231880027/DevOps_A11`。
- 分支：`test/22-e7-gate-validation`。
- 构建基础 SHA：`9898fdd8daf35ba4b5e7cd6dbc241361794d6263`，运行时包含未提交的两行 Dockerfile 修改。需结合 `source-sha.txt`、`git-status.txt` 与 `source-changes.patch` 还原；不能将该 SHA 单独当作包含本次配置的完整版本。后续文档修改不属于构建快照。
- 镜像标签：`course1020-buildchecker:231880027`。
- 镜像 ID：`sha256:ce5413913ee0d4d6b30ad74ab5dec02f5bf05ff7a3d2dc19ddde21be46842e4f`，构建与门禁保存的 inspect 记录一致。
- 构建开始：2026-10-20 15:14:04；门禁开始：15:15:46（Asia/Shanghai），由 invocation.json 的 UTC 时间换算。
- 实际版本：Docker 客户端/服务端 29.8.1；宿主 Python 3.10.12；容器 Python 3.13.14、pytest 8.4.2、pluggy 1.6.0、GCC 14.2.0、GNU Make 4.4.1、strace 6.13，架构 amd64；检测报告版本 `0.2.0-teaching`。
- 独立判定容器使用 `--rm --network none`、镜像默认 app 用户，无 bind mount 或 volume。两个文件的 SHA-256 与宿主一致，证明测试和依赖脚本来自镜像。
- 实际构建场景容器使用 `--rm --network none --user 0:0 -e HOME=/tmp --cap-add SYS_PTRACE`，输入只读挂载到 `/fixture`，输出挂载到 `/evidence`。这些参数以保存的 command.json 为准。

## 证据目录与索引

以下路径均相对于当前服务器证据根目录：

```text
/root/231880027/DevOps_A11/work/e7-validation-231880027-20261020-151352/
```

归档整理仅调整目录名称，全部 261 个文件内容的 SHA-256 核对一致。原始命令及清理记录保留运行时路径 `work/e7-image-validation-231880027-20261020-151352/`；查阅文件时使用上列当前路径，不将保存命令中的旧路径直接用于重跑。

| 相对路径 | 内容 |
| --- | --- |
| `source-sha.txt`、`git-status.txt`、`source-changes.patch` | 构建基础版本和未提交配置补丁 |
| `build-command.json`、`build-console.log`、`build-exit-code.txt` | 构建入口命令、输出和退出码 |
| `build/invocation.json`、`build/build/` | 构建时间、实际 Docker 命令及 stdout/stderr、退出码 |
| `build/image/stdout.log` | 构建后的镜像身份 |
| `build/unit-tests/` | 默认 pytest 命令、日志和退出码 |
| `container-oracle/command.json`、`container-oracle/stdout.log`、`container-oracle/stderr.log`、`container-oracle/exit-code.json` | 容器内独立判定测试，unittest 结果位于 stderr.log |
| `image-files/command.json`、`image-files/stdout.log`、`image-files/hash-comparison.json` | 镜像文件哈希及与宿主的比较 |
| `gate-command.json`、`gate-console.log`、`gate-exit-code.txt` | 完整门禁入口命令、输出和退出码 |
| `full-gate/invocation.json`、`full-gate/driver/` | 门禁时间、驱动命令及日志 |
| `full-gate/gate/gate-result.json`、`full-gate/gate/results.csv` | 八项场景判定，逐项对应 |
| `full-gate/gate/image/stdout.log` | 门禁使用的镜像身份 |
| `full-gate/gate/unit-tests/stdout.log` | 门禁内 pytest 结果 |
| `full-gate/gate/<场景>/command.json`、`stdout.log`、`stderr.log` | 各场景实际命令与输出，后两文件位于同一场景目录 |
| `full-gate/gate/<场景>/fixture/`、`full-gate/gate/<场景>/evidence/` | 场景输入、报告、输入哈希、构建日志和 trace |
| `evidence-check-command.json`、`evidence-check.json`、`evidence-check-exit-code.txt` | 原始/修复报告校验命令、结果和退出码 |
| `container-cleanup.json` | 9 个记录容器的清理核对 |
| `toolchain/`、`docker-version.txt`、`host-python.txt` | 镜像工具链及实际容器、宿主版本 |

场景包括 original-1、original-2、original-3、fixed、build-failed、unsupported、timeout。成功分析还保存 actual-graph.json、declared-graph.json、processes.json、make-db.txt 和 trace/t.*；失败场景不要求具备成功分析的全部图产物。

## 测试结果与判定依据

镜像构建退出 0。默认 pytest 自动收集 15 项服务测试与 7 项判定测试，共 **22 passed**；无挂载容器中独立运行 unittest，**7 个方法通过**，其中新增方法含 3 个子场景。7 项是同组判定测试的独立运行，不另外计入 22 项。

完整门禁退出 0，恰好八项且全部 passed=true。JSON 与 CSV 的场景、passed、状态、命令退出码及 trace ID 一致。

| 门禁项 | 工具状态 | 命令退出码 | 核对内容 | 场景结果 |
| --- | --- | --- | --- | --- |
| unit-tests | 不适用 | 0 | 22 passed（15 服务＋7 判定） | PASS |
| original-1 | SUCCEEDED | 1 | 精确 MD(main.o, config.h)、RD(main.o, unused.h) | PASS |
| original-2 | SUCCEEDED | 1 | 同上，两条发现 | PASS |
| original-3 | SUCCEEDED | 1 | 同上，两条发现 | PASS |
| fixed | SUCCEEDED | 0 | findings=[]，clean/build 均退出 0 | PASS |
| build-failed | FAILED | 1 | CHECK_FAILED，build_exit_code=2 | PASS |
| unsupported | FAILED | 1 | UNSUPPORTED，build_exit_code=0 | PASS |
| timeout | TIMED_OUT | 1 | TIMEOUT，真实超时报告及 trace | PASS |

工具状态描述检测过程，命令退出码控制调用方行为，PASS/FAIL 表示场景是否符合 oracle。原始检测构建成功但发现依赖错误，因 --fail-on-findings 退出 1；故障被正确识别也可判 PASS，不能以网络或镜像失败替代目标故障。

证据校验退出 0，passed=true，原始精确两条发现、修复后为空，changed_inputs=["Makefile"]。校验针对保存报告及哈希字段，不独立重验全部 trace。

真实锚点（相对于证据根目录）：

- MD：`full-gate/gate/original-1/evidence/trace/t.14:579` 成功以 O_RDONLY 打开 config.h。报告中的 `trace/t.15:23` 是打开输出 main.o，用于关联输出，不能当作读取 config.h 的证据；进程关系见同目录 processes.json。
- RD：`full-gate/gate/original-1/evidence/make-db.txt:1041` 声明 main.o: main.c unused.h；冗余结论限于该任务和当前配置的实际观察。
- 构建失败：`full-gate/gate/build-failed/evidence/build-stderr.log`，真实缺少 config.h。
- 超时：`full-gate/gate/timeout/command.json` 设置 --timeout 1；`evidence/trace/t.14:1` 执行 sleep 10，findings.json 记录 TIMEOUT、elapsed_ms=1005。

`container-cleanup.json` 对本次 cid 文件中的完整 ID 运行 docker container ls 过滤查询，9 次退出码均为 0、查询结果为空，证明检查时这些容器均已移除，包括超时场景。未操作其他成员容器。

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

docker run --rm --network none course1020-buildchecker:231880027 \
  python3 -m unittest discover -s tests/e7 -v \
  > "$REPLAY/container-oracle.log" 2>&1
echo $? > "$REPLAY/container-oracle-exit-code.txt"

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

提交测试、镜像配置及说明时使用 Refs #22，并至少获得一名非作者组员评审。PR/Review 链接以实际记录为准。

结论适用于上述基础版本及配置补丁、镜像与输入。范围限于单 Make、每任务一个最终输出的教学样例，不等同论文完整基准。原始 work/ 和压缩备份不纳入 Git，备份排除真实 .env、令牌、私钥和登录文件。
