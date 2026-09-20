# E2 契约校验记录

- 日期：2026-09-21
- 契约版本：1.0.0
- 关联 Issue：#1
- 分支：`docs/1-e2-contracts`

## 校验命令

```bash
find contracts/schemas contracts/samples -type f -name '*.json' -print0 | xargs -0 -n1 jq empty
python3 scripts/validate_contract.py
python3 -m py_compile scripts/validate_contract.py
git diff --check
```

## 实际结果

```text
All contract JSON files parse successfully.
PASS schema: contracts/schemas/e2-create-request.schema.json
PASS schema: contracts/schemas/e2-job-response.schema.json
PASS exchange: draft
PASS exchange: full-check
PASS exchange: incremental-check
PASS exchange: repair
PASS failed job: full-check-failed.json -> FAILED / ANALYSIS_5001
PASS rejection: unknown-job-type.json -> HTTP 400 / REQUEST_1001
PASS rejection: incremental-check-missing-baseline.json -> HTTP 400 / REQUEST_1001
PASS rejection: incremental-check-mismatched-baseline.json -> HTTP 400 / REQUEST_1002
PASS contract validation: 2 schemas, 4 exchanges, 3 rejections
```

## 结果解释

- 四类创建请求和成功 Job 响应均通过结构及跨字段校验；BuildChecker 失败样例验证了 `FAILED`、空 `output` 和 `ANALYSIS_5001` 的互斥规则。
- 未知 `job_type` 和缺少增量 `baseline` 直接映射到 HTTP 400 / `REQUEST_1001`。
- 增量 baseline 的 commit 不等于 `base_commit` 时映射到 HTTP 400 / `REQUEST_1002`。
- 这是契约样例和字段规则的验证，不是四个服务的运行测试；服务实现由 #2、#3 及 B11 对应任务负责。
