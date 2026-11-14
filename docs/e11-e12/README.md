# E11–E12 A11 操作入口

## 公共环境

在 Linux 云服务器上设置本地 Git 身份为数字学号后执行：

    python3 run_e11e12.py build
    python3 run_e11e12.py test
    python3 run_e11e12.py prepare

prepare 只创建课程生成的 data/integration-sample/，真实项目必须另建 data/real-project/，并使用完整 base/target SHA。data/ 和 work/ 不进入 Git。

2026-11-14 收尾验证使用独立服务器克隆 /root/241880439/DevOps_A11-e11-e12-20261114。已存在的旧样例与个人目录保留。Docker Hub 元数据不可达时可通过 --docker-cli-image 指定相同摘要的镜像源；prepare 支持 --dataset-name、--python-image、--debian-mirror，覆盖值写入 dataset.json。示例：

    python3 run_e11e12.py build --docker-cli-image m.daocloud.io/docker.io/library/docker:28.5.1-cli@sha256:9190b0613792e658a7783cf14b2d5ace5941bb68ede7276922ea36ee457d76ad
    python3 run_e11e12.py prepare --dataset-name integration-mirror --python-image m.daocloud.io/docker.io/library/python:3.13-slim@sha256:f82c96458eedc847b233e582eb31336f4954b39cae020b6dcf5b3ed0e5cbcd74 --debian-mirror https://mirrors.tuna.tsinghua.edu.cn

重新运行须用新的 dataset-name 和 work 子目录。镜像源替换保持指定摘要，不关闭 TLS 或包签名校验。

## A11 E11-A

    python3 run_e11e12.py run --request data/integration-sample/e11-a.json --out work/e11-a-leader
    cat work/e11-a-leader/result.json

通过条件：baseline 的 BuildChecker 实际图与 GCC 投影一致；target 的增量报告与同一 target 的全量报告在 main.o/helper.o 发现集合一致；所有报告记录 commit、job_id、trace_id 和产物 SHA。

## 服务启动（只准备，不等于联调完成）

    python3 run_e11e12.py serve --port 8080

服务宿主端口只绑定 127.0.0.1，B11 通过 SSH 转发访问。相同幂等键必须复用任务，修改输入返回 409；服务重启会把未完成任务标记为 SERVER_RESTARTED。真实跨组联调由组长后续亲自执行并单独记录。

组长本轮服务容器为 a11-e12-20261114。下载与取证入口：

    python3 scripts/e11e12/api_client.py --request data/integration-mirror/e12.json --key <本次唯一编号> --out work/api-client-<本次唯一编号>

该命令提交真实任务并校验每个产物的清单哈希、响应头哈希和下载内容。B11 通过转发使用 --url http://127.0.0.1:18080，完整交接见 [B11联调交接](B11联调交接.md)。

## 提交边界

A11 独立 CI 运行契约测试、环境构建和 E11-A；新增 E12 reference CI 运行课程固定 MD 适配器、五阶段和真实回环 API，以参考回放身份归档，B11 个人实现和分机确认仍由对方提供。交付内容、状态与剩余人工事项见 [最终交付检查](最终交付检查.md)，三人贡献见 [最终分工与完成记录](最终分工与完成记录.md)。
