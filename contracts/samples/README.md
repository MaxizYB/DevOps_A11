# E2 契约样例

`requests/` 包含四类服务的有效创建请求，`responses/` 包含对应的成功 Job 响应和执行失败 Job 响应，`invalid/` 包含必须在创建阶段拒绝的请求。

这些样例使用虚构的完整 40 位 commit SHA 和 `artifact://` URI，仅用于验证字段、版本、状态和交接规则；它们不是可运行项目的构建证据。

运行以下命令检查样例：

```bash
python3 scripts/validate_contract.py
```

校验预期：

| 样例 | 预期 |
| --- | --- |
| `requests/*.json` 与 `responses/*.json` | 通过 |
| `responses/full-check-failed.json` | `FAILED`、`output: null`、`ANALYSIS_5001` |
| `invalid/unknown-job-type.json` | HTTP 400 / `REQUEST_1001` |
| `invalid/incremental-check-missing-baseline.json` | HTTP 400 / `REQUEST_1001` |
| `invalid/incremental-check-mismatched-baseline.json` | HTTP 400 / `REQUEST_1002` |
