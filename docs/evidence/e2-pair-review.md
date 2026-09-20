# E2 配对组交接检查记录

- A 组：A11
- B 组：B11
- 契约版本：1.0.0
- 关联 Issue：#1
- 记录状态：A11 已发布，等待 B11 互读确认

## A11 已提供的交接材料

- 四类任务的创建请求和成功 Job 响应：`contracts/samples/requests/` 与 `contracts/samples/responses/`。
- `artifact://` 本地读取映射：见 `contracts/e2-interface-contract.md` 第 6 节。
- 全量检测图、错误报告和增量基线的样例：见 FULL_CHECK 与 INCREMENTAL_CHECK 样例。
- 无效输入及预期拒绝：未知 `job_type`、缺少 baseline、baseline commit 不匹配。

## B11 互读检查项

- [ ] 能解释并读取 A11 的 `ACTUAL_GRAPH` 或 `ERROR_REPORT` 产物 URI。
- [ ] 能解释 EChecker baseline 的 `base_commit`、`commit` 和 `configuration_id` 一致性要求。
- [ ] 能说明 MDFixer 仅消费 `MISSING` 报告，不消费 `REDUNDANT` 报告。
- [ ] 记录确认、问题或需要变更的字段，并关联到 #1 或后续 Issue。

## 当前结论

A11 已完成契约包、样例和自校验发布。B11 的实际互读确认尚未在仓库或 GitHub Issue 中记录；在确认前，不将其表述为已完成验收。
