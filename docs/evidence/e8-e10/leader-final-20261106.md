# E8–E10 组长收尾证据索引

日期：2026-11-06；学号：241880439；Issue：#29。

## 版本与环境

- 组长实验源码：d8062baac0e5086671a962021a63eaf6e31bbcc0。
- 实验父提交：成员 PR 合并后的 7c145d6b6a83b0e98f29099fffac6cbfadcbc1dc。
- 服务器仓库：/root/241880439/DevOps_A11-e8-e10。
- 原始证据：work/leader-final-20261106/；本地最终归档的 evidence/leader/。
- 镜像：course-e8e10:241880439，ID sha256:47e2ec8d350d9a250cc737a6d6f38e94d90cd66d92a8a3e94f8a19b90d3dc715。
- 实际资源：约 3.54 GiB 可见内存、约 66 GiB 可用磁盘；内存低于手册建议值，按确认方案串行运行。

## 通过结果

| 项目 | 证据 | 结果 |
|---|---|---|
| 容器测试 | initial-unit-tests.log | 25 tests，全部 OK，退出 0 |
| E8 | experiments/e8/ | gate、增量/全量、动态投影均通过 |
| E9 | experiments/e9/ | C0–C3 及个人目标迁移均通过 |
| E10 | experiments/e10/ | 30 行、60 份原始 JSON、动态交叉核对通过 |
| E8 自主 | experiments/e8-personal/ | 嵌套叶头文件新增，完整预期通过 |
| E9 自主 | experiments/e9-personal/ | include 目标迁移，完整预期通过 |
| E10 自主 | experiments/e10-personal/ | 宏开启/恢复各 5 次，10 行通过 |

总运行结果见 experiments/run-result.json，六个阶段均列为 passed；逐文件 SHA256 见 experiments/sha256-manifest.json。原始证据含样例内部 Git 历史、输入快照、命令、日志、BuildChecker trace、Make 数据库、报告和结果 CSV。

## GitHub 收尾记录

成员 PR #33、#34 已合并到 main；其 JSON、Issue #30/#31、保护配置前快照和下载的成员证据位于最终归档 delivery/github/。组长个人 PR 的真实号码、head SHA、CI run、评论/自审例外、合并 SHA 和保护配置恢复结果在归档生成后写入 delivery/github/leader-pr.json、leader-review.json、protection-after.json。

本次允许组长自己审核自己的收尾 PR，是用户明确授权的例外；记录为自审，不伪造非作者批准。必需 CI 检查保持开启，保护配置在合并后恢复为一名批准评审、strict 和最后推送审批。
