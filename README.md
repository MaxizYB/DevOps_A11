# DevOps_A11

A11 组 DevOps 教学实验仓库。当前从 E2（需求与接口契约）开始，A 组负责全量依赖检测与跨提交增量检测，并与同号 B 组约定后续交接方式。

## E2 分工

- 组长：建立契约、维护仓库框架、合并 PR/MR、跟踪进度与个人贡献。
- BuildChecker 负责人：完成固定提交与固定构建配置下的全量依赖检测工作。
- EChecker 负责人：完成基于历史基线的跨提交增量检测工作。

本次初始框架只建立协作边界和目录，不包含业务实现、Schema、JSON 契约或接口样例。契约内容由组长在对应 Issue 中单独提交。

## 目录结构

```text
.github/                 GitHub Issue 与 PR 模板
contracts/               组长维护的共享契约，当前保留为空
docs/adr/                架构决策记录
docs/evidence/           可追溯的设计与验证证据
services/buildchecker/   BuildChecker 的实现与测试边界
services/echecker/       EChecker 的实现与测试边界
```

## 协作入口

初始框架推送后，所有任务发布、开发、修改和合并均从 GitHub Issue 开始。详细规则见 [A11 组协作规范](docs/A11组协作规范.md)。

每位成员的基本流程如下：

1. 认领或被指派一个可验收的 Issue。
2. 从最新 `main` 创建带 Issue 编号的分支。
3. 在分支上提交实现和验证证据。
4. 创建关联该 Issue 的 PR/MR，评审通过后由组长合并。
