# E11–E12 A11 backlog

本清单只覆盖 A11 可独立完成的工作；B11 的实现和 A11/B11 实际联调不在本阶段代办。

## 组长：公共框架与 E11-A

- 接入 run_e11e12.py、E11 环境和 Docker CLI/buildx 固定版本。
- 维护 E11–E12 编排契约及 E2 字段映射，保留 job_id、trace_id、commit、artifact SHA 和幂等规则。
- 提供 E11-A 全量→增量流程、异步服务入口、路径边界和重启/冲突错误处理。
- 配置只运行 A11 E11-A 的 CI 门禁；不将 B11 轨道或跨组联调伪装成 A11 个人结果。
- 汇总组员证据、审核 PR、启动服务器服务并和 B11 完成最终联调。

## 成员 231880027

- 在个人分支完成 E11-A 自主变化测试：body/include/declaration/flags/header 至少一项，记录复用与刷新目标。
- 验证错误 commit 返回 STALE_REPORT，保存实际报告、命令和证据摘要。

## 成员 241880411

- 在个人分支完成 E11-A 独立验证：BuildChecker 图与 EChecker 增量投影一致、产物 SHA/commit 元数据完整。
- 补充契约/API 拒绝测试或真实项目适配边界，记录不支持项目和失败日志。

## 暂不在本组 Issue 中实施

- B11 的 DRAFT→MDFixer 生产实现。
- A11/B11 的真实服务器联调；由组长在双方 E11 轨道就绪后启动并记录
