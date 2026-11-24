# 教师微服务样例（Issue #53，231880027）

本目录选择性保留教师 Microservice_Lab 的 API/Worker、监控配置及脚本，内容保持原样；它对固定依赖集合做差，不执行本组四项论文工具。个人实测与原始目录见 [阶段 1 记录](../../../docs/evidence/microservice/231880027/sample-validation.md)。

## 独立启动

在服务器本目录执行，始终限定个人 Compose 项目：

```bash
python3 scripts/lab.py init
# 编辑 .env：参照 .env.example 设置个人端口、项目名和已核对的镜像引用。
# 保留 init 生成的私有 Grafana 密码，不提交 .env。
chmod 600 .env
find app monitoring scripts -type d -exec chmod 755 {} +
find app monitoring scripts -type f -exec chmod 644 {} +
docker compose -p issue53-sample-231880027 config --quiet
docker compose -p issue53-sample-231880027 up -d --wait --wait-timeout 90
python3 scripts/lab.py target 1
```

电脑端使用 SSH 转发：

```bash
ssh -N -L 19390:127.0.0.1:19390 -L 13300:127.0.0.1:13300 root@47.110.157.207
```

Prometheus：`http://localhost:19390/targets`；Grafana：`http://localhost:13300`，用户 admin，密码在服务器私有 .env。数据源为 `http://prometheus:9090`，UID 为 lab-prometheus；面板 UID 为 microservice-lab。

## 三阶段与受控超时

```bash
python3 scripts/lab.py run normal
# 正常阶段至少保留 20 秒采样。
docker compose -p issue53-sample-231880027 stop worker
python3 scripts/lab.py target 0
python3 scripts/lab.py run down
# DOWN 至少保留 25 秒采样，确认后才恢复。
docker compose -p issue53-sample-231880027 start worker
docker compose -p issue53-sample-231880027 up -d --wait --wait-timeout 45 worker
python3 scripts/lab.py target 1
python3 scripts/lab.py run recovered
# 恢复阶段至少保留 25 秒采样。
python3 scripts/lab.py run timeout
docker compose -p issue53-sample-231880027 logs --timestamps --no-color api worker
```

每次脚本运行自动创建新输出目录和幂等键，并以同键重提检查任务未重复创建。预期依次为 SUCCEEDED/1、FAILED/3、SUCCEEDED/1、TIMED_OUT/3；脚本正确识别预期故障时退出 0。

Prometheus 每 4 秒采样、抓取超时 2 秒，Grafana 每 5 秒刷新。截图使用同一绝对时间范围，保留时间和图例。原始 work/ 与 .env 已忽略。查看完可执行：

```bash
docker compose -p issue53-sample-231880027 down
```

本轮只停止个人样例 Worker，没有停止公共 EChecker。正式项目采样与 #54 协调，后续另行记录。
