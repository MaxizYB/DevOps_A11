# EChecker 增量检测交接说明

本目录是 A11 组 EChecker 模块的工作边界。EChecker 负责基于历史实际依赖图比较跨提交变化，输出当前提交的增量依赖错误和可继续传递的更新后依赖图。

本说明对应 E2 `echecker` 任务，用于补充 `INCREMENTAL_CHECK` 的模块专有输入、输出、基线校验和交接前提。生产服务、HTTP API 和最终共享 Schema 不在本任务范围内。

## 目标

EChecker 在 E2 阶段需要说明三件事：

1. 增量检测任务需要哪些最小输入。
2. 历史 baseline 如何与 `base_commit`、当前提交和构建配置保持一致。
3. 输出如何表达当前发现、新增发现、已消除发现，并交给后续提交继续使用。

## 最小输入

`INCREMENTAL_CHECK` 创建请求应包含公共任务字段：

- `schema_version`
- `trace_id`
- `job_type`
- `idempotency_key`
- `input`

`input` 中的 EChecker 专有字段至少包括：

| 字段 | 说明 |
| --- | --- |
| `base_commit` | 历史基线提交 C0 的完整 SHA。 |
| `repository.url` | 被检测仓库地址。 |
| `repository.commit` | 当前提交 C1 的完整 SHA。 |
| `baseline.actual_graph_uri` | BuildChecker 在 C0 上生成的实际依赖图 URI。 |
| `baseline.commit` | baseline 图所属提交，必须等于 `base_commit`。 |
| `baseline.configuration_id` | baseline 图所属构建配置。 |
| `environment.image_uri` | 本次检测使用的构建环境镜像 URI。 |
| `environment.configuration_id` | 本次检测使用的构建配置。 |
| `build_command` | 在当前提交上执行的构建命令。 |
| `timeout_seconds` | 本次任务允许的最长执行时间。 |

Issue #3 中提到的 `project_root` 仍是待决项：当前 E2 契约的 EChecker 输入尚未包含该字段。如果后续实现确实需要项目根目录，应在契约 Issue 中提出字段变更，并同步更新 Schema、样例和验证脚本。

## 基线校验

创建 `INCREMENTAL_CHECK` 任务前必须完成以下校验：

- `baseline` 字段必须存在。
- `baseline.actual_graph_uri` 必须可读取。
- `baseline.commit` 必须等于 `base_commit`。
- `baseline.configuration_id` 必须等于 `environment.configuration_id`。
- baseline 图必须来自指定 `base_commit`，不能使用当前提交或其他提交的图冒充。

校验失败时不应进入增量分析：

| 场景 | 预期行为 |
| --- | --- |
| 缺少 `baseline` | HTTP 400，不创建 Job，错误码 `REQUEST_1001`。 |
| baseline commit 与 `base_commit` 不匹配 | HTTP 400，不创建 Job，错误码 `REQUEST_1002`。 |
| baseline configuration 与当前环境配置不匹配 | HTTP 400，不创建 Job，错误码 `REQUEST_1002`。 |
| baseline artifact URI 不可读取或元数据不匹配 | Job `FAILED`，错误码 `ARTIFACT_2001`。 |

## 输出

EChecker 成功完成时，任务状态为 `SUCCEEDED`。检测到 MD/RD 属于正常分析结果，不写入 `job.error`。

`output.artifacts` 至少包含：

- 更新后的 `ACTUAL_GRAPH`：对应当前提交 `repository.commit`，供后续提交继续作为 baseline 使用。
- `ERROR_REPORT`：记录当前提交上的依赖错误及相对于 baseline 的变化。

输出还应能表达：

| 字段或概念 | 含义 |
| --- | --- |
| `current_findings` | 当前提交仍然存在的发现数量。 |
| `new_findings` | 相比 baseline 新增的发现数量。 |
| `resolved_findings` | baseline 中存在但当前提交已消除的发现数量。 |

错误报告中的每条发现应至少能追溯到 target、dependency、commit、位置和证据。报告中的 commit 应指向当前提交；如果引用 baseline 发现，也必须能区分其来源提交。

## 产物交接

所有大文件通过 `artifact://` URI 交接，不直接嵌入任务响应。每个产物必须记录：

- `artifact_id`
- `type`
- `uri`
- `media_type`
- `producer_job_id`
- `commit`
- `configuration_id`

EChecker 消费 BuildChecker 的历史 `ACTUAL_GRAPH`，并产出新的 `ACTUAL_GRAPH` 和 `ERROR_REPORT`。下游 MDFixer 只消费 MD 类型报告；RD 类型发现用于报告和人工判断，不直接进入 MDFixer 修复流程。

## 依赖和待决问题

- 依赖 BuildChecker 在 `base_commit` 上产出的历史实际依赖图。
- 依赖 DRAFT 或 B 组提供可读取的构建环境镜像产物。
- 依赖共享契约定义的 Job 模型、错误码、artifact URI 和版本策略。
- 待确认 B 组是否能按 `artifact://` URI 读取 A 组产物。
- 待确认 EChecker 是否需要把 `project_root` 纳入正式输入。
- 待确认真实 C0/C1/C2 历史样例和人工 Oracle，E3 阶段会在 `fixtures/e3/echecker-history/` 与 `docs/evidence/e3/echecker/` 中补充。

## 现有样例和验证

当前仓库已有以下 EChecker 契约样例：

- `contracts/samples/requests/incremental-check-create.json`
- `contracts/samples/responses/incremental-check-succeeded.json`
- `contracts/samples/invalid/incremental-check-missing-baseline.json`
- `contracts/samples/invalid/incremental-check-mismatched-baseline.json`

可使用以下命令验证契约样例：

```bash
python3 scripts/validate_contract.py
```

已记录的 E2 契约校验结果显示：

- 缺少 incremental baseline 映射到 HTTP 400 / `REQUEST_1001`。
- baseline commit 不等于 `base_commit` 映射到 HTTP 400 / `REQUEST_1002`。
- 有效 `INCREMENTAL_CHECK` 样例可表达更新后的实际依赖图和错误变化报告。
