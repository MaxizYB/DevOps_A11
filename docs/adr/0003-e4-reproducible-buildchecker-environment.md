# ADR-0003：E4 使用可重复的 BuildChecker 工程环境骨架

- 状态：Accepted
- 日期：2026-09-29
- 关联 Issue：#14

## 决策

- A11 先在未取得教师实验包时建立 E4 A 组骨架；实验包取得后，对照 `E4实验包/A-buildchecker/` 并吸收兼容的工程改进。
- E2 的 `contracts/`、E3 的 `fixtures/e3/` 和历史证据保持原路径不变；E4 只新增容器、编排、锁文件、CLI、测试和运行脚本。
- BuildChecker 的 E4 CLI 只提供 `version` 和基于 E3 MD/RD fixture 的 `smoke`；实际依赖图分析留到后续 MVP，不把冒烟结果写成检测器结果。
- 每次 `make` 子命令和 `make all` 都创建新的 `work/<UTC timestamp>/` 证据目录，原始日志默认不进入 Git。
- 基础镜像按 E4 手册指定的不可变 digest 引用；Python 开发依赖使用带哈希的锁文件。

## 验收边界

本地没有 Docker daemon 时只能验证 Python 单测、脚本静态检查和契约回归；镜像构建、容器单测、strace 冒烟、镜像扫描及两名组员 ECS 重跑必须在有 Docker 的服务器上完成并记录。
