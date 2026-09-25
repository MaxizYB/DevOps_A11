# E2 BuildChecker 交接说明

## 1. 任务范围

- 关联 Issue：#2
- Job 类型：`FULL_CHECK`
- BuildChecker 在固定 commit、固定 `configuration_id` 下执行全量 MD/RD 检测。
- 当前 E2 只定义模块交接内容，不实现真正的检测器。

## 2. 输入说明

BuildChecker 沿用 `contracts/e2-interface-contract.md` 中的 `FULL_CHECK` 输入字段：

| 字段 | 作用 |
| --- | --- |
| `repository.url` | 指定待检仓库的读取地址。 |
| `repository.commit` | 指定本次分析使用的完整 commit SHA。 |
| `environment.image_uri` | 指向可读取的构建环境镜像产物。 |
| `environment.configuration_id` | 标识影响构建结果的环境配置。 |
| `clean_build_command` | 在项目目录中执行 clean build。 |
| `project_root` | 指定镜像内的项目根目录。 |
| `timeout_seconds` | 限制本次任务允许的最长执行时间。 |

依赖图和 MD/RD 报告必须绑定同一个固定 commit 与固定 `configuration_id`。本说明不增加或重新设计公共字段。

## 3. 前置条件

BuildChecker 开始分析前需要满足：

- 能定位到请求中的完整 commit；
- `image_uri` 可读取；
- 构建环境可以运行；
- `configuration_id` 已确定；
- `project_root` 存在；
- `clean_build_command` 可以执行；
- clean build 正常完成后再进入依赖分析。

构建或分析失败时，使用现有公共契约中的任务状态和错误模型，不新增错误码。

## 4. 输出产物

成功的 BuildChecker 任务至少产生以下产物：

| 产物 | 用途和主要消费者 |
| --- | --- |
| `ACTUAL_GRAPH` | 记录本次构建实际使用的依赖。EChecker 以它作为增量检测的主要输入。 |
| `DECLARED_GRAPH` | 记录构建脚本声明的依赖，用于和实际依赖对照。 |
| `ERROR_REPORT` | 记录 MISSING 和 REDUNDANT 检测结果。MDFixer 只读取其中的 MISSING 检测结果。 |
| `BUILD_LOG` | 记录构建过程，供任务排查和人工检查使用。 |

## 5. MD/RD 语义

- `MISSING`：实际依赖存在，但声明依赖中缺失。
- `REDUNDANT`：声明依赖存在，但本次构建实际未使用。

样例中的实际依赖为 `main.o -> main.c` 和 `main.o -> config.h`，声明依赖为 `main.o -> main.c` 和 `main.o -> unused.h`。两张图对比后：

- `main.o -> config.h` 只出现在实际依赖图中，因此报告为 `MISSING`；
- `main.o -> unused.h` 只出现在声明依赖图中，因此报告为 `REDUNDANT`。

## 6. 下游交接

EChecker 主要读取 `ACTUAL_GRAPH`，读取前检查产物的 commit 和 `configuration_id`。MDFixer 读取 `ERROR_REPORT` 中的 `MISSING` 检测结果，不消费 `REDUNDANT`。

所有下游读取的产物都应与当前源码 commit 和 `configuration_id` 对应。

## 7. 正常检测结果与任务失败

`ERROR_REPORT` 和 `job.error` 表达不同内容。

正常检测到 MD/RD 时：

- Job 可以是 `SUCCEEDED`；
- `output` 存在；
- `error = null`；
- 检测结果写入 `ERROR_REPORT`。

环境、执行或分析器失败时：

- Job 为 `FAILED`、`TIMED_OUT` 或 `CANCELLED`；
- `output = null`；
- `error` 存在。

失败任务不返回可供下游消费的半成品依赖图。

BuildChecker 使用公共契约中已有的错误码：

| 场景 | 错误码或状态 |
| --- | --- |
| `image_uri` 无法读取或产物元数据不匹配 | `ARTIFACT_2001`，Job 为 `FAILED` |
| 构建环境不可用 | `ENV_3002`，Job 为 `FAILED` |
| BuildChecker 在生成依赖图前执行失败 | `ANALYSIS_5001`，Job 为 `FAILED` |
| 超过 `timeout_seconds` | `EXEC_4002`，Job 为 `TIMED_OUT` |
| 任务被取消 | `EXEC_4003`，Job 为 `CANCELLED` |

失败响应格式可参考 `contracts/samples/responses/full-check-failed.json`。该样例使用 `ANALYSIS_5001` 表示 BuildChecker 在生成依赖图前退出，响应中 `output = null`，错误信息写入 `error`。

## 8. 样例性质

`services/buildchecker/examples/` 中的文件是 E2 模块交接样例，用于说明产物内容。这些文件不代表 BuildChecker 已经真实运行，也不作为工具准确率或运行结果证据。

公共规范始终以 `contracts/` 下的现有契约为准。
