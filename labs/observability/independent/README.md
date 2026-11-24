# 独立 A11 业务三阶段观测（Issue #53）

负责人 @tongqianpolan（231880027）。复用公共四角色与网关实现，以新的源码快照、输入副本、Compose 项目、网络、输出和监控卷完成个人正常/停机/恢复。业务代码未修改；本实验不等同于 #54 本人的独立验收或公共协作窗口。

本轮结果和截图见 [独立观测记录](../../../docs/evidence/microservice/231880027/independent-validation.md)。服务镜像复用公共镜像的实际 ID，不声称本轮重新构建服务镜像；DRAFT 对候选的业务构建仍实际执行。

## 本轮环境

- 项目：`issue53-business-231880027`，网络：`issue53-business-231880027_default`。
- API：`127.0.0.1:18381`，Prometheus：`127.0.0.1:19392`，Grafana：`127.0.0.1:13302`。
- 运行根：`work/issue53-independent-20261124/runtime`；原始证据：`work/issue53-independent-20261124/evidence`。
- 源码快照：`f4026115dfd4185fa26d178da396a604c3a0dbd1`，只归档 Git 源文件，不复制真实 .env、Git 登录信息、历史 data/work。
- 个人输入位于运行根 `data/issue53-project/`。base/target 分别为 `5b431fcc656804434db59f4452f046ef284e6eb4` / `c2301112968b4cf185a94449e5dbc85764f4a2df`。
- Prometheus 复用阶段 2 的抓取配置，但部署于个人业务网络，数据库和 Grafana 数据卷独立；阶段 2 公共网络监控继续运行。
- 抓取周期 4 秒、超时 2 秒，Grafana 刷新 5 秒。UID 为 `a11-independent-231880027`，数据源 UID 为 `a11-prometheus`。

## 新克隆首次准备运行环境

本节用于尚无本轮私有 .env 的新克隆。在仓库根目录执行，使用新的运行目录。当前环境已准备好，直接使用后续启动/验证步骤即可。公共输入是只读来源；新环境需先准备对应输入和 .env.example 中固定的镜像。

```bash
cd /root/231880027/DevOps_A11-microservice
run_id=$(date -u +%Y%m%dT%H%M%SZ)
runtime="$PWD/work/issue53-independent-$run_id/runtime"
mkdir -p "$runtime"
git archive f4026115dfd4185fa26d178da396a604c3a0dbd1 | tar -x -C "$runtime"
source_data=/root/241880439/DevOps_A11-microservice-20261124/data/e13-a11-project-20261117-v2
mkdir -p "$runtime/data/issue53-project"
cp "$source_data/a11-project.bundle" "$source_data/candidate.Dockerfile" "$runtime/data/issue53-project/"
git clone "$runtime/data/issue53-project/a11-project.bundle" "$runtime/data/issue53-project/repo"
git -C "$runtime/data/issue53-project/repo" checkout --detach c2301112968b4cf185a94449e5dbc85764f4a2df
python3 - "$runtime" "$source_data" <<'PY'
from pathlib import Path
import json, secrets, sys
runtime, source = map(Path, sys.argv[1:])
request = json.loads((source / 'e12.json').read_text())
request.update(repo='/course/data/issue53-project/repo',
               candidate='/course/data/issue53-project/candidate.Dockerfile')
(runtime / 'data/issue53-project/e12.json').write_text(json.dumps(request, indent=2) + '\n')
config = Path('labs/observability/independent')
if (config / '.env').exists():
    raise SystemExit('Existing .env: retain it; use a separate env file for another run.')
lines = (config / '.env.example').read_text().splitlines()
lines = ['E14_ROOT=' + str(runtime) if x.startswith('E14_ROOT=') else x for x in lines]
lines = [x.replace('CHANGE_ME', secrets.token_urlsafe(24)) for x in lines]
env = config / '.env'
env.write_text('\n'.join(lines) + '\n')
env.chmod(0o600)
PY
```

当前 .env 已存在，直接用于本轮服务，不需重做上面准备；若另起运行，请将新环境写入单独的私有 env 文件并使用另一个项目名/空闲端口。不要覆盖或删除本轮 .env 后直接改指向运行中的服务。

## 启动和验证

在仓库根目录定义，只操作该个人项目：

```bash
stack() {
  docker compose --env-file labs/observability/independent/.env \
    -p issue53-business-231880027 \
    -f labs/e13e14/compose.yaml \
    -f labs/microservice/compose.yaml \
    -f labs/observability/independent/compose.yaml "$@"
}
stack config --quiet
stack up -d --wait --wait-timeout 100
stack exec -T prometheus promtool check config /etc/prometheus/prometheus.yml
curl -fsS http://127.0.0.1:18381/health
curl -fsS http://127.0.0.1:19392/-/ready
curl -fsS http://127.0.0.1:13302/api/health
stack ps
```

电脑端访问：

```bash
ssh -N -L 19392:127.0.0.1:19392 -L 13302:127.0.0.1:13302 root@47.110.157.207
```

Targets：`http://localhost:19392/targets`；面板：`http://localhost:13302/d/a11-independent-231880027`。用户 admin，密码在私有 .env；不要将密码或登录文件写入报告或 Git。

## 正常、停机、恢复

以下命令适用于已经准备好的个人环境。新的实验用新输出目录和幂等键；先观察至少 25 秒正常采样。

```bash
run_id=$(date -u +%Y%m%dT%H%M%SZ)
runtime=$(sed -n 's/^E14_ROOT=//p' labs/observability/independent/.env)
request="$runtime/data/issue53-project/e12.json"
python3 labs/microservice/run_job.py --url http://127.0.0.1:18381 \
  --request "$request" --key "issue53-$run_id-normal" --out "work/issue53-$run_id-normal"
# 保留至少 25 秒正常任务后的采样，再停止个人 EChecker。
stack stop echecker
# 在个人 Targets 和 up{job="a11-echecker"} 查询中确认实际 DOWN。
python3 labs/microservice/run_job.py --url http://127.0.0.1:18381 \
  --request "$request" --key "issue53-$run_id-down" --out "work/issue53-$run_id-down" \
  --expect-error DOWNSTREAM_UNAVAILABLE
# 保留至少 30 秒故障采样。
stack start echecker
stack up -d --no-deps --wait --wait-timeout 60 echecker
# 确认健康与实际 UP 后，再提交恢复任务。
python3 labs/microservice/run_job.py --url http://127.0.0.1:18381 \
  --request "$request" --key "issue53-$run_id-recovered" --out "work/issue53-$run_id-recovered"
# 保留至少 30 秒恢复采样，导出同一绝对窗口的面板、Targets、指标和日志。
stack logs --timestamps --no-color api echecker
```

服务不可用时任务应在 incremental-check 阶段 FAILED，错误码 DOWNSTREAM_UNAVAILABLE、尝试 3 次；客户端正确识别预期错误时退出 0。若发生镜像、内存或网络部署故障，应保留原始错误，不能记作该目标故障通过。

## 指标、计数重置和边界

五个面板复用阶段 2 的真实 PromQL，完整表达式见 `a11-independent.json` 和原始 window.json：

- up 观察 API 与 EChecker；API 始终 UP，EChecker UP/DOWN/UP。
- API 计数器未重启，本轮从零累积至 succeeded=2、failed=1、timed_out=0。
- EChecker 的内存计数随 stop/start 归零，恢复后 succeeded=1 是正确结果，不当作整轮累计值。
- 用 `resets(a11_stage_requests_total{job="a11-echecker",status="succeeded"}[5m])` 核对重置；耗时由 sum/count 的近 1 分钟 rate 比值计算，无请求显示空数据。
- 正常与恢复按同 job/trace 对齐 API、EChecker 日志；停机任务只有 API 的失败尝试及终态，下游停止期间没有该任务日志。

复用了 Docker daemon/构建缓存，CPU、内存和网络仍共享；本轮串行运行任务。不要执行全局 prune、宽泛 docker stop 或操作组员 Compose。

查看结束可 `stack down`，保留个人证据和卷；此命令不影响其他项目。后续由 #54 自行复测/确认，不冒写其个人结果，也不把本轮记作已协调的公共故障窗口。
