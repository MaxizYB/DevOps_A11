# C0 Baseline

C0 是 EChecker 的历史图基线提交。

- `main.o` 声明依赖：`main.c config.h`
- `main.c` 实际包含：`config.h`
- clean build 后运行 `app.exe` 输出：`10`
- 人工 Oracle：本例范围内声明依赖和实际依赖一致。
