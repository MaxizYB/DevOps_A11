# GNU Make MD/RD 样例

本样例在同一个 `main.o` 上放置一条缺失依赖和一条冗余依赖，用于核对后续 BuildChecker 的结果。人工标准答案见 `oracle.json`。

| 文件 | 用途 |
| --- | --- |
| `main.c` | 引入 `stdio.h`、`config.h`，打印 `VALUE` |
| `config.h` | 初始定义 `VALUE` 为 1 |
| `unused.h` | 编译 `main.c` 时未使用 |
| `Makefile` | 构建 `app`，故意写错 `main.o` 的依赖 |
| `oracle.json` | 人工判断的 MD/RD 标准答案 |

`main.c` 实际读取 `config.h`，但 `main.o` 的 prerequisites 只有 `main.c unused.h`。因此 `main.o -> config.h` 为 MISSING，`main.o -> unused.h` 为 REDUNDANT。

从仓库根目录创建 `work/e3/<UTC时间>-issue-6-md-rd/`，将整个 `fixtures/e3/md-rd/` 复制到其中的 `project/`，再进入 `project/` 执行。所有修改、编译产物和原始日志都留在该运行副本；不要直接修改 fixture 做实验。

```sh
run="work/e3/$(date -u +%Y%m%dT%H%M%SZ)-issue-6-md-rd"
mkdir -p "$run"
cp -R fixtures/e3/md-rd "$run/project"
cd "$run/project"
```

1. 执行 `make clean`、`make`、`./app`；程序应输出 `1`。
2. 等待至少 2 秒，只把运行副本的 `config.h` 改为 `#define VALUE 2`，再执行 `make`、`./app`；普通增量构建应跳过 `main.o`，程序仍输出 `1`。
3. 保持 `VALUE=2`，执行 `make clean`、`make`、`./app`；程序应输出 `2`。
4. 等待至少 2 秒，只修改运行副本的 `unused.h` 注释，再执行 `make`、`./app`；应看到 `main.o` 重编译，程序仍输出 `2`。

检查每条命令的退出码和构建输出；如与上述判断不符，保留真实日志并检查文件时间戳。fixture 源码提交 SHA：`ddedbb87bf980286c17ece296a8f9763841c31ea`。组长已在 Linux 独立副本完成复核，复核结果与 Oracle 一致。
