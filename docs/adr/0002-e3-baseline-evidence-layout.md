# ADR-0002：E3 分离版本化 Fixture、本地 Work 与可提交证据

- 状态：Accepted
- 日期：2026-09-22
- 关联 Issue：#5

## 背景

E3 要求保存可供后续检测器使用的测试项目、真实 Git 提交、环境、命令、预期结果和实际观察。将源码、嵌套 Git 仓库、编译产物和临时日志混在一起会导致版本不可追溯、PR 噪声过大，且容易把人工 Oracle 与工具结果混淆。

## 决策

- `fixtures/e3/` 只保存可版本控制的人工样例、源码快照、生成脚本和说明。
- `work/e3/` 保存每次运行的真实 clone、嵌套 Git 历史、编译产物和原始日志；除说明文件外默认忽略。
- `docs/evidence/e3/` 保存可提交的运行摘要：固定版本、环境清单、命令、退出码、关键输出、Oracle、实际观察和失败原因。
- 使用 `scripts/e3/capture_environment.py` 生成环境清单，并使用 `scripts/e3/validate_e3_framework.py` 检查基础布局和清单结构。
- C0/C1/C2 历史以版本化快照或生成脚本定义，在 `work/e3/` 生成真实 Git 仓库；实际 SHA 写入证据，而不是提交嵌套 `.git/` 目录。

## 备选方案

- 将所有日志和构建产物提交到 fixture：证据直观，但会引入机器相关文件、二进制和频繁覆盖。
- 只保留 README 和截图：体积小，但无法验证命令、SHA、时间戳行为和失败原因。
- 将 fixture 作为 Git submodule：可以保留历史，但会增加课程协作与克隆成本，且不适合最小人工样例。

## 后果

- 成员必须将每次运行写入新的 `work/e3/<run-id>/` 目录，并把需要提交的摘要转录到 `docs/evidence/e3/`。
- 原始日志不自动提交；出现争议或无法复现时，负责人须在 Issue/PR 说明其位置、平台和保留方式。
- #5 负责检查目录规则；#6 与 #7 负责在各自交付物中遵守规则。

## 验证

运行：

```bash
python3 scripts/e3/capture_environment.py --output docs/evidence/e3/environment/local-YYYY-MM-DD.json
python3 scripts/e3/validate_e3_framework.py
```

并在干净副本审阅 fixture、work 和 evidence 的职责是否混淆。
