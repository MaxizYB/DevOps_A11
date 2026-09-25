# E2 EChecker 增量检测交接证据

- 阶段：E2
- 模块：echecker
- 关联 Issue：#3
- 分支：`docs/3-echecker-incremental-check`
- 契约版本：1.0.0

## 阅读来源

- `contracts/e2-interface-contract.md`：E2 共享接口契约，尤其是公共 Job 模型、artifact URI、错误码和 EChecker 接口。
- `contracts/samples/requests/incremental-check-create.json`：有效增量检测创建请求样例。
- `contracts/samples/responses/incremental-check-succeeded.json`：有效增量检测成功响应样例。
- `contracts/samples/invalid/incremental-check-missing-baseline.json`：缺少 baseline 的无效请求。
- `contracts/samples/invalid/incremental-check-mismatched-baseline.json`：baseline commit 与 `base_commit` 不匹配的无效请求。
- `docs/adr/0001-e2-async-job-artifact-contract.md`：异步 Job、artifact URI 和 EChecker baseline 校验的设计决策。
- `services/echecker/README.md`：EChecker 模块边界、输入输出和待决问题说明。

## 最小输入整理

EChecker 的 `INCREMENTAL_CHECK` 请求需要公共字段 `schema_version`、`trace_id`、`job_type`、`idempotency_key` 和 `input`。其中 `input` 的最小模块输入为：

| 字段 | 示例来源 | 作用 |
| --- | --- | --- |
| `base_commit` | `0123456789abcdef0123456789abcdef01234567` | 指定历史基线提交 C0。 |
| `repository.url` | `https://github.com/example/make-sample.git` | 指定被检测仓库。 |
| `repository.commit` | `fedcba9876543210fedcba9876543210fedcba98` | 指定当前提交 C1。 |
| `baseline.actual_graph_uri` | `artifact://job-FULL_CHECK-C0-001/graph-001/actual.json` | 指向 BuildChecker 在 C0 上产生的历史实际依赖图。 |
| `baseline.commit` | `0123456789abcdef0123456789abcdef01234567` | 标记 baseline 图所属提交，必须等于 `base_commit`。 |
| `baseline.configuration_id` | `cfg-ubuntu22-gcc12-release-v1` | 标记 baseline 图所属构建配置。 |
| `environment.image_uri` | `artifact://job-DRAFT-001/image-001/image.tar` | 指向本次检测使用的构建环境镜像。 |
| `environment.configuration_id` | `cfg-ubuntu22-gcc12-release-v1` | 标记当前任务使用的构建配置，必须与 baseline 配置一致。 |
| `build_command` | `make` | 指定当前提交上的构建命令。 |
| `timeout_seconds` | `1800` | 指定任务超时时间。 |

Issue #3 中提到的 `project_root` 尚未进入当前 E2 契约。若后续实现需要该字段，应在契约 Issue 中作为字段变更讨论，并同步更新 Schema、样例和校验脚本。

## 有效样例解释

`contracts/samples/requests/incremental-check-create.json` 表达的是从 C0 到 C1 的增量检测：

- `base_commit` 是 C0。
- `repository.commit` 是当前提交 C1。
- `baseline.actual_graph_uri` 指向由 `job-FULL_CHECK-C0-001` 产生的 C0 实际依赖图。
- `baseline.commit` 等于 `base_commit`，说明历史图确实来自 C0。
- `baseline.configuration_id` 等于 `environment.configuration_id`，说明两次比较在同一构建配置下进行。

`contracts/samples/responses/incremental-check-succeeded.json` 表达成功完成后的交接结果：

- `status` 为 `SUCCEEDED`，表示分析正常完成。
- `output.artifacts` 包含当前提交 C1 的更新后 `ACTUAL_GRAPH`，可作为后续 C1 到 C2 检测的 baseline。
- `output.artifacts` 包含当前提交 C1 的 `ERROR_REPORT`，用于下游解释当前发现和变化。
- `current_findings`、`new_findings`、`resolved_findings` 分别说明当前发现、新增发现和已消除发现。
- `error` 为 `null`，因为检测到依赖错误属于正常分析结果，不是工具执行失败。

## 无效基线场景

| 样例 | 拒绝原因 | 预期行为 |
| --- | --- | --- |
| `contracts/samples/invalid/incremental-check-missing-baseline.json` | 请求缺少 `baseline` 字段，无法确认历史图来源。 | HTTP 400，不创建 Job，错误码 `REQUEST_1001`。 |
| `contracts/samples/invalid/incremental-check-mismatched-baseline.json` | `baseline.commit` 使用当前提交 C1，不等于 `base_commit` C0。 | HTTP 400，不创建 Job，错误码 `REQUEST_1002`。 |

配置不匹配也应按同类前置条件错误处理：若 `baseline.configuration_id` 不等于 `environment.configuration_id`，请求应被拒绝为 HTTP 400 / `REQUEST_1002`，避免跨配置比较造成误报。

## 依赖和待决问题

- 依赖 BuildChecker 先在 `base_commit` 上产生可读取的历史 `ACTUAL_GRAPH`。
- 依赖 DRAFT 或 B 组产出可读取的构建环境镜像 URI。
- 依赖共享契约继续维护统一 Job 模型、错误码、artifact URI 和版本策略。
- B 组是否能读取 A 组 `artifact://` URI，需要在配对组互读记录或关联 Issue 中确认。
- 真实 C0/C1/C2 历史、人工 Oracle 和命令行为证据将在 E3 的 `fixtures/e3/echecker-history/` 与 `docs/evidence/e3/echecker/` 中补充。

## 验证方法

运行以下命令验证当前 E2 契约样例和跨字段规则：

```powershell
python3 scripts\validate_contract.py
```

本次验证结果：

```text
PASS schema: contracts\schemas\e2-create-request.schema.json
PASS schema: contracts\schemas\e2-job-response.schema.json
PASS exchange: draft
PASS exchange: full-check
PASS exchange: incremental-check
PASS exchange: repair
PASS failed job: full-check-failed.json -> FAILED / ANALYSIS_5001
PASS rejection: unknown-job-type.json -> HTTP 400 / REQUEST_1001
PASS rejection: incremental-check-missing-baseline.json -> HTTP 400 / REQUEST_1001
PASS rejection: incremental-check-mismatched-baseline.json -> HTTP 400 / REQUEST_1002
PASS contract validation: 2 schemas, 4 exchanges, 1 failed job, 3 rejections
```

## 当前结论

EChecker 的 E2 交接材料已经能支持组长补全 `INCREMENTAL_CHECK` 的输入、输出、产物和失败行为：有效样例明确区分 C0、C1 和 baseline 图所属提交；无效样例给出可检查的拒绝行为；待决问题也已明确标出，避免把未确认字段或 B 组读取能力写成已完成事实。

## 个人贡献记录

- 整理 EChecker 增量检测最小输入、输出语义、基线校验和待决问题。
- 编写 `services/echecker/README.md` 的模块交接说明。
- 编写本文档，记录阅读来源、样例解释、无效场景和验证结果。
