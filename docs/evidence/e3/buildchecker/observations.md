# 本次观察

运行目录：`work/e3/20260924T021234Z-issue-6-md-rd/`。依据为该目录中的四份原始日志和 `summary.json`。

- 初始构建成功，`./app` 输出 `1`。
- MD：将运行副本的 `config.h` 改为 `VALUE 2` 后，普通 `make` 报告 `app` 已是最新，未出现编译命令；`main.o` 的修改时间未变化，`./app` 仍输出 `1`。clean build 重新编译后输出 `2`。
- RD：只改运行副本的 `unused.h` 注释后，`make` 输出 `cc -c main.c -o main.o`，`main.o` 的修改时间更新；`./app` 仍输出 `2`。

结果与 `MANUAL_ORACLE` 的两条判断一致。当前未运行 BuildChecker。
