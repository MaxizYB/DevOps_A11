# E11–E12 证据目录

原始运行目录使用被 .gitignore 忽略的 work/，建议按以下命名保存：

- work/e11-a-<student-id>-<timestamp>/：E11-A baseline/full/incremental、target full、日志和 result.json
- work/e12-api-<student-id>-<timestamp>/：服务 API 请求、轮询、artifact 清单和下载哈希
- work/e12-real-<student-id>-<timestamp>/：真实项目独立克隆、完整 SHA 和五阶段结果

可提交的说明文档必须记录：仓库来源、base/target 完整 SHA、configuration_id、schema_version、job_id、trace_id、产物 URI/SHA、命令、环境版本和实际结论。不要提交 token、.env、.git、大型 work 原始目录或实验包压缩包。

本目录不把课程生成 fixture 或组长的公共自检计为成员个人实验；成员个人结果需在各自 Issue/PR 中引用

组长的公共接入记录见 [environment-preparation-20261110.md](environment-preparation-20261110.md)。该记录区分了源码/契约校验、课程生成样例与尚未在本机完成的 Docker/服务器验证。

241880411 的 Issue #38 验证见 [个人报告](241880411/个人报告.md) 和 [运行摘要](241880411/run-summary.json)，包含真实 Docker E11-A、一致性核查与产物及 API 边界测试。

231880027 的 Issue #39 结果见 [独立测试记录](231880027-independent-tests.md)。

2026-11-14 组长云端收尾见 [个人报告](241880439/个人报告.md)、[ADR](241880439/ADR.md) 和 [数据清单](241880439/数据与联调记录.csv)。报告区分 A11 样例验收、参考 E11-B/E12 回放、待 B11 实际访问和真实项目验收；原始 work 证据随本地压缩包归档，不纳入 Git。
