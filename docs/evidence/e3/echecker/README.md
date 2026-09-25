# EChecker E3 Evidence

本目录保存 [#7](https://github.com/MaxizYB/DevOps_A11/issues/7) 的可提交证据摘要。原始运行仓库、编译产物和完整验证日志位于 `work/e3/20260924T020000Z-issue-7-echecker-history/`，不提交到仓库。

## 文件

- `commits.json`：C0/C1/C2 的真实 40 位 SHA、tag 和 baseline 关系。
- `oracle.json`：人工 Oracle，包括声明依赖、实际依赖、MD 判断和预期输出。
- `commands.md`：复现命令、退出码和关键输出。
- `observations.md`：实际观察与验收条件对照。
- `failures.md`：失败记录、已修正问题和剩余风险。

## 关键关系

- `base_commit` 使用 C0。
- C1 和 C2 的 baseline 图应来自 C0 的 `ACTUAL_GRAPH`。
- `baseline.commit == base_commit`。
- C0、C1、C2 使用同一 Linux 复现配置 `cfg-linux-ubuntu22-gcc11-o0-v1`；C2 额外记录编译命令变化 `-DMODE=7`，用于验证命令变化造成的增量行为差异。
