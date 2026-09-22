# E3 Fixtures

`fixtures/e3/` 只保存可版本控制的人工样例、源码快照、生成脚本和说明。它不是执行工作目录：真实 Git clone、编译产物、临时日志和系统调用跟踪输出必须写入 [`work/e3/`](../../work/e3/README.md)。

## 目录与责任

```text
fixtures/e3/
├── md-rd/                         # #6: BuildChecker 的 MD/RD Make 样例
└── echecker-history/
    └── snapshots/C0 C1 C2/         # #7: 创建真实 Git 历史的版本化快照
```

| 路径 | 责任任务 | 应保存内容 | 不应保存内容 |
| --- | --- | --- | --- |
| `md-rd/` | #6 | 源码、Makefile、Oracle、复现说明 | 编译产物、覆盖式日志 |
| `echecker-history/snapshots/` | #7 | C0/C1/C2 源码快照、创建历史脚本、Oracle | 嵌套 `.git/`、临时对象数据库 |

## 共同规则

- fixture 中的人工预期必须标记 `INSTRUCTOR_ORACLE` 或其他明确来源，且与实际工具输出分开保存。
- C0/C1/C2 的真实 Git 历史必须由版本控制的脚本或明确步骤生成到 `work/e3/`；不要把嵌套 Git 仓库提交到本仓库。
- 每次运行使用 `work/e3/<UTC日期时间>-issue-<编号>-<主题>/` 命名，例如 `work/e3/20260922T090000Z-issue-6-md-rd/`。
- 可提交的摘要证据放在 [`docs/evidence/e3/`](../../docs/evidence/e3/README.md)，包含固定版本、环境、命令、Oracle、观察和失败记录。
