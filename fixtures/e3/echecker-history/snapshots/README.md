# EChecker C0/C1/C2 Snapshots

本目录保留用于生成 #7 真实 Git 历史的版本化快照。

```text
snapshots/
├── C0/  # 基线：main.o 声明 main.c config.h，clean build 输出 10
├── C1/  # 新增 feature.h 但漏写声明依赖，clean build 输出 12
└── C2/  # 源码同 C1，只改 CFLAGS 为 -O0 -DMODE=7
```

每个快照只保存源码、Makefile 和简要说明。真实 Git 仓库、`.git/` 目录、编译产物和原始命令输出保存在 `work/e3/`。
