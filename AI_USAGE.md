# AI 使用记录

## 2026-11-24：微服务公共接入与期末报告底稿（Refs #52）

- 使用者为 A11 组长 241880439 / MaxizYB，工具为 Codex。根据教师手册拆分 #52–#54，复用已有 E12 任务 API、E14 四角色与 A11 真项目。
- AI 辅助实现 Compose 覆盖配置、网关、有限重试、业务指标、取证客户端和测试，整理操作说明、组长验收证据及期末底稿。教师样例由教师提供，A11 配置探针复用上次已核验的原始两条提交与候选。
- Codex 驱动执行本地回归和 A11 云服务器复核。68 项 E11/E12、42 项 E13/E14、4 项网关测试通过。云端五阶段、EChecker 停机与恢复、可应用错误补丁拒绝及教师样例另有真实记录，见 [组长验收记录](docs/microservice/组长验收记录.md)。组员个人检查、评审与报告贡献按各自 PR 留存。

## 2026-11-18：E14 cJSON profile 修复（Refs #49、#43）

- 使用者：A11 组长 241880439 / MaxizYB；工具：Codex。用户要求继续完成当前能完成的 E13/E14 收尾。
- AI 辅助：检查四角色适配边界，修复 cJSON profile 转发、服务独立导入、专用 patch/validate、隔离快照 Dockerfile.broken 注入与来源哈希；加入跨 profile 报告拒绝和真实 GCC/Make/strace 回归。
- 本地验证：34 项 E13/E14 测试通过；真实工具回归使用合成小项目，不冒称 B11 cJSON 或个人独立成果。云端同 target 预检、故障/恢复和新提交 CI 将另行登记，当前不预填通过。
- 边界：保留用户原有 docs/e11-e12/B11联调交接.md 修改；不直接推送 main、不变更审批门槛、不代签 B11 回执或 #45 的独立记录、不发布未通过门禁的 RC。

## 2026-11-17 下午：B11 cJSON E13 当次全量/增量检测与回传（Refs #43、#45）

- 使用者：A11 组长 241880439 / MaxizYB；工具：Codex。用户要求先回应 B11 第一次交接，不等待 B11 完成此前 A11 项目包。
- 来源：原始 cjson-b-e13-handoff.tar.gz（SHA256 7e8ece5d8dda4b2a04ea2f605fcafa31d1aca2c375c36d1cedf1d33fe09e8142）；B11 项目 base cf0d87a095becada87336ed786f11070e9a037b5、target f0c8fa4f812abe50964956cd0580ab963430ba35。B11 新增 test.c 的整数边界测试，不冒称 A11 原创或成员个人成果。
- AI 辅助：核查 bundle/提交祖先与实际差异；编写可追溯的组长运行、完整原始证据打包工具和 B11 回传说明；在本组服务器串行运行两个版本 make test、候选 CMD 等价输出检查和 E11-A。
- 实测：job-85e6c008fc4a433d813ebc18b675039d，45 项产物哈希复核通过；全量/增量发现一致，cJSON_Utils.o 缺 cJSON.h；不将存在依赖问题写成程序测试失败，也不把 reused 说成目标文件未实际复核。
- 扫描：保留 raw 扫描命中退出 1；24 处均逐项核对为 base/target 未变的 Unity HTTP 测试样例固定 Postman 字段，另扫实际日志/报告。未修改原始报告、源码或通用扫描器以制造零命中。
- 限制：检测范围仅既有 cJSON_Utils.o 适配；本轮未构建 B11 候选镜像、运行 B 端修复、签收或完整正式 C1–C8，不代替成员独立验收。服务器输入和既有 E12 服务未改动；B11 报告消费回执与其测试 A11 项目仍待对方完成。

## 2026-11-17：E13/E14 公共准备与A11→B11交接（Refs #43）

- 使用者：241880439 / MaxizYB；工具：Codex。按用户确认的三人分工发布#43/#44/#45，组长统一发送/接收B11资料。
- 来源：学生发放包_20261116.zip的手册、课件、参考四服务/编排/交接/日志扫描与测试；原始字节哈希记录在docs/e13-e14/教学包来源.json。保留参考来源，不冒称从零实现。
- AI辅助：公共接入、接收端fixed_report_sha256检查、有限正数超时参数、A11配置探针项目的功能/边界测试和真实Git历史、云端参考预检及无凭据交接包。
- 验证和限制：具体命令/状态以docs/e13-e14/验证记录.md为准。公共预检不等同成员个人实测或B11独立消费；跨组正式矩阵、签收、评审合并和v0.9-rc发布仍为待完成项，不改保护规则或虚构Review。
- 项目选型：依据本轮手册允许课程样例经本组实际修改/测试/提交形成交换项目；如实说明当日新建维护历史及AI辅助，不声称长期维护上游。DRAFT候选是安装依赖方案的手工回放，本次不调用外部模型API。

## 2026-11-14：E11/E12 组长整合、云端参考回放与交付准备

- 使用者/工具：241880439 / MaxizYB，Codex。关联 #36、#38、#39 和收尾 PR #42。
- 用户请求：审阅成员成果，完成组长可执行工作，整理交付并明确 B11 与人工剩余事项。
- AI 辅助：保留个人提交整合 #40/#41、解决 AI_USAGE 追加冲突；开发 API 真实下载/哈希验证客户端及三项测试、固定摘要镜像源参数、证据汇总及打包工具；执行云端课程样例回放并生成个人报告、ADR、分工与 B11 交接。
- 实际验证：云端 35 项测试、E11-A 及 715 项独立核查、参考 E11-B、五阶段参考 E12、API 的 184 项检查通过。Docker Hub/包源失败与新数据集成功重试均留原始日志。
- 来源与限制：DRAFT 候选来自课程 prepare，未调用模型另行生成；课程生成 Git 样例不冒充真实项目，组长同机回放不冒充 B11 成果或分机确认。main 的既有他人批准门槛未修改。
- 人工仍需确认：B11 E11-B 原始证据与实际分机访问、真实 C/Make 项目及完整 base/target、收尾 PR 非最后推送者批准。AI 辅助审查以组长身份记录，不虚构独立人员评审。
- 证据：docs/evidence/e11-e12/241880439/、docs/e11-e12/；云端 work/leader-20261114/；本地被忽略的 work/e11-e12-final-20261114/collected/。

本文件记录影响课程设计、源码或交付材料的 AI 辅助工作。每项记录须说明人工判断和验证结果，不能把 AI 输出直接视为已验证结论。

## 2026-11-18：B11 E13 交付包复核与成员成果整合

- 使用者：A11 组长 241880439 / MaxizYB；工具：Codex。用户要求在收到 B11-E13-handoff-20261118.tar.gz 后先完成可完成的整合工作。
- AI 辅助：读取并解包 B11 交付材料；逐个核对 result/request/recheck/validation JSON；重算 artifact URI 对应文件的 SHA-256 和字节数；核对 base/target、阶段顺序、C2–C8 与 H1–H3 语义；编写 B11 独立核验记录并更新 E13 分工、交叉测试和验证记录。
- 成员成果：将 PR #48 对应分支在本地整合到 E13/E14 集成分支，纳入 241880411 的个人证据和测试改动；运行 py_compile 与 labs/e13e14 的 21 项单测通过。远程 GitHub 随后将 PR #48 标记为已合并，合并提交为 `55e60ca391ec60dcc723284102c856c6dedff44c`；不把该远程状态扩写为 B11 签收或成员以外的 Review。
- 人工判断与限制：PR #48 的历史 run #12 曾因 Docker Hub 拉取 python:3.13-slim 返回 HTTP 500 失败；合并提交对应的 E13-E14 integration gate run #14 已成功。B11 交付目录的 96 个扫描命中属于已核对的上游 Unity 固定 Postman 示例，未被改写成零命中。E13 最终门禁、B11 正式签收、#45 独立记录、PR #47 最终合并和 v0.9-rc 仍待完成。

## 2026-11-11：E11-A 个人验证辅助（241880411）

- 工具：Codex；关联任务：Issue #38。
- AI 辅助：梳理要求，补充独立集合核查、产物与 HTTP 边界测试，修正基线日志 commit 归属，并协助实验验证和材料整理。
- 验证：本地 Docker 的 E11/E12 25 项测试通过，真实 E11-A 和个人独立核查通过。
- 个人记录：[报告与 AI 使用说明](docs/evidence/e11-e12/241880411/AI_USAGE.md)。

## 2026-11-12：E11-A 个人验证（231880027，Refs #39）

- 工具/模型：Codex GPT-6.1Sol。
- 任务：辅助编写 #39 的个人测试、复现脚本和证据摘要。
- AI 建议：设置共享头文件和函数体变化场景，固定预期并校验报告提交与哈希。
- 人工采纳与限制：采用个人测试和消费验证，复用课程参考实现；人工评审待完成。
- 关联文件：`scripts/e11e12/`、个人测试文件及 [实验摘要](docs/evidence/e11-e12/231880027-independent-tests.md)。
- 验证：21 项测试、25 项回归测试通过；刷新、复用及三类拒绝符合预期，`git diff --check` 通过。

## 2026-11-03：E8–E10任务发布与公共环境接入（Refs #29）

- 工具：Codex；具体模型版本未记录，不猜测版本。
- 用户要求：按讨论方案发布三人任务并准备公共环境，成员个人实验和扩展仍由本人完成。组长另明确同意现有约3.54GiB主机无法扩容，按实际资源试跑并记录差异。
- 来源：`DevOps_E8_E10_20261031.zip` 的公共准备、A轨道三份手册、提交与个人测试说明、实验包和空白模板。选择性接入参考实现、新workflow、版本化helper和模板，保留原E2–E7，不把参考代码称作本人从零实现。
- 本次修改边界：Issue #29/#30/#31、独立 `labs/e8e10/`、`run_lab.py`、`scripts/e8e10/`、分支命名例外、操作/证据说明；不代写成员个人报告、实现或认证，不继承上次审批例外。
- 验证：本地参考7项、原服务26项、E2/E3校验及密钥检查通过；ECS三学号镜像串行构建、各7项参考测试及lab_ready通过，组长另完成A三入口公共smoke、E10共30行一致。初始SHA两条CI均通过；版本、SHA、image ID和边界见 `docs/evidence/e8-e10/environment-preparation-20261103.md`，不把公共自检算作成员个人实验。真实work、材料ZIP、安装包、镜像和认证不进入Git。

## 2026-10-23：E5–E7 评审、合并与最终交付（Refs #20、#22）

- 工具：Codex，具体模型版本未记录；不伪造完整对话或模型版本。
- 任务：重新核对 E5–E7 PPT、A 轨道指南、验收清单及报告/CSV 模板，实际审阅 PR #26/#27，协作完成 #28 的失败、拒绝和恢复，整理报告、分工和可提交的证据包。
- 采纳：保留教学参考来源与 E2–E4；独立检出成员分支测试，最终集成源码本地 26 passed；对失败 PR 实际尝试普通合并并保存 exit=1，随后仅恢复错误测试预期；ECS 在最终 main SHA 上另建克隆重建并重跑，命令和实际结果进入被忽略的原始证据。
- 授权与限制：组长明确授权本次审批例外；只临时调整审批，必需 CI、strict 与管理员约束始终保留，操作后恢复常态配置。不冒充两位成员完成个人 Review，不把失败演示算作算法修复，不把历史或助教记录冒充最终 main 运行。
- 关联文件：`docs/实验报告.md`、`docs/AI使用说明.md`、`docs/分工与完成记录.md`、`docs/验收记录.csv`、`docs/backlog/e5-e7-backlog.md`；原始证据在 `work/e5-e7-final-20261023/`，ZIP 在仓库根目录且不纳入 Git。

## 2026-10-22：E6 BuildChecker 验证辅助

- 工具/模型：Codex。
- 任务：辅助完成 Issue #21 的代码审阅、边界修复、测试补充和实验记录整理。
- AI 建议：辅助分析 Make 工作目录与符号链接的处理边界，补充回归测试，并核对 MD/RD 结果、输入哈希和原始证据。
- 人工采纳与限制：依据课程参考实现和实际运行结果整理材料；人工评审待完成，结论限于当前教学样例和构建配置。
- 关联文件：`services/buildchecker/buildchecker/fullcheck.py`、`services/buildchecker/tests/test_fullcheck.py`、`docs/evidence/e6/`。
- 验证：ECS 服务测试 19 项、独立判定测试 6 项、门禁 8 项通过；原始精确两条 MD/RD，修复后为空，仅 Makefile 输入哈希改变。详见 [E6 验证记录](docs/evidence/e6/issue-21-validation.md)。

## 2026-10-20：E5–E7 A 轨道公共基础接入

- 工具/模型：Codex。
- 任务：依据 E5–E7 教学包，将 A-buildchecker 的 E6 全量检测、E7 门禁和云端实验入口接入已有 E2–E4 仓库，并为 #20 准备可供成员并行开发的公共版本。
- AI 建议：保留 E4 环境入口，新增 `scripts/lab_cloud.py`；复用教学包的可审计 `fullcheck.py`、真实故障 oracle、CI artifact 流程；按学号隔离镜像和 `work/` 证据目录。
- 人工采纳与限制：保留当前 E2–E4 契约和 Git 历史；仅导入 A 轨道代码，不导入 B 轨道或 EChecker 生产实现；修正参考入口的默认镜像名和 doctor 证据输出；将 doctor 的最低内存与既有 E4 ECS 门槛统一为 3.5 GiB（实际服务器为 3.5 GiB，仍低于推荐值）；增加 E4 CLI 兼容的 `opened_header` 辅助函数。论文级完整基准不在本阶段声明完成。
- 关联文件：`services/buildchecker/buildchecker/fullcheck.py`、`services/buildchecker/buildchecker/smoke.py`、`scripts/lab_cloud.py`、`scripts/run_e7_a_gate.py`、`tests/e7/`、`.github/workflows/e7-quality-gate.yml`、`docs/evidence/e5/`、`docs/evidence/e6/`、`docs/evidence/e7/`。
- 验证：本地 `python3 -m compileall`、`PYTHONPATH=.:services/buildchecker pytest -q services/buildchecker/tests tests/e7`（21 passed）；ECS Docker 构建、E5 原始证据和完整门禁已完成，实际路径和结果记录于 `docs/evidence/e5-e7-20261020-leader-run.md`，不以本地结果替代云端结论。

## 2026-10-20：E7 自主测试、镜像配置与验证（Refs #22）

- 工具/模型：Codex。
- 提示摘要：补充 E7 自主边界测试，将测试及依赖脚本打包进镜像，执行验证并整理统一的结果与证据说明。
- AI 建议与采纳：新增少一条、多一条、重复一条发现的拒绝测试；Dockerfile 仅增加两条 COPY，打包 tests/e7/ 和 scripts/run_e7_a_gate.py。未修改检测算法、服务测试、门禁预期或依赖。
- 关联文件：tests/e7/test_e7_a_gate.py、services/buildchecker/Dockerfile、docs/evidence/e7/README.md、docs/evidence/e7/e7-20261020-test-cloud-validation.md 和本记录。
- 来源与版本：参考检测器、门禁和既有测试来自公共基础提交 41cc04da58911a8017fc2838471e15e7df5b95ef。实际构建使用 9898fdd8daf35ba4b5e7cd6dbc241361794d6263 加证据保存的未提交 Dockerfile 补丁；该 SHA 单独不包含本次配置修改。
- 实际验证：Codex 经 SSH 构建镜像，退出 0；pytest 22 passed（15 项服务＋7 项判定）；无宿主挂载容器内 unittest 7 个方法通过，新增方法含 3 个子场景；测试文件与依赖脚本哈希同宿主；八项门禁全部通过且退出 0；证据校验退出 0，仅 Makefile 输入哈希改变；9 个记录容器已移除，实际工具版本已保存。差异检查通过。
- 证据：/root/231880027/DevOps_A11/work/e7-validation-231880027-20261020-151352/；镜像 ID sha256:ce5413913ee0d4d6b30ad74ab5dec02f5bf05ff7a3d2dc19ddde21be46842e4f，构建与门禁记录一致。
- 整理：统一文档版本与证据目录名称，核对重命名前后全部文件内容不变；原始命令日志保留运行时路径。work 不纳入 Git，成果需组员评审。

## 2026-10-06：E4 服务器 smoke 权限失败修复

- 工具/模型：Codex。
- 任务：处理 ECS `make all` 在执行临时 `app` 时出现的 `PermissionError`，关联 Issue #18。
- 依据与实现：用户提供的日志显示构建、测试均通过；在独立挂载命名空间复现 `/tmp` tmpfs 的 `noexec` 行为后，显式添加 `exec`，保留 `nosuid`、`nodev`、非 root 和只读根文件系统。CLI 将执行权限错误写成 JSON，编排脚本同时指出标准输出和错误日志。
- 相关修正：补齐本地 pytest 导入路径；扫描工作区时排除未跟踪且被忽略的课件/压缩包；区分源码中的私钥头示例与实际 PEM 行，并继续扫描 Git 历史和解码后的镜像环境变量。
- 验证：挂载 `noexec` 的原实现复现同样错误，修复后提供 JSON 诊断；挂载 `exec` 的 smoke 输出 `1`、成功打开 `config.h` 且通过。回归测试、工作区/Git 历史扫描、契约校验和 Compose 配置解析通过。开发机 Docker daemon 不可用，完整 ECS `make all` 由组长重跑确认。

## 2026-09-29：E4 A 组可重复工程环境骨架

- 工具/模型：Codex。
- 任务：在教师实验包尚未取得时，依据 E4 课件和 A 组命令手册，在本仓库建立 BuildChecker 工程环境骨架；实验包取得后进行差异复核。
- AI 建议：保留 E2/E3 目录，新增固定 digest Dockerfile、Compose 资源限制、带哈希依赖锁、`make all` 编排、`version/smoke` CLI、单元测试和脱敏密钥扫描，并吸收实验包中的模块入口、工具链记录、超时和项目隔离约定。
- 人工采纳与限制：保留现有 E3 fixture 文本以维持基线，只采纳兼容的工程改进；没有把 smoke 结果表述为 BuildChecker 算法结果。由于当前开发机没有 Docker daemon，镜像构建、容器测试、镜像扫描和两名 ECS 组员复跑仍须在服务器验证。
- 关联文件：`Dockerfile`、`compose.yaml`、`Makefile`、`scripts/e4/`、`services/buildchecker/buildchecker/`、`docs/evidence/e4/`、`docs/adr/0003-e4-reproducible-buildchecker-environment.md`。
- 验证：Python 单测 `5 passed`；本机 `strace` smoke 通过；E2 契约校验、Python 编译、Compose 配置解析和 `git diff --check` 通过。

## 2026-09-20：E2 初始协作框架

- 工具/模型：Codex
- 任务：根据 E2 课件建立本仓库的协作规范、Issue/PR 模板和非实现性目录骨架。
- 提示摘要：要求以 Issue 驱动后续任务；组长负责契约、框架、合并和统计；另外两项工作分别留给 BuildChecker 与 EChecker 负责人；本次不得实现服务或编写接口契约。
- AI 建议：采用带课程阶段和模块的 Issue 标题，使用带 Issue 编号的工作分支，并为契约、两项检测、ADR 和证据保留独立目录。
- 人工采纳与限制：采纳目录与协作流程；明确排除 Schema、JSON 契约、接口样例和业务实现，契约由组长在后续独立 Issue 中决定。
- 关联文件：`README.md`、`docs/A11组协作规范.md`、`.github/`、`contracts/`、`services/`、`docs/adr/`、`docs/evidence/`。
- 验证：检查目录边界与模板内容，并运行 `git diff --check`；尚未运行服务测试，因为本次没有可执行实现。

## 2026-09-21：E2 契约落库与样例校验

- 工具/模型：Codex。
- 任务：将组长提供的 E2 接口契约草稿整理为版本化仓库文件，并补齐 Schema、示例、ADR、Backlog、交接检查记录和校验脚本。
- 提示摘要：以用户提供的草稿为准完成 #1，推送并合并；不改写已确定的字段语义或实现服务。
- AI 建议：用机器可读 Schema 和无外部依赖的校验脚本验证四类任务、未知 `job_type`、缺少 baseline 和 baseline 不匹配；将 B11 尚未确认的互读状态如实记录。
- 人工采纳与限制：契约字段、错误码、状态和 URI 规则来自用户草稿；新增文件只为使 E2 交付物可验证和可追溯。未声称 B11 已完成互读验收。
- 关联文件：`contracts/`、`docs/adr/0001-e2-async-job-artifact-contract.md`、`docs/backlog/e2-backlog.md`、`docs/evidence/e2-pair-review.md`。
- 验证：运行 `python3 scripts/validate_contract.py`，并将结果写入 E2 验证记录。

## 2026-09-22：E3 基线治理框架

- 工具/模型：Codex。
- 任务：在 #5 中建立 E3 的 fixture/work/evidence 目录边界、环境记录、证据模板、任务模板和校验工具。
- 提示摘要：先完成组长不依赖成员样例的工作；MD/RD 样例和 C0/C1/C2 历史仍由 #6、#7 分别完成。
- AI 建议：将版本化源码、可再生本地运行目录和可提交证据分开；用标准库脚本记录课程要求的系统与工具版本，并验证框架完整性。
- 人工采纳与限制：E3 任务边界和必需证据来自课程课件及 #5/#6/#7；未生成 #6 的源码/Oracle，也未生成 #7 的 Git 历史、SHA 或行为结果。
- 关联文件：`fixtures/e3/`、`work/e3/`、`docs/evidence/e3/`、`docs/backlog/e3-backlog.md`、`docs/adr/0002-e3-baseline-evidence-layout.md`、`scripts/e3/`。
- 验证：运行环境采集、`python3 scripts/e3/validate_e3_framework.py`、Python 编译和 `git diff --check`。

## 2026-09-23：E2 BuildChecker 交接材料

- 工具/模型：Codex。
- 任务：参与整理 BuildChecker E2 交接文档、README 和产物样例。
- 提示摘要：按照 Issue #2 和现有 E2 公共契约补齐 BuildChecker 专有交接材料，不实现检测器，不修改公共契约和共享 Schema。
- AI 建议：用同一 commit 和 `configuration_id` 编写实际依赖图、声明依赖图和错误报告样例，并说明 MD/RD 差集、下游读取方式和失败行为。
- 人工采纳与限制：采纳文档结构和产物样例；样例明确标记为 `CONTRACT_EXAMPLE`，不使用伪造的 PID、系统调用、时间戳或真实运行日志。
- 关联文件：`docs/evidence/e2-buildchecker-handoff.md`、`services/buildchecker/README.md`、`services/buildchecker/examples/`。
- 验证：运行 `python3 scripts/validate_contract.py`、三份 JSON 格式检查和 `git diff --check`。

## 2026-09-24：E3 EChecker C0/C1/C2 基线

- 工具/模型：Codex。
- 任务：根据 #7 准备 EChecker 的 C0/C1/C2 Git 历史 fixture、人工 Oracle、命令证据和实际观察摘要。
- 提示摘要：要求 C0 clean 输出 10，C1 新增 `feature.h` 但漏写 Makefile 依赖且 clean 输出 12，C2 只改编译命令并记录增量输出 12 与 clean 输出 19；遵循 #5 的 fixture/work/evidence 目录约定。
- AI 建议：用版本化快照和生成脚本在 `work/e3/` 创建真实 Git 历史；将原始运行仓库和日志留在 ignored 的工作目录，将 SHA、Oracle、命令和观察摘要提交到 `docs/evidence/e3/echecker/`。
- 人工采纳与限制：采纳最小 C/Make 样例和证据结构；不实现 EChecker 算法、服务端 API 或 BuildChecker 全量样例；最终证据切换为用户在 Ubuntu 22.04/GCC 11 环境中的 Linux 复现结果。
- 关联文件：`fixtures/e3/echecker-history/`、`docs/evidence/e3/echecker/`。
- 验证：运行 `conda run -n devops python fixtures\e3\echecker-history\create_history.py`、`conda run -n devops python scripts\e3\validate_e3_framework.py`、JSON 格式检查和 `git diff --check`。

## 2026-09-25：E2/E3 最终复现与收尾

- 工具/模型：Codex。
- 任务：审阅成员 PR，解决 EChecker 分支冲突，完成 E3 两项基线的收尾复现，并整理最终验收记录。
- AI 建议：让 C0/C1/C2 生成脚本每次创建新的 UTC 运行目录；修正 C2 快照，使其相对 C1 只修改编译命令；将最终 SHA、环境和四组行为写入收尾证据。
- 人工采纳与限制：采纳可重复运行目录和严格 C2 变更边界；没有把基线行为误写成 BuildChecker/EChecker 算法已经实现，也没有代替 B11 完成 E2-04 互读确认。
- 关联文件：`fixtures/e3/echecker-history/create_history.py`、`fixtures/e3/echecker-history/snapshots/C2/README.md`、`docs/evidence/e3/final-acceptance.md`、`docs/backlog/e3-backlog.md`。
- 验证：收尾生成脚本得到 C0/C1/C2 行为 `10 / 12 / 12 / 19`；E3 框架、E2 契约、Python 编译、JSON 和 `git diff --check` 均通过。

- 契约收尾决策：将 Issue #3 提到的 `project_root` 正式加入 `INCREMENTAL_CHECK` 输入，并同步更新契约文档、两个 Schema、样例、校验器和 EChecker 交接材料。该字段在 E2 尚未有服务消费者前完成最终化；若已有外部消费者再采用新增必填字段，需按版本规则提升主版本并经双方确认。

## 2026-09-22：E2 EChecker 增量检测交接材料

- 工具/模型：Codex。
- 任务：根据 #3 整理 EChecker 的增量检测模块说明和交接证据，补充 `INCREMENTAL_CHECK` 的输入、baseline 校验、输出语义、依赖和待决问题。
- 提示摘要：要求依据接口契约、#3 说明和协作规范，在预期分支 `docs/3-echecker-incremental-check` 上完善模块 README 和证据文档。
- AI 建议：将 `project_root` 标记为待决字段，因为当前 E2 契约尚未包含该输入；引用已有有效/无效样例解释基线校验和变化报告，不实现服务代码。
- 人工采纳与限制：采纳文档结构和验证记录；交付范围限于 E2 模块交接材料，不实现 EChecker 服务、HTTP API 或最终共享 Schema；B 组产物读取能力和真实 C0/C1/C2 历史仍标记为待确认。
- 关联文件：`services/echecker/README.md`、`docs/evidence/e2-echecker-incremental-check.md`。
- 验证：运行 `git diff --check` 和 `python3 scripts/validate_contract.py`，契约校验全部通过。

## 2026-09-24：E3 BuildChecker MD/RD 测试基线

- 工具/模型：Codex。
- 任务：补充 Issue #6 的 MD/RD 测试样例、人工 Oracle 和实验记录，并整理相关文档。
- 提示摘要：用最小 GNU Make 项目在同一个 `main.o` 中构造 `config.h` 的缺失依赖和 `unused.h` 的冗余依赖；在 `work/e3/` 副本中完成四步实验，不直接修改 fixture。
- AI 建议：将 `main.o -> config.h` 记为 MISSING、`main.o -> unused.h` 记为 REDUNDANT，并分别保存人工 Oracle、运行日志和观察记录。
- 人工采纳与限制：已检查 Makefile 的依赖关系及四步实验结果。修改 `config.h` 后普通 `make` 未重编译，clean build 后输出更新；修改 `unused.h` 后触发额外重编译。本阶段未实现或运行真正的 BuildChecker；fixture 源码提交 SHA 已记录，PR 和组员复现结果留待后续 Review。
- 关联文件：`fixtures/e3/md-rd/`、`docs/evidence/e3/buildchecker/`、`docs/evidence/e3/environment/local-2026-09-24.json`；原始记录位于 `work/e3/20260924T021234Z-issue-6-md-rd/`。
- 验证：运行四步 Make 实验，并执行 `python3 scripts/e3/validate_e3_framework.py`、JSON 格式检查和 `git diff --check`。

## 2026-11-10：E11/E12 A11 公共准备

- 工具/模型：Codex（gpt-6.1-sol）。
- 任务：在 Issue #36 中接入 A11 的 E11-A 公共环境、E12 编排骨架、异步服务入口、契约校验、CI、操作文档和成员任务边界。
- AI 建议：保留 E2 1.0.0 契约，把 E11/E12 作为编排层；将 data/ 与 work/ 作为本地可再生目录；把 B11 实现和真实跨组联调留给后续；对 E11-A 强制基线全量图、增量报告和目标全量结果对照。
- 人工采纳与限制：采纳公共目录、路径约束、幂等冲突、服务重启失败标记和 SSH 回环访问方案；没有把编排父任务伪装成 E2 四类组件 Job，也没有把 E12 联调写成已完成。本机 Docker daemon 不可用，因此不宣称容器构建、服务启动或云端实验通过。
- 关联文件：run_e11e12.py、labs/e11e12/、contracts/e11-e12-orchestration.md、contracts/schemas/e12-orchestration-request.schema.json、.github/workflows/e11e12-a.yml、docs/e11-e12/、docs/backlog/e11-e12-backlog.md。
- 修正：修复 E11-A 执行后误进入 E11-B 固定报告分支；让全量检测使用请求超时；修复 E2 校验器只检查两份 E2 Schema 时被 E12 Schema 干扰的问题；补充 E11-A 流程和服务重启状态测试。
- 验证：python3 scripts/validate_contract.py、python3 scripts/validate_e11e12_contract.py、14 项 labs/e11e12 单元测试、Python 编译和 git diff --check 均通过。

## 2026-11-15：B11 cJSON 交接接入与云端联调准备

- 工具：Codex。操作者/整理者：A11 组长 241880439。
- 用户要求：以现有 cJSON 上游历史缺陷为真实开源样例，接入 B11 交接、完成 A11 修改和部署，并说明双方下一轮操作与最终材料归属。
- AI 辅助：审计 B11 源码和原始清单；保留 A11 编排/路径/报告边界，迁入 cJSON 专用适配和测试；补充编译命令一致的依赖缓存、报告衔接校验、部署指纹、离线数据准备和不含密码的新版客户端打包。
- 来源：B11 7b45b9c04686f3aefe861bb1d8a17aa63c969f23；DaveGamble/cJSON base 359567fdde253f311545a6c80b0fa6fb62e8ff09、target cf0d87a095becada87336ed786f11070e9a037b5。候选为 B11 记录候选加明确记录的镜像/包源调整，不声称本轮调用模型生成候选。
- 实际验证：本地单元/契约测试、云端五阶段和 API 自验；准确命令、结果与未完成项见 docs/e11-e12/cJSON接入与验证记录.md 和归档原始证据。失败目录保留，选题不虚构为本组长期维护。
- 边界：组长自验不代替 B11 独立运行；B11 个人报告、ADR 与 Review 不代签；不修改 main 分支保护，也不把 AI 检查冒充非作者批准。

## 2026-11-15 晚：正式联调核验与最终交付

- 工具：Codex；A11 组长 241880439 负责整理/复核。
- 用户要求：B11 已回传 B11_cJSON正式联调.zip，核验后给出最终交付材料。
- AI 辅助：对回传 ZIP 做数据安全检查，复核 210 项客户端结果、部署/项目/请求/幂等信息；从云服务器取回同一个 job-80afbdd237724fd19cb49db9ec23b147 的原始记录，独立核对 89 个下载和服务器字节、五阶段、缓存和本轮修复输入，228 项审计通过。
- 新增审计工具与归档安全测试，更新报告/ADR 引用、数据清单与分工记录；按 E11-A 和 E12 分别整理源码、个人/AI 材料、原始结果、GitHub 追溯和逐文件 SHA256。
- 原件与限制：保留 B11 自己提交的报告、ADR、操作者声明与交接缺文档的备注，不冒签；历史失败/待办原件不改。技术链路完成，但 cJSON 第三方选题、3.54 GiB 内存偏差和 GitHub 实际审批合并状态仍如实单列。
- 验证证据：包内 peer-audit/audit.json、服务器状态和原始结果、最终测试日志、GitHub 实际快照及 SHA256SUMS.json。源码快照、部署源码、上游 cJSON 提交各自标注，ZIP/data/work 不进入 Git。

## 2026-11-19：E13/E14 配对项目独立验证（231880027，Refs #45）

- 工具：Codex。
- 任务：辅助编写个人检测、HTTP 幂等实验、关联核查脚本与说明。
- AI 建议：预先固定 cJSON 依赖预期；验证旧报告、哈希、任务隔离和真实 HTTP 409；记录修复请求原文。
- 人工采纳与限制：复用公共代码，个人只新增测试/脚本/记录；未联系 B11、修改公共编排、提交或推送，人工审阅待完成。
- 关联文件：`scripts/e13e14/`、`labs/e13e14/tests/test_peer.py`、[个人记录](docs/evidence/e13-e14/231880027/peer-consistency.md)。
- 验证：68 项 E11/E12、42 项 E13/E14（含个人 8 项）和两套契约通过；C1 A端/C2/C3/C7/C8 实测通过；独立核查组长 E14 的 1659 项产物。五阶段、1665 项产物和实际修复请求关联核查通过，失败原件保留；B11 新报告消费、合并后复验、CI/评审待完成。

## 2026-11-24：微服务样例观测（231880027，Refs #53）

- 工具：Codex。
- 任务：辅助独立部署教师 API/Worker 样例，采集 Prometheus、Grafana 和同任务日志。
- AI 建议：隔离 Compose 与回环端口，保留正常/停机/恢复及受控超时的真实采样和任务证据。
- 人工采纳与限制：沿用教师业务代码与面板；修复上传目录权限；未修改公共业务或操作组员服务，未提交或推送；人工审阅待完成。
- 关联文件：`labs/observability/sample/`、[个人阶段 1 记录](docs/evidence/microservice/231880027/sample-validation.md)。
- 验证：四场景符合预期、同键重复无新任务、正常与恢复跨服务日志一致，UP/DOWN/UP 与实际业务指标可核对；本轮仅教师样例，A11 正式采样待后续完成。

## 2026-11-24：A11 业务监控接入、独立业务三阶段观测（231880027，Refs #53）

- 工具：Codex。
- 任务：辅助配置个人 Prometheus/Grafana，抓取公共 API/EChecker 的真实指标并关联正常任务日志；辅助部署隔离的个人业务与监控栈，执行正常、EChecker 停机和恢复观测。
- AI 建议：以 external 网络独立接入，区分历史计数与本轮增量，耗时按 sum/count 的 rate 计算；以源码快照和输入副本隔离 data/work，记录 counter 重置、真实错误及同任务日志，保留统一时间窗截图。
- 人工采纳与限制：未改公共业务代码、未停止或重启公共服务，未执行 #54 故障窗口；未改公共业务、未操作组员服务或执行 #54 回滚；仅停止并恢复个人 EChecker。
- 关联文件：`labs/observability/a11/`、[sample](docs/evidence/microservice/231880027/a11-observability.md)；`labs/observability/independent/`、[独立观测记录](docs/evidence/microservice/231880027/independent-validation.md)。
- 验证：两个抓取目标 UP、数据源 OK、5 个面板有真实数据；正常任务成功且 7 个公开产物通过校验，API/EChecker 成功计数各增 1，同 job/trace 日志一致；正式故障/恢复采样待协调；正常/恢复成功，各校验 7 项公开产物；停机任务按预期 FAILED/3 次尝试；实际 UP/DOWN/UP、API 成功 2/失败 1、EChecker 计数重置及日志关联通过，输入和公共容器前后不变；#54 后续复测与协作确认另行记录。
