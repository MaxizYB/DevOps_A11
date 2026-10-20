# 组长 E5–E7 云端运行记录

本记录对应 #20 阶段 A 的公共基础分支 `42f9a73`，在本组 ECS 的独立克隆 `/root/241880439/DevOps_A11-e5-e7-20261020` 中完成。原始输出已下载到本地忽略目录 `work/e5-e7-20261020/remote/`；服务器原始目录仍保留。

## 环境与构建

- ECS：Ubuntu 22.04.5 LTS，x86_64，2 CPU，3.5 GiB 可见内存，65.8 GiB 可用磁盘。
- Git 身份：`241880439` / `241880439@smail.nju.edu.cn`；doctor `problems=[]`，仅低于推荐资源的 warnings。
- 工具：Docker 29.8.1、Compose 5.5.1、Buildx 0.37.1、Git 2.34.1、GNU Make 4.3、Python 3.10.12；镜像内 Python 3.13.14、pytest 8.4.2。
- 构建命令：`python3 scripts/lab_cloud.py build --out work/e5-e7-20261020/build-01 --build-timeout 1200`。
- 镜像：`course1020-buildchecker:241880439`，镜像 ID / digest：`sha256:3909ce91907e5e851d7af4844b32938ab3a71a788396964253dad63748c10876`；RootFS 共 15 层。
- 容器服务测试：15 passed in 0.07s。构建和单测原始输出见 `work/e5-e7-20261020/remote/build-01/`。

## E5 原始复现

命令：

```sh
python3 scripts/lab_cloud.py e5 --out work/e5-e7-20261020/e5-01
```

结果退出码为 0，程序输出为 `1`。真实原始证据中：

- `remote/e5-01/evidence/trace/t.16:580`：成功打开 `config.h`；
- `remote/e5-01/evidence/make-db.txt:1049`：`main.o: main.c unused.h`；
- `remote/e5-01/evidence/trace/t.16` 的 `execve` 显示该进程为编译器派生的 `cc1`；其父级编译任务与写出 `main.o` 的 `as` 进程归属于同一次 Make recipe。

因此本次样例的人工结论为：`main.o` 实际读取 `config.h` 但未声明，得到 MD；Make 声明 `unused.h` 但构建未读取，得到 RD。E5 使用 `strace -ff` 记录文件调用，和论文原型的 `ptrace` 以及大规模开源项目集合存在方法范围差异。

## E6 原始与修复

```sh
python3 scripts/lab_cloud.py e6 --out work/e5-e7-20261020/e6-before-01
python3 scripts/lab_cloud.py e6 --fixed --out work/e5-e7-20261020/e6-after-01
python3 scripts/verify_e6_evidence.py \
  --before work/e5-e7-20261020/e6-before-01/evidence/findings.json \
  --after work/e5-e7-20261020/e6-after-01/evidence/findings.json
```

校验结果 `passed=true`：

- 原始 `findings.json`：`status=SUCCEEDED`、clean/build 均为 0，精确两条 `MISSING(main.o, config.h)`、`REDUNDANT(main.o, unused.h)`；由于启用 `--fail-on-findings`，命令退出码为 1。
- 修复副本：`status=SUCCEEDED`、退出码为 0、`findings=[]`。
- 输入哈希集合相同，唯一变化为 `Makefile`；原始和修复 trace_id 分别为 `e6-68a11a5925f5491e9230857dee18cd67`、`e6-699a3b9e76af488f9e9b90150dff9d24`。

## E7 八项门禁

命令：

```sh
python3 scripts/lab_cloud.py gate --out work/e5-e7-20261020/e7-01
```

`gate-result.json` 的整体 `passed=true`，8/8 项通过，`results.csv` 逐项对应：

| 场景 | 工具退出码 | 状态 | 判定 |
| --- | ---: | --- | --- |
| unit-tests | 0 | — | PASS |
| original-1 / 2 / 3 | 1 | SUCCEEDED | 每次精确两条 MD/RD，PASS |
| fixed | 0 | SUCCEEDED | findings 为空，PASS |
| build-failed | 1 | FAILED | 真实构建失败被识别，PASS |
| unsupported | 1 | FAILED | 多输出返回 `UNSUPPORTED`，PASS |
| timeout | 1 | TIMED_OUT | 超时返回 `TIMEOUT` 并清理容器，PASS |

三次原始 trace_id 为 `e6-7dc507ab98404adba0ef40c28e29d177`、`e6-ce40e325b06d4a33b68d32547ee80112`、`e6-0f6f91f14ced43bdb913d92064400537`。本次云端工作区和镜像/历史密钥扫描均通过。

## 证据边界

这些是 A11 组长在一台 ECS 上、独立克隆和独立输出目录完成的教学样例证据。它们证明当前小型 GNU Make 教学 profile 的 E5–E7 流程可重放；不声称已经完成论文完整 benchmark、EChecker（E8–E10）、B 轨道或 REST 服务。
