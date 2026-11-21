# B11 同学：cJSON E13 第一次检测结果回传

我们是 A11。本包回应你们本次 `cjson-b-e13-handoff.tar.gz`，不是上午我们发给你们的 A11 项目包，也不是 E13/E14 最终提交包。对接统一由 A11 组长 241880439 负责。

## 本次输入与结果

- 收到输入包 SHA256：`7e8ece5d8dda4b2a04ea2f605fcafa31d1aca2c375c36d1cedf1d33fe09e8142`。
- base：`cf0d87a095becada87336ed786f11070e9a037b5`。
- target：`f0c8fa4f812abe50964956cd0580ab963430ba35`。
- 两提交可在完整历史 bundle 中解析，base 是 target 的祖先。target 只修改 `test.c`，新增整数边界解析测试；我们没有改动你们的项目输入、Makefile 或候选 Dockerfile。
- A11 检测代码：`ac5177910ee826bc5385da69b9cd464b7454d1f0`，不是 cJSON 的项目 SHA，也不是已合并发布版本。运行镜像 ID：`sha256:548752eeae6ae6ea598e0a5aa9e26874bb27c3065b22e554e800a6595b1e8d53`。可见内存约 3.54 GiB，隔离副本串行运行。
- job：`job-85e6c008fc4a433d813ebc18b675039d`；trace：`trace-d1af5a4997ff472485a7a46fba2b9bf7`。
- A 端状态为 `SUCCEEDED`，基线全量与目标增量两阶段完整，另做目标全量对照；45 项公开产物哈希均通过独立复核。
- base 和 target 的 `make test` 均通过。使用你们候选 CMD 的同等命令 `./cJSON_test >/dev/null && echo 1`，两版本均输出 `1`。原始可执行文件会输出示例文本，不能把它的原始 stdout 说成只有 `1`。候选 Dockerfile 原字节保留，本轮不替你们执行 DRAFT 或 MDFixer。

## 检测发现及范围

本轮使用已对接的 `cjson` 专用适配，构建/依赖检测目标是 **`make cJSON_Utils.o`**，不是整个 cJSON 的任意 Make/CMake 目标。`make test` 另外执行，验证包含你们新测试的 `cJSON_test`。

全量与增量都发现：`MISSING: cJSON_Utils.o -> cJSON.h`，没有发现本检测目标的 REDUNDANT。这是实际读取而 Makefile 漏声明的依赖，**不是 make test 失败，也不表示 A 检测执行失败**。base 与 target 中该问题均存在，本次只新增测试，没有消除此问题。

增量结果复用了 `cJSON_Utils.o` 的基线依赖（`reused` 为该目标、`refreshed` 为空），因为你们修改的是测试函数体，未改变本目标的编译命令、头文件和预处理依赖输入。我们另做 target 全量采集，发现与增量一致；不是把旧报告换一个 target 名字交回。

## 包里各文件是什么

- `evidence/A-result/`：**当次完整原始结果目录**，包括 request/result、full-check、incremental-check、基线缓存、两次全量图/Make 数据库/进程/strace、源代码快照及 Git 元数据，未裁剪、未改写报告。
- `evidence/` 其余文件：原始命令/退出码、环境/镜像、base/target 独立功能测试副本和 stdout/stderr、检测日志及 summary。
- `fixed-md.json`：由当次 `incremental-check.json` 校验后适配出的 B 端输入，保留来源 job/trace/URI/SHA。不是重新检测结果或伪造的修复报告。原件还在 `evidence/A-result/incremental-check.json`。
- `received/`：你们原始 tar.gz、bundle 和候选，便于核对收到的原字节。
- `verification.json`、`security/`、`SHA256SUMS.json`：产物复核、扫描原始命中与逐项判读、逐文件哈希。`USAGE.md`、`AI_USAGE.md`、分工记录与工具说明一并附上。

## 你们接下来做什么

1. 解压到新目录，不覆盖你们仓库。包根目录运行 `python3 verify_package.py`；再运行 `python3 verify_evidence.py evidence/A-result`。
2. 核对本次 target、job/trace，读取当次增量报告。若你们沿用 fixed-md 适配，使用包根的 `fixed-md.json`，读取 JSON **之前**校验其 SHA256：`3b77016dd7a243c11ed7e22b07f4b8c7a1a848727ce358685403576329136b72`。不要拿 E12 的旧 target 报告，也不要手改报告中的 SHA。
3. 在你们自己的 E11-B 实现/隔离工作副本中完成 DRAFT、报告消费、补丁生成、validation 和 recheck。运行请求中的项目 base/target 保持本次固定值；`fixed_report` 使用你们机器实际收到的路径，并传入上述 `fixed_report_sha256`。保留 `fixed-md-input.json/source_report` 或同等来源记录。具体路径适配你们自己的平台，不能直接照搬我们 `/course/...` 的绝对路径。
4. 回传**完整原始执行目录和日志**，以及请求、退出码、job/trace、源报告 SHA、补丁、validation 和 recheck、你们系统执行 SHA/镜像/CI。成功应有补丁被接受及 recheck 无 MISSING；失败也保留原件并反馈，不能修改原始报告凑通过。

你们仍需另行处理此前收到的 A11 项目交接包（A11 target `c2301112968b4cf185a94449e5dbc85764f4a2df`），本次 cJSON 回传不替代那个任务。我们也不把本次 A 端检测写成 B11 已消费、完整 C1 已通过或 E13 最终门禁通过。

## 扫描说明

原始整目录扫描退出码为 1，命中 24 处：全部是六个源码副本中 Unity 的两个 `testRunnerGenerator*.c` 测试样例，各含两个固定 `Postman-Token` 示例字符串。逐文件与 base/target 的 Git 原件比对一致，属于上游 HTTP 解析测试数据，不是本轮配置或发送的 A11/B11 凭据。

未删除这些源码、未覆盖原始扫描日志、未改低通用扫描规则。`security/review.json` 记录精确路径/行号/文件 SHA 和判读；实际日志/报告/trace 另外扫描。运行包装脚本因这个扫描命中返回 1，而 `evidence/commands.json` 中 **e11-a 命令退出 0**，`A-result/result.json` 为 SUCCEEDED；二者不能混淆。包不含服务器密码、私钥或真实服务令牌。
