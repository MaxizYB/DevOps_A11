# DevOps_A11

A11 组 DevOps 教学实验仓库。E2 的共享接口契约、E3 的可重放测试基线和 E4 的可重复 BuildChecker 工程骨架已发布。

## E2 分工

- 组长：建立契约、维护仓库框架、合并 PR/MR、跟踪进度与个人贡献。
- BuildChecker 负责人：完成固定提交与固定构建配置下的全量依赖检测工作。
- EChecker 负责人：完成基于历史基线的跨提交增量检测工作。

E2 共享契约、Schema、样例和校验脚本位于 [`contracts/`](contracts/README.md)。

## E3 分工

- 组长：[#5](https://github.com/MaxizYB/DevOps_A11/issues/5) 统一 fixture/work/evidence 布局、环境记录、复现规范与最终汇总。
- BuildChecker 负责人：[#6](https://github.com/MaxizYB/DevOps_A11/issues/6) 准备一个同时包含 MD 和 RD 的 GNU Make 基线及人工 Oracle。
- EChecker 负责人：[#7](https://github.com/MaxizYB/DevOps_A11/issues/7) 准备可重放的 C0/C1/C2 Git 历史、命令变化和增量行为证据。

E3 当前只准备基线和证据，不实现 BuildChecker 或 EChecker 的生产检测逻辑，也不接入 B11 的真实数据。

## E4 分工

- 组长：维护 E4 容器/Compose/Make 骨架，固定依赖并汇总服务器证据。
- 两名组员：各自在独立克隆中设置本地 Git 身份，运行 `make all`，保存成功的 `work/<时间>/`，并比较工具版本、测试和冒烟结论。

E4 的 CLI 只提供环境 `version` 和 E3 MD/RD 冒烟检查；BuildChecker 生产检测算法属于后续 MVP 阶段。运行入口和证据格式见 [`scripts/e4/README.md`](scripts/e4/README.md) 与 [`docs/backlog/e4-backlog.md`](docs/backlog/e4-backlog.md)。

## 目录结构

```text
.github/                 GitHub Issue 与 PR 模板
contracts/               版本化共享契约、Schema 和交换样例
docs/adr/                架构决策记录
docs/backlog/            课程阶段任务清单
docs/evidence/           可追溯的设计与验证证据
fixtures/e3/             版本控制的 E3 人工样例与历史快照
work/e3/                 本地运行副本和原始输出（默认不提交）
scripts/e3/              E3 环境采集与框架校验工具
services/buildchecker/   BuildChecker 的实现与测试边界
services/echecker/       EChecker 的实现与测试边界
Makefile                E4 一键命令入口
compose.yaml             E4 容器资源与安全限制
requirements-dev.*       E4 Python 开发依赖输入和哈希锁
scripts/e4/              E4 环境、运行编排和密钥检查
setup/                   服务器一次性初始化脚本
```

## 协作入口

初始框架推送后，所有任务发布、开发、修改和合并均从 GitHub Issue 开始。详细规则见 [A11 组协作规范](docs/A11组协作规范.md)。

每位成员的基本流程如下：

1. 认领或被指派一个可验收的 Issue。
2. 从最新 `main` 创建带 Issue 编号的分支。
3. 在分支上提交实现和验证证据。
4. 创建关联该 Issue 的 PR/MR，评审通过后由组长合并。

E3 基线的目录、证据要求和复现入口见 [`fixtures/e3/README.md`](fixtures/e3/README.md) 与 [`docs/evidence/e3/README.md`](docs/evidence/e3/README.md)。
