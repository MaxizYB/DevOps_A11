# E11–E12 公共准备记录

日期：2026-11-10
仓库：A11 / DevOps_A11
负责人：MaxizYB（241880439）
追溯入口：Issue #36

## 已接入

- run_e11e12.py：构建、样例准备、E11-A/E11-B/E12 回放、服务启动和容器内契约测试入口。
- labs/e11e12/：E11-A 编排、E12 父任务 API、DRAFT 兼容适配器、契约拒绝测试。
- contracts/e11-e12-orchestration.md 与 contracts/schemas/e12-orchestration-request.schema.json：在 E2 1.0.0 之上增加编排层，不覆盖共享契约。
- .github/workflows/e11e12-a.yml：只检查 A11 的 E11-A，不把 B11 实现或真实 A/B 联调计入 CI。
- docs/e11-e12/、docs/backlog/e11-e12-backlog.md：公共操作、成员任务和证据边界。
- .gitignore：忽略 data/、work/、压缩包、凭据和 Python/Docker 运行缓存。

## 当前可复现校验

在本机 Docker daemon 不可用，因此以下是实际完成的非容器校验，不冒充云端构建或联调：

    python3 -m py_compile run_e11e12.py labs/e11e12/*.py
    12 项 labs/e11e12 契约/边界测试通过
    git diff --check

课程生成样例已在本地工作区生成并运行过 E11-A，结果为 SUCCEEDED；原始 data/ 和 work/ 被忽略，不作为组长个人实验或真实项目证据提交。真实 E11-A、服务器 Docker 构建和 API 运行必须在服务器克隆中重新执行并保存新的证据目录。

## 云端执行顺序

先同步合并后的 main，再设置本地 Git 身份为 241880439，然后依次执行：

    python3 run_e11e12.py build
    python3 run_e11e12.py test
    python3 run_e11e12.py prepare
    python3 run_e11e12.py run --request data/integration-sample/e11-a.json --out work/e11-a-241880439-<timestamp>
    python3 run_e11e12.py serve --port 8080

服务只绑定回环地址；跨组访问使用 SSH -L 转发，不开放公网 8080。联调前双方先交换完整 base/target SHA、候选文件来源、configuration_id 和请求 JSON；联调日志由组长另行保存。

## 明确未完成项

- B11 的 DRAFT→MDFixer 生产实现不在 A11 公共准备中。
- A11/B11 的真实 E12 联调尚未完成；服务入口只是已准备，不能写成通过。
- 当前本机没有 Docker daemon，未宣称镜像构建、容器服务启动或云端资源验证成功。
