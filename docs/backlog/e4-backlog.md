# E4 Backlog

| ID | 任务 | 责任方 | 状态 |
| --- | --- | --- | --- |
| E4-01 | 建立 A 组可重复 BuildChecker 工程骨架 | A11 组长 | 进行中 |
| E4-02 | 在独立克隆中完成 `make all` 并保存成功证据 | BuildChecker 成员 | 待服务器运行 |
| E4-03 | 在第二个独立克隆中重跑并比较证据 | EChecker 成员 | 待服务器运行 |

## 共同完成条件

- 同一模板提交 SHA 可从两个独立克隆运行。
- `make all` 依次生成 `env.json`、`build.log`、`image.json`、`toolchain.lock`、`test.log`、`smoke.json` 和 `secret-scan.txt`。
- `smoke.json` 表明 `config.h` 被打开、应用输出 `1`；`make scan` 通过，假 Key 能被检出后清理。
- Docker/ECS 运行结果不得用本地 Python 单测或人工推测代替。
