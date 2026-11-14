# E11–E12 A11 操作入口

## 公共环境

在 Linux 云服务器上设置本地 Git 身份为数字学号后执行：

    python3 run_e11e12.py build
    python3 run_e11e12.py test
    python3 run_e11e12.py prepare

prepare 只创建课程生成的 data/integration-sample/，真实项目必须另建 data/real-project/，并使用完整 base/target SHA。data/ 和 work/ 不进入 Git。

## A11 E11-A

    python3 run_e11e12.py run --request data/integration-sample/e11-a.json --out work/e11-a-leader
    cat work/e11-a-leader/result.json

通过条件：baseline 的 BuildChecker 实际图与 GCC 投影一致；target 的增量报告与同一 target 的全量报告在 main.o/helper.o 发现集合一致；所有报告记录 commit、job_id、trace_id 和产物 SHA。

## 服务启动（只准备，不等于联调完成）

    python3 run_e11e12.py serve --port 8080

服务宿主端口只绑定 127.0.0.1，B11 通过 SSH 转发访问。相同幂等键必须复用任务，修改输入返回 409；服务重启会把未完成任务标记为 SERVER_RESTARTED。真实跨组联调由组长后续亲自执行并单独记录。

## 提交边界

A11 CI 只运行契约测试、环境构建和 E11-A；不运行 B11 的实现，也不把 E12 联调写成已通过。完整流程和真实项目验收待 B11 就绪后执行
