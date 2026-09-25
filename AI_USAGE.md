# AI 使用记录

本文件记录影响课程设计、源码或交付材料的 AI 辅助工作。每项记录须说明人工判断和验证结果，不能把 AI 输出直接视为已验证结论。

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
