# 缺陷 Issue 与修复 PR 模板

## Issue

- 用例编号与发现方：
- 输入仓库及完整 SHA：
- 预期 / 实际：
- 失败阶段、错误码和原始日志路径：
- 严重度（阻断 / 非阻断）与理由：
- 最小复现步骤：
- 是否影响其他任务或原仓库：

## PR

- 关联 Issue：
- 修改文件与原因：
- 失败前证据 / 修复后同一测试证据：
- 新增或修改的回归测试：
- 原始仓库修复前后 SHA 核对：
- CI 门禁链接与审查人：
- 剩余风险：

## #49 E14 四服务未接入 B11 cJSON 配对项目 profile

- 发现方：A11 组长收尾检查；关联 PR：#50，源分支 fix/49-e14-cjson-profile，目标为 E13/E14 集成分支；尚未合并。
- 输入：B11 cJSON base cf0d87a095becada87336ed786f11070e9a037b5、target f0c8fa4f812abe50964956cd0580ab963430ba35。
- 预期 / 实际：E14 四角色应复用已有 cJSON profile；原 orchestrate.py 只接受 main.c/helper.c/config.h，故 cJSON 项目在快照阶段被拒绝。
- 严重度：阻断 B11 cJSON 的 E14 四服务验收；不影响 E11/E12 单容器 cJSON 消费。
- 修复范围：四角色请求显式携带 project_profile，BuildChecker/EChecker/MDFixer 复用已有 cJSON profile；保留严格文件范围、候选字节和 job/trace/哈希绑定。
- 补充修复：服务独立启动时显式导入 e11e12 中的 cJSON 适配器；MDFixer 使用对应 profile 的 validate；仅在隔离 target 快照注入实验所有的 Dockerfile.broken 并保存候选/原件哈希，不覆盖上游文件。修复报告拒绝跨 profile 消费。
- 修复前证据：work/e14-issue49-before-lg62r3jh/run/result.json，状态 FAILED，错误 Unsupported teaching project profile。
- 验收：同一 B11 target 云端四服务五阶段、超时/恢复、逐文件哈希已通过；详细前后证据见 docs/evidence/e13-e14/E14-cJSON-issue49.md。Issue #49 待修复 PR 经审查合并后关闭，不提前标记已合并或最终 RC 通过。
- 本地验证（2026-11-18，America/Los_Angeles）：E13/E14 34 项、旧 E11/E12 68 项通过，含真实 GCC/Make/strace 的全量→增量→修复→复检、独立导入、跨 profile 拒绝和输入边界。修复源码 b5f66f3 的全部 CI 已通过；后续文档提交检查仍以新提交实际 CI 为准。
