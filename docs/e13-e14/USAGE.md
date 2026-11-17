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
