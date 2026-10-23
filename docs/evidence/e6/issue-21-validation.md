# Issue #21：E6 实现与验证记录

负责人：`@andelutixia`（241880411）。2026-10-22 完成 E6 原始检测、修复复检和 E7 自检：原始精确两条 MD/RD，修复后为空，服务测试 19 项、独立判定测试 6 项、门禁 8 项通过。

## 源码与环境

- 公共基础：`41cc04da58911a8017fc2838471e15e7df5b95ef`；分支：`feat/21-e6-full-check-evidence`。
- ECS 克隆：`/root/241880411/DevOps_A11-e6-20261022-1225`，由公共 main 的完整 Git bundle 创建；Git 本地身份为 `241880411` / `3320603255@qq.com`。
- 测试源码为公共基础加两份源码文件的工作区修改，归档 SHA256：`15b3aca77ec25336c46ce59be38814082edb273b85bc19af603087f615b0a41f`。各文件哈希及差异见原始证据的 `source-manifest.json`、`tested-source.patch`。
- 镜像标签：`course1020-buildchecker:241880411-e6-20261022-1225`；检测固定使用镜像 ID `sha256:55fd4e56dd0bc546e3bce9c3e8000fc57e40eec298fd8e5e959b8f54c694c2e8`。
- 宿主机：Ubuntu 22.04.5 LTS、x86_64、2 CPU、3.5 GiB 内存；Docker 29.8.1、Compose 5.5.1、Git 2.34.1、Make 4.3、Python 3.10.12；doctor 的 `problems=[]`。
- 镜像内：Python 3.13.14、Make 包 4.4.1-2、GCC 包 4:14.2.0-1、strace 包 6.13+ds-1、pytest 8.4.2。完整工具版本保存在 `commands/04-toolchain/stdout.log`。

## 实现说明与本次修改

[fullcheck.py](../../../services/buildchecker/buildchecker/fullcheck.py)、[CLI](../../../services/buildchecker/buildchecker/cli.py) 和实验驱动来自 `E5-7.zip` 的 A-buildchecker 学生参考包，由 #20 接入。本次在参考实现上补充两项边界处理和四项回归测试。

| 代码入口 | 处理方式 |
| --- | --- |
| `trace_events` | 解析每个 `t.PID`，合并 unfinished/resumed 调用，保留调用开始行号；不完整记录显式拒绝。 |
| `load_processes`、`execution_graph` | 从成功的 fork/clone、exec 建立进程树，以 Make 直接子进程为 recipe 作业，将 cc/cc1/as 的访问归入同一作业；子进程继承 fork 时的 cwd。 |
| `project_path`、`execution_graph` | 按 cwd 归一化相对路径，只保留项目内路径。失败访问、系统路径、目录打开及同一作业内生成的临时文件不计依赖；成功 `O_RDONLY` 打开作为读观察，写打开/rename 形成目标。Make 自身读取不计入编译输入。 |
| `declaration_graph` | 解析 Make 数据库的 `# Files` 段，保留声明行号，展开 `.PHONY`；order-only 依赖单独保存，不参与普通依赖差集。 |
| `analyze` | 对实际观察到的目标计算 `Actual - Declared` 得到 MD，`Declared - Actual` 得到 RD。RD 结论限定于当前构建配置和 recipe。 |
| `full_check` | 复制输入并计算哈希，在副本 clean 后通过 `strace -ff -s 4096 -e trace=%file,%process` 跟踪 `make -p`，输出两图、进程摘要和 findings。 |

[test_fullcheck.py](../../../services/buildchecker/tests/test_fullcheck.py) 的新增测试覆盖：

| 边界问题与修复 | 自主测试期望及价值 |
| --- | --- |
| Make 自身切换到不同于项目根的 cwd 后，两图的相对路径基准不同；现显式返回 `UNSUPPORTED`。 | 成功切换到其他目录时拒绝分析，失败 chdir 时仍按原项目根解析，避免虚假 MD；recipe 子进程 cwd 继承保持有效。 |
| 构建中新建符号链接可能使词法路径与实际访问对象不一致；成功 `symlink`/`symlinkat` 现显式返回 `UNSUPPORTED`。 | 两种调用成功时均拒绝，失败时正常依赖集合不变，避免错误保留或归属依赖。 |

四项新增测试在原实现上产生三处失败断言（两个链接 subTest 和 Make cwd 测试）；修复后检测器 16 项全通过。另用真实 Linux fixture 执行链接后编译、`make -C src app` 两项复现，均为 build 退出 0、报告 `FAILED/UNSUPPORTED`、CLI 退出 1。

## 命令与结果

在上述 ECS 克隆执行；重跑时更换 `E6_RUN`，保留旧证据。

```sh
E6_RUN=work/issue21-20261022-1225
E6_TAG=course1020-buildchecker:241880411-e6-20261022-1225
python3 scripts/lab_cloud.py doctor --out "$E6_RUN/doctor"
python3 scripts/lab_cloud.py build --image "$E6_TAG" --out "$E6_RUN/build" --build-timeout 1200
E6_IMAGE=$(docker image inspect "$E6_TAG" --format '{{.Id}}')
python3 -m unittest discover -s tests/e7 -v
python3 scripts/lab_cloud.py e6 --image "$E6_IMAGE" --out "$E6_RUN/before"
python3 scripts/lab_cloud.py e6 --fixed --image "$E6_IMAGE" --out "$E6_RUN/after"
python3 scripts/verify_e6_evidence.py \
  --before "$E6_RUN/before/evidence/findings.json" \
  --after "$E6_RUN/after/evidence/findings.json"
python3 scripts/lab_cloud.py gate --image "$E6_IMAGE" --out "$E6_RUN/gate"
```

| 检查 | 退出码 | 结果 |
| --- | ---: | --- |
| doctor / build | 0 / 0 | 环境通过；重建镜像的服务测试 19 项通过（3 CLI + 16 检测器） |
| E7 独立判定测试 | 0 | 6 项通过 |
| E6 before | 1 | `SUCCEEDED`，clean/build 均为 0，精确两条 MD/RD |
| E6 after | 0 | `SUCCEEDED`，clean/build 均为 0，`findings=[]` |
| E6 证据校验 | 0 | `passed=true`，仅 Makefile 输入哈希改变 |
| E7 门禁 | 0 | 服务测试、原始三次、修复、构建失败、多输出、超时共 8 项通过，JSON/CSV 一致 |

E6 两次均开启 `--fail-on-findings`，before 的退出 1 表示发现依赖问题，检测本身成功。构建错误报告 `FAILED/CHECK_FAILED`，不支持输入报告 `FAILED/UNSUPPORTED`，超时报告 `TIMED_OUT/TIMEOUT`，CLI 均退出 1。

## MD/RD 证据与修复对照

before trace_id：`e6-ecf93a06cc984cbf8e0fc02e9680e1d8`；after trace_id：`e6-8558ed7d4cdf4fb8a6a72e79b28ccd85`。

原始实际图为 `main.o -> {main.c, config.h}`、`app -> main.o`；声明图在 `main.o` 上声明 `main.c`、`unused.h`：

| 发现/目标 | 原始位置 | 依据 |
| --- | --- | --- |
| `MISSING(main.o, config.h)` | `before/evidence/trace/t.14:579` | PID 14（cc1）执行 `openat(AT_FDCWD, "config.h", O_RDONLY\|O_NOCTTY) = 4`，成功读打开但未声明 |
| `main.o` 输出 | `before/evidence/trace/t.15:23` | PID 15（as）成功以 `O_RDWR\|O_CREAT\|O_TRUNC` 打开 main.o；与 PID 14 同属 job_pid 13（cc） |
| `REDUNDANT(main.o, unused.h)` | `before/evidence/make-db.txt:1041` | 声明为 `main.o: main.c unused.h`，该 recipe 未读取 unused.h |

`processes.json` 保存 `12(make) -> 13(cc) -> {14(cc1), 15(as)}`，证明读取与写入属于同一编译作业。

修复仅在副本中将 `main.o: main.c unused.h` 改为 `main.o: main.c config.h`，原始 fixture 保留。六个输入文件集合相同，仅 Makefile 哈希变化，修复后 findings 为空。除现有校验脚本外，`audit_evidence.py` 重新计算输入哈希、检查单行替换并重放保存的 trace，图、findings、进程和证据行一致，`evidence-audit.json` 为 `passed=true`。

## 证据索引与范围

云端：`/root/241880411/DevOps_A11-e6-20261022-1225/work/issue21-20261022-1225/`。

本地备份：`work/e6-20261022-241880411/remote/issue21-20261022-1225/`。下表路径相对该根目录，原始产物均留在被 Git 忽略的 `work/`。

| 路径 | 内容 |
| --- | --- |
| `source-manifest.json`、`git-state.json`、`tested-source.patch` | 源码文件哈希、基础 SHA、身份及修改差异 |
| `doctor/env.json`、`build/`、`image-id.txt`、`commands/` | 环境、镜像、工具版本、测试，以及实际命令/stdout/stderr/退出码 |
| `before/`、`after/` | 输入副本与哈希、actual/declared graph、findings、processes、make-db、trace、clean/build 日志及容器命令/退出码 |
| `gate/gate/gate-result.json`、`gate/gate/results.csv` | 八项门禁结果与各场景原始记录 |
| `boundary-checks/`、`boundary-result.json`、`evidence-audit.json` | 新增边界复现与产物一致性复核 |

采集及复核脚本保留在云端 `work/source-issue21/` 和本地同名备份；源码归档、manifest 与回归日志另见本地 `work/e6-20261022-241880411/source/`。

教学范围为单个 Make 进程、每 recipe 一个最终输出，依赖依据是成功 read-open 观察。不支持递归 Make、共享 cwd 线程、符号链接解析、Make `-C` 和需要目录 FD 跟踪的路径；本次不涉及 EChecker 或 REST 服务。组员评审及合并后配合 #22 的最终版本复验待完成。
