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

## 2026-09-22：E2 EChecker 增量检测交接材料

- 工具/模型：Codex。
- 任务：根据 #3 整理 EChecker 的增量检测模块说明和交接证据，补充 `INCREMENTAL_CHECK` 的输入、baseline 校验、输出语义、依赖和待决问题。
- 提示摘要：要求依据接口契约、#3 说明和协作规范，在预期分支 `docs/3-echecker-incremental-check` 上完善模块 README 和证据文档。
- AI 建议：将 `project_root` 标记为待决字段，因为当前 E2 契约尚未包含该输入；引用已有有效/无效样例解释基线校验和变化报告，不实现服务代码。
- 人工采纳与限制：采纳文档结构和验证记录；交付范围限于 E2 模块交接材料，不实现 EChecker 服务、HTTP API 或最终共享 Schema；B 组产物读取能力和真实 C0/C1/C2 历史仍标记为待确认。
- 关联文件：`services/echecker/README.md`、`docs/evidence/e2-echecker-incremental-check.md`。
- 验证：运行 `git diff --check` 和 `conda run -n devops python scripts\validate_contract.py`，契约校验全部通过。
