# E13/E14 公共基础复现

在有旧 E11/E12 教学镜像的Linux私有克隆中，git local user.name应为本人学号。

    python3 run_e11e12.py test
    python3 labs/e13e14/prepare_project.py --out data/e13-a11-project-20261117-v2
    python3 labs/e13e14/prepare_upstream.py 学生发放包_20261116.zip
    python3 run_e11e12.py run --request data/e13-a11-project-20261117-v2/e11-a.json --out work/e13-a11-a-01
    python3 labs/e13e14/verify_evidence.py work/e13-a11-a-01
    python3 run_e11e12.py run --request data/e13-a11-project-20261117-v2/e12.json --out work/e13-a11-e12-01
    python3 labs/e13e14/verify_evidence.py work/e13-a11-e12-01

正式交换使用已发交接包中的bundle与固定SHA，不应重新运行prepare生成新的提交冒充同一轮输入。每次输出必须全新。H1/H2/H3逐一运行各自request-e12.json；失败保存原件，开缺陷Issue再复测。

四服务预检（不等于E13已通过或RC已验收）：

    export E14_ROOT="$PWD" E14_IMAGE=course-e11e12:241880439
    docker compose -f labs/e13e14/compose.yaml -p e14-241880439 config --quiet
    docker compose -f labs/e13e14/compose.yaml -p e14-241880439 up -d --wait
    python3 labs/e13e14/orchestrate.py --request data/e13-a11-project-20261117-v2/e12.json --out work/e14-a11-01
    python3 labs/e13e14/verify_evidence.py work/e14-a11-01
    docker compose -f labs/e13e14/compose.yaml -p e14-241880439 logs --no-color

扫描需分别覆盖源码/历史/镜像与本轮work日志；scan_runtime_logs退出2为未完成。只在隔离副本注入假Key、错误报告/补丁/超时；保存失败后用新目录重试。仅在本组约定范围内关闭该Compose项目，不停止Docker。

跨组API仍沿用E12异步jobs接口和SSH隧道；18081–18084为四角色编排接口，不是原jobs API的替换。无账号密码进入源码或交接包。

## B11 cJSON 四服务（#49 / PR #50）

需包含 #49 修复的源码。依赖检测仅 cJSON_Utils.o，功能另验证 make test。原始候选、bundle 与实验所有的 Dockerfile.broken 均放 data/，不覆盖上游文件；请求额外明确 profile：

    {
      "mode": "e12",
      "project_profile": "cjson",
      "repo": "/course/data/b11-e14-issue49/repo",
      "base": "cf0d87a095becada87336ed786f11070e9a037b5",
      "target": "f0c8fa4f812abe50964956cd0580ab963430ba35",
      "candidate": "/course/data/b11-e14-issue49/candidate.Dockerfile",
      "broken_dockerfile": "/course/data/b11-e14-issue49/Dockerfile.broken",
      "expected_output": "1",
      "build_timeout": 600
    }

原始请求和输入随本轮证据提供。先将 bundle 克隆到上述 repo 并核对两个完整 SHA，启动独立 Compose 项目，将请求保存到 data/ 后执行：

    python3 labs/e13e14/orchestrate.py --request data/b11-e14-issue49/request-e14.json --out work/e14-b11-cjson-new-01
    python3 labs/e13e14/verify_evidence.py work/e14-b11-cjson-new-01

本轮云端因 Docker Hub 不可达，仅对本次 DRAFT 使用同 digest 的 BuildKit source policy；source-policy.json、compose.mirror.yaml 和运行驱动随 evidence/E14-cJSON/ 中的原始 harness 提供。使用覆盖时按记录的容器路径放在独立仓库下，并给 compose 同时添加对应 -f；不改原候选或共享 daemon。不需覆盖的网络直接用基础 Compose。前后证据和原件哈希见 docs/evidence/e13-e14/E14-cJSON-issue49.md。

本阶段不能发布 v0.9-rc；先完成候选发布说明.md 的独立记录、审查合并和最终重跑。
