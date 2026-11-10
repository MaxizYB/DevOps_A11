# E11–E12 证据目录

原始运行目录使用被 .gitignore 忽略的 work/，建议按以下命名保存：

- work/e11-a-<student-id>-<timestamp>/：E11-A baseline/full/incremental、target full、日志和 result.json
- work/e12-api-<student-id>-<timestamp>/：服务 API 请求、轮询、artifact 清单和下载哈希
- work/e12-real-<student-id>-<timestamp>/：真实项目独立克隆、完整 SHA 和五阶段结果

可提交的说明文档必须记录：仓库来源、base/target 完整 SHA、configuration_id、schema_version、job_id、trace_id、产物 URI/SHA、命令、环境版本和实际结论。不要提交 token、.env、.git、大型 work 原始目录或实验包压缩包。

本目录不把课程生成 fixture 或组长的公共自检计为成员个人实验；成员个人结果需在各自 Issue/PR 中引用

组长的公共接入记录见 [environment-preparation-20261110.md](environment-preparation-20261110.md)。该记录区分了源码/契约校验、课程生成样例与尚未在本机完成的 Docker/服务器验证。
