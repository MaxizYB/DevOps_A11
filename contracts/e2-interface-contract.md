# E2 接口契约

## 1. 文档信息

- 配对组：A11 / B11
- 版本：1.0.0
- 更新时间：2026-09-20
- 说明：本文件记录 E2 阶段的接口、数据传递和验收约定。`INCREMENTAL_CHECK` 的 `project_root` 在 E2 尚未有服务消费者前完成最终化，因此仍属于 1.0.0 交付包；若已有外部消费者再采用该字段，必须按版本兼容规则发布新的主版本。

## 2. 小组职责与流程

| 服务         | 负责组 | 作用                                   |
| ------------ | ------ | -------------------------------------- |
| DRAFT        | B 组   | 生成可构建的 Docker 环境               |
| BuildChecker | A 组   | 全量检测实际依赖和声明依赖             |
| EChecker     | A 组   | 检测跨提交的增量依赖错误               |
| MDFixer      | B 组   | 根据 MD 报告生成修复补丁               |
| 重新验证     | A/B 组 | 重新构建、测试和检测，决定是否接受补丁 |

流程：

```text
DRAFT -> BuildChecker -> EChecker -> MDFixer -> 构建、测试、重检
```

## 3. 公共任务模型

### 3.1 公共字段

所有创建请求和任务响应必须包含 `schema_version`。

| 字段           | 类型        | 请求 | 响应 | 说明                                         |
| -------------- | ----------- | ---: | ---: | -------------------------------------------- |
| schema_version | string      | 必填 | 必填 | 数据结构版本，格式为 主版本.次版本.修订号    |
| job_id         | string      |    - | 必填 | 服务端生成的全局唯一任务编号                 |
| trace_id       | string      | 必填 | 必填 | 同一流程中的任务使用同一个值                 |
| job_type       | enum        | 必填 | 必填 | DRAFT、FULL_CHECK、INCREMENTAL_CHECK、REPAIR |
| status         | enum        |    - | 必填 | 任务状态，见第 4 节                          |
| execution      | object      |    - | 必填 | 服务端生成的执行信息，见第 4 节              |
| input          | object      | 必填 | 必填 | 服务专有输入                                 |
| output         | object/null |    - | 必填 | 成功结果，见第 6 节                          |
| error          | object/null |    - | 必填 | 执行错误，见第 5 节                          |

### 3.2 标识和重试

- `job_id` 必须全局唯一，格式为 `job-<job_type>-<唯一标识>`。
- `trace_id` 标识一次完整流程，格式为 `trace-<唯一标识>`。
- 创建任务时由服务端生成 `job_id`。
- 任务重试时生成新的 `job_id`，继续使用原来的 `trace_id`。
- 重试任务在 `execution.retry_of_job_id` 中记录上一次的 `job_id`。
- 创建请求必须携带 `idempotency_key`，用于避免重复创建相同任务。

### 3.3 创建请求和任务响应

创建请求的必填字段：

```text
schema_version
trace_id
job_type
idempotency_key
input
```

创建请求不包含 `job_id`、`status`、`execution`、`output` 和 `error`。

任务响应的必填字段：

```text
schema_version
job_id
trace_id
job_type
status
execution
input
output
error
```

## 4. 任务状态和执行信息

### 4.1 接口

| 操作         | 参考接口                        |
| ------------ | ------------------------------- |
| 生成构建环境 | `POST /v1/dockerfile-jobs`        |
| 全量检测     | `POST /v1/full-check-jobs`        |
| 增量检测     | `POST /v1/incremental-check-jobs` |
| 修复缺失依赖 | `POST /v1/repair-jobs`            |
| 查询任务     | `GET /v1/jobs/{job_id}`           |

创建接口接受请求后返回 HTTP 202 和 `job_id`。客户端通过查询接口获取任务结果。

### 4.2 状态

```text
QUEUED -> RUNNING -> SUCCEEDED
                  |-> FAILED
                  |-> TIMED_OUT
                  `-> CANCELLED
```

- `QUEUED`：任务已接受，等待执行。
- `RUNNING`：任务正在执行。
- `SUCCEEDED`：任务正常完成，结果可用；检测到 MD/RD 仍属于成功完成。
- `FAILED`：工具或系统执行失败。
- `TIMED_OUT`：超过允许的执行时间。
- `CANCELLED`：任务被取消。

### 4.3 execution

`execution` 由服务端生成。客户端只在 `input` 中提供任务所需的超时时间。

所有任务都必须在 `input` 中提供 `timeout_seconds`。该值由调用方根据任务类型、项目规模和运行资源保守设置，不要求额外试运行，也不设置默认值。计时从 `started_at` 开始，不包含排队时间。

| 字段            | 类型          | 规则                              |
| --------------- | ------------- | --------------------------------- |
| attempt         | integer       | 服务端生成，从 1 开始             |
| retry_of_job_id | string/null   | 重试时填写上一个 Job，否则为 null |
| queued_at       | datetime      | 进入队列的时间                    |
| started_at      | datetime/null | 实际开始执行的时间                |
| finished_at     | datetime/null | 任务结束的时间                    |
| duration_ms     | integer/null  | 实际执行时长，单位为毫秒          |
| timeout_seconds | integer       | 本次任务允许的最长执行时间        |

时间统一使用 ISO 8601 格式，例如 `2026-09-20T10:00:00+08:00`。

所有任务响应都包含上表中的 execution 字段；下表列出的字段在对应状态下必须为非 null。

| 状态      | 必填字段                                              |
| --------- | ----------------------------------------------------- |
| QUEUED    | attempt、queued_at、timeout_seconds                   |
| RUNNING   | attempt、queued_at、started_at、timeout_seconds       |
| SUCCEEDED | started_at、finished_at、duration_ms、timeout_seconds |
| FAILED    | started_at、finished_at、duration_ms、timeout_seconds |
| TIMED_OUT | started_at、finished_at、duration_ms、timeout_seconds |
| CANCELLED | finished_at、timeout_seconds                          |

## 5. 错误码和错误响应

### 5.1 错误结构

```json
{
  "code": "ENV_3002",
  "message": "Docker image build failed",
  "retryable": false,
  "details": {},
  "log_uri": "artifact://job-DRAFT-001/log-001/build.log"
}
```

| 字段      | 类型        | 说明                 |
| --------- | ----------- | -------------------- |
| code      | string      | 稳定的机器可读错误码 |
| message   | string      | 简短的人类可读说明   |
| retryable | boolean     | 是否允许重试         |
| details   | object      | 必要的补充信息       |
| log_uri   | string/null | 详细日志位置         |

### 5.2 错误码格式

错误码类型为 string，格式为 `类型_四位编号`：

```text
^[A-Z]+_[0-9]{4}$
```

编号范围按错误来源划分：

| 编号范围 | 错误类型 | 说明                               |
| -------- | -------- | ---------------------------------- |
| 1xxx     | REQUEST  | 请求字段或任务前置条件错误         |
| 2xxx     | ARTIFACT | 产物不存在、无法读取或元数据不匹配 |
| 3xxx     | ENV      | 构建环境或镜像错误                 |
| 4xxx     | EXEC     | 任务执行错误                       |
| 5xxx     | ANALYSIS | 分析工具错误                       |
| 6xxx     | REPAIR   | 修复或修复后验证错误               |

### 5.3 具体错误码

| 错误码        | 类型     | 触发条件                                 | HTTP/任务状态        | 默认可重试 |
| ------------- | -------- | ---------------------------------------- | -------------------- | ---------: |
| REQUEST_1001  | REQUEST  | 请求缺少必填字段或字段格式错误           | HTTP 400，不创建 Job |         否 |
| REQUEST_1002  | REQUEST  | commit、configuration 或 baseline 不匹配 | HTTP 400，不创建 Job |         否 |
| ARTIFACT_2001 | ARTIFACT | 产物 URI 不可读取或产物元数据不匹配      | Job FAILED           |         否 |
| ENV_3002      | ENV      | Docker 镜像构建失败或环境不可用          | Job FAILED           |         否 |
| EXEC_4002     | EXEC     | 超过 timeout_seconds                     | Job TIMED_OUT        |         否 |
| EXEC_4003     | EXEC     | 任务被取消                               | Job CANCELLED        |         否 |
| EXEC_4004     | EXEC     | 超过 max_iterations                      | Job FAILED           |         否 |
| ANALYSIS_5001 | ANALYSIS | BuildChecker 或 EChecker 执行失败        | Job FAILED           |         否 |
| REPAIR_6001   | REPAIR   | Patch 无法应用或修复后验证失败           | Job FAILED           |         否 |

只有确认错误来自临时性基础设施故障时，`retryable` 才能设为 `true`，并在 `details` 中说明原因。

请求字段校验失败时，创建接口直接返回 HTTP 400，不创建 Job。任务创建成功后发生的错误，写入任务响应的 `error` 字段。

### 5.4 错误和检测发现的区别

- 工具没有执行完，写入 `job.error`，任务状态为 `FAILED` 或 `TIMED_OUT`。
- 正常检测到 MD/RD，不写入 `job.error`，任务仍可为 `SUCCEEDED`。
- MD/RD 写入 `ERROR_REPORT` 产物。
- `FAILED`、`TIMED_OUT` 和 `CANCELLED` 状态不允许输出半成品，`output` 必须为 null。

成功和失败的互斥规则：

```text
status = SUCCEEDED
-> output 必须存在，error 必须为 null

status = FAILED / TIMED_OUT / CANCELLED
-> error 必须存在，output 为 null
```

## 6. 产物传递规则

大文件不直接放在任务响应中，通过 artifact URI 传递。artifact URI 与具体项目名称和阶段名称无关。

### 6.1 产物结构

```json
{
  "artifact_id": "graph-001",
  "type": "ACTUAL_GRAPH",
  "uri": "artifact://job-FULL_CHECK-001/graph-001/actual.json",
  "media_type": "application/json",
  "producer_job_id": "job-FULL_CHECK-001",
  "commit": "完整 commit SHA",
  "configuration_id": "cfg-ubuntu22-gcc12-release-v1"
}
```

必填字段：

| 字段             | 说明               |
| ---------------- | ------------------ |
| artifact_id      | 产物唯一编号       |
| type              | 产物类型           |
| uri               | 产物读取地址       |
| media_type        | 文件媒体类型       |
| producer_job_id   | 生成该产物的 Job   |
| commit            | 产物对应的源码版本 |
| configuration_id  | 产物对应的构建配置 |

产物类型：

```text
DOCKERFILE
DOCKER_IMAGE
BUILD_LOG
ACTUAL_GRAPH
DECLARED_GRAPH
ERROR_REPORT
PATCH
TEST_RESULT
```

### 6.2 传递要求

- 接收方必须能够根据 uri 读取产物。
- 产物必须记录对应的 commit 和 configuration_id。
- 增量检测的 baseline 必须来自指定的 base_commit。
- 修复报告必须属于当前源码 commit。
- 产物内容和文件地址都必须能被另一组理解和读取。

artifact URI 映射到项目根目录下的 `artifacts/`：

```text
artifact://job-FULL_CHECK-001/graph-001/actual.json
-> artifacts/job-FULL_CHECK-001/graph-001/actual.json
```

后续可以将同一 URI 映射到产物服务或对象存储，调用方不依赖绝对本地路径。

`configuration_id` 使用 `cfg-系统-工具链-模式-版本` 格式，例如 `cfg-ubuntu22-gcc12-release-v1`。凡是影响构建结果的环境配置发生变化，必须生成新的 `configuration_id`；commit、job_id、trace_id 和任务类型不属于 configuration_id。

## 7. DRAFT 接口

### 7.1 输入

```json
{
  "repository": {
    "url": "https://example.com/project.git",
    "commit": "完整 commit SHA"
  },
  "build_command": "make",
  "verify_command": "make test",
  "max_iterations": 20,
  "timeout_seconds": 1800
}
```

必填字段：`repository.url`、`repository.commit`、`build_command`、`verify_command`、`timeout_seconds`。

`max_iterations` 为可选正整数，取值范围为 1 到 50，默认值为 20。如果不提供，服务端使用 20，并在任务响应的 input 中返回规范化后的值。

### 7.2 输出

`output.artifacts` 至少包含：

- DOCKERFILE
- DOCKER_IMAGE
- BUILD_LOG

同时记录最终构建结果和验证结果。只有构建及验证均通过时，DRAFT 才能报告成功产物。

### 7.3 失败

- 镜像构建失败：`ENV_3002`。
- 超过时间限制：`EXEC_4002`。
- 达到最大迭代次数仍未成功：`EXEC_4004`，并在 details 中记录实际迭代次数。

## 8. BuildChecker 接口

### 8.1 输入

```json
{
  "repository": {
    "url": "https://example.com/project.git",
    "commit": "完整 commit SHA"
  },
  "environment": {
    "image_uri": "artifact://job-DRAFT-001/image-001/image",
    "configuration_id": "cfg-ubuntu22-gcc12-release-v1"
  },
  "clean_build_command": "make clean && make",
  "project_root": "/project",
  "timeout_seconds": 1800
}
```

必填字段：仓库、完整 commit、镜像、configuration_id、clean build 命令、项目根目录和 timeout_seconds。

### 8.2 输出

`output.artifacts` 至少包含：

- ACTUAL_GRAPH
- DECLARED_GRAPH
- ERROR_REPORT
- BUILD_LOG

ERROR_REPORT 中的发现使用 MISSING 和 REDUNDANT 类型，并记录 target、dependency、commit、位置和证据。

## 9. EChecker 接口

### 9.1 输入

```json
{
  "base_commit": "C0 的完整 SHA",
  "repository": {
    "url": "https://example.com/project.git",
    "commit": "C1 的完整 SHA"
  },
  "baseline": {
    "actual_graph_uri": "artifact://job-FULL_CHECK-001/graph-001/actual.json",
    "commit": "C0 的完整 SHA",
    "configuration_id": "cfg-ubuntu22-gcc12-release-v1"
  },
  "environment": {
    "image_uri": "artifact://job-DRAFT-001/image-001/image",
    "configuration_id": "cfg-ubuntu22-gcc12-release-v1"
  },
  "build_command": "make",
  "project_root": "/project",
  "timeout_seconds": 1800
}
```

必填字段：base_commit、当前 commit、baseline 实际依赖图、baseline commit、配置 ID、镜像、构建命令、项目根目录和 timeout_seconds。`project_root` 是镜像内用于执行构建的非空路径。

baseline 的 commit 和 configuration 必须分别等于 base_commit 和当前任务使用的配置。缺少或不匹配时，创建请求被拒绝。

### 9.2 输出

`output.artifacts` 至少包含：

- 更新后的 ACTUAL_GRAPH
- ERROR_REPORT

报告应区分当前发现、新增发现和已消除发现。

## 10. MDFixer 接口

### 10.1 输入

```json
{
  "repository": {
    "url": "https://example.com/project.git",
    "commit": "完整 commit SHA"
  },
  "md_report_uri": "artifact://job-INCREMENTAL_CHECK-001/report-001/md-report.json",
  "makefile_path": "Makefile",
  "environment": {
    "image_uri": "artifact://job-DRAFT-001/image-001/image",
    "configuration_id": "cfg-ubuntu22-gcc12-release-v1"
  },
  "build_command": "make",
  "verify_command": "make test",
  "timeout_seconds": 1800
}
```

必填字段：仓库、当前 commit、MD 报告、Makefile 路径、镜像、配置 ID、构建命令、验证命令和 timeout_seconds。

MDFixer 只消费 MISSING 报告，不消费 REDUNDANT 报告。

### 10.2 输出

`output.artifacts` 至少包含：

- PATCH
- BUILD_LOG
- TEST_RESULT
- 重新检测后的 ERROR_REPORT

同时记录声明风格说明和补丁是否被接受。

### 10.3 失败

- 报告与当前 commit 不匹配：请求被拒绝。
- Patch 无法应用或验证失败：`REPAIR_6001`。
- 修复后仍有 MD：任务状态为 `FAILED`，使用 `REPAIR_6001`，补丁不作为正式产物返回。

## 11. 版本兼容规则

### 允许的变化

- 新增可选字段。
- 更新共享 Schema 的版本。
- 保留已有字段的含义。

### 需要双方确认的变化

- 删除或重命名字段。
- 修改字段类型或语义。
- 修改状态枚举。
- 将可选字段改为必填字段。

任何破坏性变化必须更新 `schema_version` 的主版本号，并同步修改请求、响应和校验样例。
