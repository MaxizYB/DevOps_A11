# EChecker C0/C1/C2 Command Evidence

- 关联 Issue：#7
- 分支：`test/7-c0-c1-c2-baseline`
- 收尾运行目录：`work/e3/20260925T043526Z-issue-7-echecker-history/`
- 收尾真实仓库：`work/e3/20260925T043526Z-issue-7-echecker-history/repo/`
- 环境清单：`docs/evidence/e3/environment/local-2026-09-25-gcc16.json`
- 原始日志：`work/e3/20260925T043526Z-issue-7-echecker-history/verification.log`
- 结构化原始结果：`work/e3/20260925T043526Z-issue-7-echecker-history/verification_summary.json`

## Linux 复现工具版本

```text
git version 2.55.0
GNU Make 4.4.1
cc (GCC) 16.2.1 20260810
Python 3.14.7
strace -- version 7.0
```

本次收尾证据在 Linux x86_64 环境中复现，配置记为 `cfg-linux-lts-gcc16-o0-v2`。成员原始 Ubuntu/GCC 11 记录仍可从 PR #12 的提交历史追溯。

## 生成命令

```bash
python3 fixtures/e3/echecker-history/create_history.py
```

退出码：0。

生成的真实 SHA：

| 标签 | SHA |
| --- | --- |
| C0 | `242df6090df69b2c1e61ac422030ae901eac715c` |
| C1 | `7f5e4341e938e890fa71b6d219ef51437d5cea1f` |
| C2 | `fb03409e287fde67af2f707e689cf1c38a36ff51` |

## 关键验证步骤

| 步骤 | 命令 | 退出码 | 关键输出 |
| --- | --- | ---: | --- |
| C0 checkout | `git -c advice.detachedHead=false checkout C0` | 0 | `HEAD is now at 242df60 C0 baseline declared dependencies` |
| C0 clean | `make clean` | 0 | `rm -f app.exe main.o` |
| C0 build | `make` | 0 | `gcc -O0 -c main.c -o main.o` |
| C0 run | `app.exe` | 0 | `10` |
| C1 checkout | `git -c advice.detachedHead=false checkout C1` | 0 | `HEAD is now at 7f5e434 C1 add missing feature dependency` |
| C1 clean | `make clean` | 0 | `rm -f app.exe main.o` |
| C1 build | `make` | 0 | `gcc -O0 -c main.c -o main.o` |
| C1 run | `app.exe` | 0 | `12` |
| C2 checkout | `git -c advice.detachedHead=false checkout C2` | 0 | `HEAD is now at fb03409 C2 change compile flags only` |
| C2 command preview | `make -n -B main.o` | 0 | `gcc -O0 -DMODE=7 -c main.c -o main.o` |
| C2 incremental build | `make` | 0 | `make: Nothing to be done for 'all'.` |
| C2 incremental run | `app.exe` | 0 | `12` |
| C2 clean | `make clean` | 0 | `rm -f app.exe main.o` |
| C2 clean build | `make` | 0 | `gcc -O0 -DMODE=7 -c main.c -o main.o` |
| C2 clean run | `app.exe` | 0 | `19` |

## 复现顺序

1. 运行生成命令创建真实 Git 历史。
2. 在生成的 `repo/` 中按上表 checkout C0、C1、C2。
3. C1 clean build 后不要清理产物，直接 checkout C2，以保留 C1 产物进入 C2。
4. 在 C2 先运行普通增量构建，再运行 clean build，对比输出 `12` 和 `19`。
