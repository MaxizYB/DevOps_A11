# A11 真实业务监控（Issue #53）

负责人：@tongqianpolan（231880027）。本目录只部署个人 Prometheus/Grafana，使用公共 Compose 网络抓取 API、EChecker，不启动或重启公共业务服务。教师样例另见 [sample/](../sample/README.md)，[阶段 2 记录](../../../docs/evidence/microservice/231880027/a11-observability.md)。

## 部署与访问

当前公共网络为 `a11-microservice-241880439_default`，依赖 #52 / PR #55 的业务部署。API/EChecker 监听容器端口 8080。先确认公共服务和网络存在，再在本目录操作：

```bash
cd /root/231880027/DevOps_A11-microservice/labs/observability/a11
python3 - <<'PY'
from pathlib import Path
import secrets
p = Path('.env')
if not p.exists():
    p.write_text(Path('.env.example').read_text().replace(
        'CHANGE_ME', secrets.token_urlsafe(24)))
    p.chmod(0o600)
PY
docker compose -p issue53-observability-231880027 config --quiet
docker compose -p issue53-observability-231880027 up -d
docker compose -p issue53-observability-231880027 exec -T prometheus \
  promtool check config /etc/prometheus/prometheus.yml
curl -fsS http://127.0.0.1:19391/-/ready
curl -fsS http://127.0.0.1:13301/api/health
```

镜像按 .env.example 的 digest 固定，当前 ECS 已有，pull_policy 为 never；新环境需先准备这些镜像。若组件仍在启动，等待就绪后重试上述健康查询。不要输出完整的 Compose 渲染配置或 .env，以免暴露密码。

电脑端：

```bash
ssh -N -L 19391:127.0.0.1:19391 -L 13301:127.0.0.1:13301 root@47.110.157.207
```

- Targets：`http://localhost:19391/targets`，应有 a11-api、a11-echecker，两者 UP。
- Grafana：`http://localhost:13301/d/a11-microservice-231880027`。用户 admin，密码保存在本目录私有 .env。
- 数据源 UID：a11-prometheus；容器内 URL：`http://prometheus:9090`。
- 抓取周期 4 秒、超时 2 秒；面板刷新 5 秒；Prometheus 数据保留 14 天。
- 网络：只有个人 Prometheus 加入公共 external 网络，Grafana 通过个人网络访问 Prometheus；宿主端口只绑定 loopback。

## 实际指标与面板

`prometheus.yml` 抓取 `api:8080/metrics`、`echecker:8080/metrics`。五个面板的实际 PromQL 见 `grafana/dashboards/a11.json`：

1. 两个业务目标的 up 时序。
2. `a11_jobs_total{job="a11-api"}`，按 succeeded/failed/timed_out 展示 API 累计任务数。
3. `a11_stage_requests_total{job="a11-echecker"}`，独立展示 EChecker 请求数，不与 API 任务数相加。
4. API 的 duration_seconds_sum/count 近 1 分钟 rate 比值，按状态统计平均任务耗时。
5. EChecker 对应 sum/count 的近 1 分钟 rate 比值。

原始 counter 包含部署前的历史任务。低流量窗口可查询 `increase(a11_jobs_total{job="a11-api"}[5m])`；它是 Prometheus 外推估计，不当作精确整数任务数。精确任务数通过原始 counter 前后值和 job 日志核对。进程重启会归零，可查询 `resets(a11_jobs_total{job="a11-api"}[5m])`；rate/increase 按 counter 处理重置。

耗时无已完成请求时显示空数据，不补零，也不把平均耗时标作 P95。up=1 仅代表抓取成功；无数据与实际 up=0 分别排查。

## 正常任务与日志核对

在仓库根目录，使用公共部署能访问的原始输入，输出使用新目录：

```bash
cd /root/231880027/DevOps_A11-microservice
run_id=$(date -u +%Y%m%dT%H%M%SZ)
python3 labs/microservice/run_job.py \
  --request /root/241880439/DevOps_A11-microservice-20261124/data/e13-a11-project-20261117-v2/e12.json \
  --key "issue53-231880027-normal-$run_id" \
  --out "work/issue53-a11-normal-$run_id"
```

任务前后各保留至少 20–25 秒采样。按返回的 job_id/trace_id 检索 `docker logs --timestamps a11-microservice-241880439-api-1` 与 `docker logs --timestamps a11-microservice-241880439-echecker-1`，核对 incremental-check 的尝试、结束与整个任务终态。本轮实际任务、退出码和产物见阶段 2 记录。

## 与 #54 的正式采样窗口

当前阶段只完成正常任务采样，未执行公共停机。由 #54 协调同一输入的正常、故障、恢复任务，提前告知预计时间与实际 job/trace；本监控必须在故障前启动并已有正常样本。停止实际 EChecker 后，等 Prometheus 产生有效 up=0 样本再由 #54 恢复。保存覆盖三阶段的同一绝对时间窗口、Targets、面板导出、任务日志和错误码；面板现有历史失败计数不能作为本轮故障证据。

查看完只关闭个人监控，不删除公共网络或数据卷：

```bash
cd /root/231880027/DevOps_A11-microservice/labs/observability/a11
docker compose -p issue53-observability-231880027 down
```

.env、work/ 与登录信息不提交；AI 使用在仓库根 AI_USAGE.md 中记录。
