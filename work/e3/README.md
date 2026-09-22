# E3 Local Work Area

本目录存放本机运行产生的 clone、编译产物、原始日志和临时 Git 历史。除本文件外，其内容默认由 `.gitignore` 忽略，避免将机器相关或可再生的数据误提交。

每次运行创建一个新目录：

```text
work/e3/<UTC日期时间>-issue-<编号>-<主题>/
```

示例：`work/e3/20260922T090000Z-issue-7-c0-c1-c2/`。

运行结束后，将需要追溯的命令、退出码、关键输出、完整 commit SHA、环境引用和失败原因摘要写入 [`docs/evidence/e3/`](../../docs/evidence/e3/README.md)。
