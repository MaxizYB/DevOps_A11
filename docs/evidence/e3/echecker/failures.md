# EChecker C0/C1/C2 Failure Notes

## 当前失败

无阻塞失败。最新一次生成与验证命令退出码为 0，实际输出满足：

- C0 clean = `10`
- C1 clean = `12`
- C2 incremental from C1 products = `12`
- C2 clean = `19`

## 剩余风险

- 当前证据已经在 Linux 环境复现；若课程后续指定不同服务器或 Docker 镜像，应在对应环境中重新运行生成脚本并更新 SHA。
- 原始运行仓库和完整日志位于 `work/e3/20260924T020000Z-issue-7-echecker-history/`，该目录按规范不提交；若复核方无法复现，应在 Issue 中记录平台、命令和完整输出。
