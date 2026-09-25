# EChecker C0/C1/C2 Command Evidence

- 关联 Issue：#7
- 分支：`test/7-c0-c1-c2-baseline`
- 运行目录：`work/e3/20260924T020000Z-issue-7-echecker-history/`
- 真实仓库：`work/e3/20260924T020000Z-issue-7-echecker-history/repo/`
- 环境清单：`docs/evidence/e3/environment/local-2026-09-24-ubuntu22-gcc11.json`
- 原始日志：`work/e3/20260924T020000Z-issue-7-echecker-history/verification.log`
- 结构化原始结果：`work/e3/20260924T020000Z-issue-7-echecker-history/verification_summary.json`

## Linux 复现工具版本

```text
git version 2.34.1
GNU Make 4.3
gcc (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0
Python 3.10.12
strace -- version 5.16
```

本次证据在 Ubuntu 22.04 风格的 Linux 环境中复现，配置记为 `cfg-linux-ubuntu22-gcc11-o0-v1`。

## 生成命令

```bash
python3 fixtures/e3/echecker-history/create_history.py
```

退出码：0。

生成的真实 SHA：

| 标签 | SHA |
| --- | --- |
| C0 | `8dfd90625e9d6f4598649ac3c956bbe46941e393` |
| C1 | `72092998daefc643163073b7203ddda847ce130e` |
| C2 | `0188a10285501024a25e4fa6a1cae9dec32e3ead` |

## 关键验证步骤

| 步骤 | 命令 | 退出码 | 关键输出 |
| --- | --- | ---: | --- |
| C0 checkout | `git -c advice.detachedHead=false checkout C0` | 0 | `HEAD is now at 8dfd906 C0 baseline declared dependencies` |
| C0 clean | `make clean` | 0 | `rm -f app.exe main.o` |
| C0 build | `make` | 0 | `gcc -O0 -c main.c -o main.o` |
| C0 run | `app.exe` | 0 | `10` |
| C1 checkout | `git -c advice.detachedHead=false checkout C1` | 0 | `HEAD is now at 7209299 C1 add missing feature dependency` |
| C1 clean | `make clean` | 0 | `rm -f app.exe main.o` |
| C1 build | `make` | 0 | `gcc -O0 -c main.c -o main.o` |
| C1 run | `app.exe` | 0 | `12` |
| C2 checkout | `git -c advice.detachedHead=false checkout C2` | 0 | `HEAD is now at 0188a10 C2 change compile flags only` |
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
