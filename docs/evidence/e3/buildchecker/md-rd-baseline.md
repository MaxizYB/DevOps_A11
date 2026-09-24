# Issue #6 MD/RD 基线记录

## 项目与版本

- 关联 Issue：[#6](https://github.com/MaxizYB/DevOps_A11/issues/6)
- 样例类型：GNU Make MD/RD
- fixture：`fixtures/e3/md-rd/`，复制到运行目录的 `project/`
- fixture 完整 commit SHA：`TO_BE_FILLED_AFTER_FIXTURE_COMMIT`（本次文件尚未提交）
- 当前分支：`test/6-md-rd-baseline`
- 运行目录：`work/e3/20260924T021234Z-issue-6-md-rd/`

## 环境与配置

- configuration_id：`e3-md-rd-gnu-make-v1`
- 环境清单：`docs/evidence/e3/environment/local-2026-09-24.json`，采集时间 `2026-09-24T02:12:15Z`
- OS / CPU：Darwin 25.5.0 / arm64
- Git：2.48.1；GNU Make：3.81；编译器：Apple clang 21.0.0 (clang-2100.1.1.101)；Python：3.9.11
- `strace`：当前机器未找到可执行文件；本实验未使用

## 预期 Oracle

来源：`MANUAL_ORACLE`，见 `fixtures/e3/md-rd/oracle.json`。

| 类型 | 目标 | 依赖 | 人工判断 |
| --- | --- | --- | --- |
| MISSING | `main.o` | `config.h` | `main.c` 包含 `config.h`，Makefile 的 `main.o` prerequisites 未声明它。 |
| REDUNDANT | `main.o` | `unused.h` | Makefile 声明了 `unused.h`，编译 `main.c` 不使用它。 |

## 命令与结果

以下命令在运行副本的 `project/` 中执行。修改前各等待 2 秒，完整命令、逐条退出码与 stdout/stderr 见 [`commands.md`](commands.md)。

| 步骤 | 命令摘要 | 退出码 | 原始日志 | 关键输出 |
| --- | --- | --- | --- | --- |
| 初始构建 | `make clean`; `make`; `./app` | 0 / 0 / 0 | `01-initial-build.log` | `cc -c main.c -o main.o`；程序 `1` |
| MD 增量 | `sleep 2`; 改 `config.h` 为 `VALUE 2`; `make`; `./app` | 0 / 0 / 0 / 0 | `02-md-incremental.log` | ``make: `app' is up to date.``；程序 `1` |
| clean 对照 | `make clean`; `make`; `./app` | 0 / 0 / 0 | `03-md-clean-build.log` | `cc -c main.c -o main.o`；程序 `2` |
| RD 重编译 | `sleep 2`; 改 `unused.h` 注释; `make`; `./app` | 0 / 0 / 0 / 0 | `04-rd-rebuild.log` | `cc -c main.c -o main.o`；程序 `2` |

原始日志均位于上述运行目录。四组命令的 stderr 均为空。

## 实际观察

修改 `config.h` 后，普通 `make` 未重新编译 `main.o`，程序仍输出旧值 `1`；clean build 后输出 `2`。只改 `unused.h` 后，`main.o` 重新编译，输出仍为 `2`。行为与人工 Oracle 一致，详见 [`observations.md`](observations.md)。

## 失败与下一步

- 当前失败：本次基线实验没有阻塞性失败。
- 下一步：人工提交 fixture 后补充最终 SHA；后续创建 PR；另一位组员按 fixture README 复现。
- Cross-member reproduction: pending review.

## 个人贡献与追溯

- 作者：@andelutixia
- PR：待后续创建
- 最终提交 SHA：`TO_BE_FILLED_AFTER_FIXTURE_COMMIT`
