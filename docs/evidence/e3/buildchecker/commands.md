# 本次实际命令

工作目录：`work/e3/20260924T021234Z-issue-6-md-rd/project/`。从 `fixtures/e3/md-rd/` 复制得到；原始日志和 `summary.json` 在其父目录。表中输出为 stdout，所有命令的 stderr 均为空。

## 1. 初始构建

原始日志：`work/e3/20260924T021234Z-issue-6-md-rd/01-initial-build.log`

| 命令 | exit code | 关键 stdout |
| --- | ---: | --- |
| `make clean` | 0 | `rm -f app main.o` |
| `make` | 0 | `cc -c main.c -o main.o`；`cc main.o -o app` |
| `./app` | 0 | `1` |

## 2. MD 增量构建

原始日志：`work/e3/20260924T021234Z-issue-6-md-rd/02-md-incremental.log`

| 命令 | exit code | 关键 stdout |
| --- | ---: | --- |
| `sleep 2` | 0 | 无 |
| `python3 -c 'from pathlib import Path; Path("config.h").write_text("#define VALUE 2\n")'` | 0 | 无 |
| `make` | 0 | ``make: `app' is up to date.`` |
| `./app` | 0 | `1` |

## 3. clean build 对照

原始日志：`work/e3/20260924T021234Z-issue-6-md-rd/03-md-clean-build.log`

| 命令 | exit code | 关键 stdout |
| --- | ---: | --- |
| `make clean` | 0 | `rm -f app main.o` |
| `make` | 0 | `cc -c main.c -o main.o`；`cc main.o -o app` |
| `./app` | 0 | `2` |

## 4. RD 重编译

原始日志：`work/e3/20260924T021234Z-issue-6-md-rd/04-rd-rebuild.log`

| 命令 | exit code | 关键 stdout |
| --- | ---: | --- |
| `sleep 2` | 0 | 无 |
| `python3 -c 'from pathlib import Path; Path("unused.h").write_text("/* Changed unused comment for RD test. */\n")'` | 0 | 无 |
| `make` | 0 | `cc -c main.c -o main.o`；`cc main.o -o app` |
| `./app` | 0 | `2` |
