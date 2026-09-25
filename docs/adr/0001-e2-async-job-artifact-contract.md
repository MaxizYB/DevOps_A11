# ADR-0001：E2 使用异步 Job 和 Artifact URI 交接

- 状态：Accepted
- 日期：2026-09-20
- 关联 Issue：#1

## 背景

BuildChecker、EChecker、DRAFT 和 MDFixer 都可能运行超过一次 HTTP 请求的生命周期，并且会产生依赖图、日志、镜像和补丁等大文件。A11 与 B11 需要在固定源码提交和固定构建配置下交接这些结果，同时区分“检测到 MD/RD”与“工具执行失败”。

## 决策

- 四类服务采用统一的、带 `schema_version` 的异步 Job 模型；创建接口返回 HTTP 202 和服务端生成的 `job_id`，结果通过 `GET /v1/jobs/{job_id}` 查询。
- 同一端到端流程复用 `trace_id`；重试生成新 `job_id`，并通过 `execution.retry_of_job_id` 关联前次任务。
- 成功分析发现写入 `ERROR_REPORT`，任务仍可为 `SUCCEEDED`；执行失败写入 `error`，终态为 `FAILED`、`TIMED_OUT` 或 `CANCELLED`，且不返回半成品 `output`。
- 大型交接数据使用 `artifact://` URI；每个产物必须记录生产 Job、完整 commit 和 `configuration_id`。在本仓库中 URI 映射至 `artifacts/`，以后可替换为对象存储而不改变消费者接口。
- EChecker 必须验证 `baseline.commit == base_commit`，并验证 baseline 与当前环境的 `configuration_id` 一致；缺失或不一致的输入返回 HTTP 400，不创建 Job。
- `INCREMENTAL_CHECK.input.project_root` 是镜像内执行构建的非空路径。该字段在 E2 尚未有服务消费者前补入所有 Schema、样例和校验；若未来已有消费者再采用这一新增必填字段，必须按版本兼容规则提升主版本。

## 备选方案

- 同步 HTTP 请求：实现简单，但执行时间与客户端连接耦合，无法可靠承载构建和分析任务。
- 将图、日志和补丁直接嵌入响应：小样例方便阅读，但会造成超大响应，且不利于跨组传递与完整性追溯。
- 使用绝对本地路径传递产物：实现成本低，但接收方无法在不同主机或未来的对象存储中稳定读取。

## 后果

- 每个服务需要保存 Job 元数据、状态和产物元数据；消费者必须能解析或下载约定的 URI。
- 改动字段、状态枚举或字段语义时必须考虑消费者；破坏性变化提升 `schema_version` 主版本。
- 契约至少需要有效样例、无效样例和跨字段校验，不能只依靠接口文字描述。

## 验证

运行 `python3 scripts/validate_contract.py`。该校验会验证四类有效请求和响应、一个分析失败 Job、未知 `job_type`、缺少 EChecker baseline，以及 baseline 提交不匹配的拒绝行为。
