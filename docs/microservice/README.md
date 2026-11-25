# A11 微服务实验

依据 2026 秋发放的 Microservice_Lab.zip。教师样例与 A11 真实配置探针分别运行。组长公共验收记录见 [组长验收记录](组长验收记录.md)。

| 负责人 | 任务 | 提交物 |
| --- | --- | --- |
| 241880439 / MaxizYB | [#52](https://github.com/MaxizYB/DevOps_A11/issues/52) 公共部署与集成 | Compose、任务接口、真实输入、五阶段实测、期末报告底稿 |
| 231880027 / tongqianpolan | [#53](https://github.com/MaxizYB/DevOps_A11/issues/53) 监控与日志 | Prometheus、Grafana、三段时间窗口和同任务日志 |
| 241880411 / andelutixia | [#54](https://github.com/MaxizYB/DevOps_A11/issues/54) 容错与回滚 | 正常、停机、恢复和拒绝补丁的独立证据 |

两位成员在个人 Issue 下回填工作分支、PR、运行时间与证据路径。两人约定一个停机窗口，等 Prometheus 记录一次 DOWN 后再启动同一个 EChecker。

## 云服务器目录

- A11 公共运行目录为 `/root/241880439/DevOps_A11-microservice-20261124`，Compose 项目为 `a11-microservice-241880439`，API 宿主端口为 `127.0.0.1:18280`。
- 教师样例独立目录为 `/root/241880439/Microservice_Lab-20261124/Microservice_Lab`，Compose 项目为 `a11-microservice-sample-241880439`。样例 API、Prometheus、Grafana 使用实验包默认回环端口。通过 SSH 转发访问监控。
- 已有 E12 环境用 `127.0.0.1:8080`。本轮使用上述项目名限定 Compose 操作。
- 私有凭据和环境文件存于云端并按最小权限管理。原始结果写到各自的 `work/`，Git 只提交配置、记录和证据索引。

## 准备固定输入

公共运行目录中已恢复 A11 配置探针。新克隆者可从 A11 上次交接包取出原始 `a11-project.bundle`、`candidate.Dockerfile` 和请求 JSON，按下列位置布置：

```text
data/e13-a11-project-20261117-v2/
  a11-project.bundle
  candidate.Dockerfile
  e12.json
  repo/                         # git clone a11-project.bundle repo
```

`base` 为 `5b431fcc656804434db59f4452f046ef284e6eb4`，`target` 为 `c2301112968b4cf185a94449e5dbc85764f4a2df`。请求中的 `repo` 和 `candidate` 使用容器路径 `/course/data/e13-a11-project-20261117-v2/...`。候选 Dockerfile SHA256 为 `621c2d44a7f7b05a796f03ed6301b9df8d28e3aba9e7cac2520b2cd8f1def6a7`。输入应保留原 Git 提交与文件字节。

## 启动与实验命令

在 A11 仓库根目录执行。云端 `course-e11e12:241880439` 已有，另建环境时按 [E11/E12 环境说明](../e11-e12/README.md) 获取对应镜像。需要替换镜像来源时按 [组长记录](组长验收记录.md) 使用已校验的源映射。

```sh
export E14_ROOT="$PWD" E14_IMAGE=course-e11e12:241880439
# 云服务器课程镜像源映射已预置。独立镜像源环境按实际情况设置。
export EXPERIMENTAL_BUILDKIT_SOURCE_POLICY=/course/work/microservice-infrastructure/source-policy.json
stack() {
  docker compose -p a11-microservice-241880439 -f labs/e13e14/compose.yaml -f labs/microservice/compose.yaml "$@"
}
stack config --quiet
stack up -d --wait --wait-timeout 95
stack ps
curl -fsS http://127.0.0.1:18280/health
curl -fsS http://127.0.0.1:18280/metrics

request=data/e13-a11-project-20261117-v2/e12.json
run_id=$(date -u +%Y%m%dT%H%M%SZ)
python3 labs/microservice/run_job.py --request "$request" \
  --key "$run_id-normal" --out "work/microservice-$run_id-normal"
```

任务 API 复用 E12 的 `/v1/jobs`、进度查询和产物下载协议。内网由 API 按服务名调用 DRAFT、BuildChecker、EChecker 和 MDFixer，容器之间使用端口 8080。任务原始证据在 `work/microservice-jobs/<job_id>/evidence/runtime/`，可使用 `python3 labs/e13e14/verify_evidence.py <runtime目录>` 校验完整产物。外部的课程 `scripts/project.py ... --port 18280` 也可验证五阶段。此前为旧 E12 内部产物编写的专用断言由新客户端和 E14 原始证据核验器覆盖。

停机验收由 #54 执行。在三轮中使用同一份请求，键分别加 `-normal`、`-down`、`-recovered`。停止角色后，带 `--expect-error DOWNSTREAM_UNAVAILABLE` 调用客户端。

```sh
stack stop echecker
python3 labs/microservice/run_job.py --request "$request" \
  --key "$run_id-down" --out "work/microservice-$run_id-down" \
  --expect-error DOWNSTREAM_UNAVAILABLE
# 等监控负责人确认捕获 DOWN 样本后再恢复。
stack start echecker
stack up -d --wait --wait-timeout 75 echecker
python3 labs/microservice/run_job.py --request "$request" \
  --key "$run_id-recovered" --out "work/microservice-$run_id-recovered"
stack logs --timestamps --no-color api draft buildchecker echecker mdfixer \
  > "work/microservice-$run_id-services.log"
```

API 对拒绝连接或服务名暂时不可解析最多尝试三次。收到下游 HTTP 错误或读取超时时直接结束该任务。原始快照位于每个任务独立目录。

## 监控接口

| 目标 | 指标 | 用法 |
| --- | --- | --- |
| `api:8080/metrics` | `a11_jobs_total{service="api",status="..."}` | 终态成功、失败、超时分组计数 |
| `api:8080/metrics` | `a11_jobs_duration_seconds_sum` / `_count` | 用同一窗口的每组增量比计算平均任务耗时 |
| `echecker:8080/metrics`，其他角色同理 | `up`、`a11_stage_requests_total`、`a11_stage_requests_duration_seconds_sum` / `_count` | 采集健康、各服务请求结果和耗时 |

状态标签取 `succeeded`、`failed`、`timed_out`。进程重启后计数从零开始，跨重启用 PromQL `increase` 或 `rate`。同一个任务的 API 与角色日志按 `job_id` / `trace_id` 检索。故障时查 API 日志的 `stage_attempt_failed`、`stage_finished`、`job_finished`，以及故障前后角色的同编号记录。

## 集成边界与交付

真实任务的 DRAFT 镜像执行构建和输出验证，检测、补丁和复检角色运行在固定教学镜像。`environment.json` 与容器镜像清单分别记录两者，没有证据证明后续角色消费了 DRAFT 产出的镜像。演示可展示镜像标识及这项限制。

上机报告按教师模板汇总部署、业务指标、三阶段故障、补丁回滚和真实 Git 提交五阶段。期末报告建议正文 6–10 页，2026-12-01 前按助教通知提交，12 月进行 20 分钟小组汇报。已有课程验收按 [期末报告底稿](期末报告底稿.md) 集中索引。
