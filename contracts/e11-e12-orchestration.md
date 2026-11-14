# E11–E12 编排契约（A11 公共版本）

版本：e11e12-1
配对：A11 / B11
状态：A11 发布候选；跨组联调待双方实际验证

## 1. 边界

本文件定义 E11–E12 实验包提供的编排层输入、阶段顺序、产物引用和失败语义。它是 E2 1.0.0 异步 Job/Artifact 契约之上的组合 API，不替代 E2 的四类服务契约。E2 的 schema_version、job_id、trace_id、commit、configuration_id、幂等和错误码规则仍然适用于服务适配器。

A11 负责 BuildChecker→EChecker（E11-A）和编排层中对全量/增量报告的校验；B11 负责 DRAFT→MDFixer（E11-B）。本文件不声称 A11 已完成 A11/B11 的真实联调。

本层的 e11e12-1 是编排层内部信封版本，不覆盖 E2 的 1.0.0 服务版本。适配器必须把阶段映射为 E2 的 job_type，并在对外交换时保留 schema_version、job_id、trace_id、execution、input、output、error、commit、configuration_id 和幂等语义。这样 E12 只增加顺序编排，不改变 A/B 已约定的服务边界。

## 2. 请求

编排请求是 JSON 对象，字段如下：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| mode | 是 | e11-a、e11-b 或 e12 |
| repo | 是 | 服务器 data/ 下的项目路径；真实项目需保留来源记录 |
| base | 是 | 基线提交的完整 40 位 SHA |
| target | 是 | 目标提交的完整 40 位 SHA |
| candidate | E11-B/E12 | DRAFT 候选 Dockerfile 路径 |
| fixed_report | E11-B | 固定 MD 报告路径；E12 不使用固定报告 |
| expected_output | 否 | 镜像验证的期望输出，默认由调用方明确提供 |
| build_timeout | 否 | 构建/验证超时秒数，必须为正整数 |

路径必须位于服务端允许的 data/ 根目录内，禁止 .. 越界、绝对路径逃逸和从任意目录读取产物。

## 3. 阶段映射

| 编排模式 | 阶段顺序 | A11 / B11 边界 |
| --- | --- | --- |
| e11-a | full-check(base) → incremental-check(target) | A11 独立可验收 |
| e11-b | draft(target) → fixed-md → repair → recheck | B11 负责实际实现；A11 只保留编排兼容性 |
| e12 | draft → full-check(base) → incremental-check(target) → repair → recheck(target) | A11/B11 共同联调；本阶段不提前宣称完成 |

E11-A 的增量报告必须消费基线缓存，且与同一目标提交的全量报告在 main.o、helper.o 投影上相等。E12 的 MDFixer 输入必须是同一轮 incremental-check 的实际产物，不得回退到固定 MD。

### 3.1 E2 字段映射

| 编排阶段 | E2 job_type | 输入/输出映射 |
| --- | --- | --- |
| draft | DRAFT | candidate 对应 DRAFT 产物；构建日志和镜像引用进入 output.artifacts |
| full-check | FULL_CHECK | base 对应 repository.commit；实际图、声明图和检查报告进入 output.artifacts |
| incremental-check | INCREMENTAL_CHECK | base 对应 base_commit，target 对应 repository.commit；baseline-cache 映射为 baseline |
| repair | REPAIR | 当前 target 对应 repository.commit；candidate.patch 映射为 PATCH |
| fixed-md | — | 仅为 E11-B 的固定输入适配，不是 E12 的新服务；E12 必须消费本轮 incremental-check |

编排层产物清单包含相对 URI、SHA256、大小、commit、configuration_id 和 producer_job_id。它不是 E2 的 component Artifact 对象；E2 适配器还必须补齐对应 E2 子任务的 media_type 和 output.artifacts 结构，不能把编排层 parent job_id 伪装成 E2 component job_id。

## 4. 标识、提交和产物

- 一个编排 Job 使用一个 job_id 和 trace_id；内部各 E2 子任务保留父级关联并共享 trace_id。
- 所有报告必须写明 schema_version、commit、job_id、trace_id；产物清单必须写明 URI、SHA256、producer job、commit 和 configuration_id。
- 基线报告对应 base，修复前后的目标报告对应 target。提交不匹配直接失败并返回 STALE_REPORT。
- 下载产物后重新计算 SHA256；内容变化返回 ARTIFACT_HASH_MISMATCH，不继续消费。
- 任务结果遵守 E2 成功/失败互斥：成功有 output 且无 error；失败、超时或取消无半成品 output。

## 5. API

服务默认只绑定服务器回环地址，由 SSH 转发提供跨组访问。该 /v1/jobs 是 E12 编排任务 API，使用 e11e12-1 的父任务状态，不取代 E2 四个组件的创建/查询 API；阶段产物由适配器按上表映射为 E2 response 结构：

- GET /health
- POST /v1/jobs：请求体 {"idempotency_key":"...","input":<编排请求>}，接受后返回任务编号
- GET /v1/jobs/{job_id}：轮询状态、trace_id 和错误
- GET /v1/jobs/{job_id}/artifacts：获取产物清单
- GET /v1/jobs/{job_id}/files/{relative_path}：下载并通过 X-Content-SHA256 校验

相同幂等键和完全相同输入必须复用同一任务；同一键修改输入返回 HTTP 409 IDEMPOTENCY_CONFLICT。服务重启后未完成任务标记 SERVER_RESTARTED，已完成任务仍可查询。

## 6. 联调前置检查

双方交换请求 JSON、base/target 完整 SHA、候选文件来源、configuration_id 和端口转发方式；先分别通过本组 E11 轨道检查，再由组长启动服务进行真实联调。联调记录必须包含请求/响应、job_id、trace_id、阶段状态、产物 URI/SHA 和最终验收结果
