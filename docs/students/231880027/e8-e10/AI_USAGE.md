# AI使用记录

## E8
工具/模型/日期：Codex AI；GPT-6.1 Sol；2026-11-03。
输入上下文与问题：Issue #30 相关阶段拆分、E8 A 手册、参考 lab.py/test_profile.py、模板及真实 ECS 环境；用户授权完成阶段1 E8、容器测试与样例内部 Git，不外层 commit/push 或修改 GitHub。
模型建议：真实 BuildChecker 对象图建立历史基线，未变化时验证复用；新增 config.h 间接 include 的自主测试，固定完整图/发现及 added/resolved，保留全量对照。
采纳/拒绝及理由：采用最小测试扩展；保留原 7 项测试和参考算法。E8 阶段未实施目标级缓存优化、后续 E9/E10 或公共 workflow/环境修改，避免扩大范围。
人工修改：本轮所列测试与文档由 AI 实际编辑，不记作人工手写；尚无人工署名审核记录。AI 编辑了 test_profile.py 中新增的 Student231880027E8Tests，以及个人报告/ADR/本记录，并执行 Docker、采证和样例内部提交。
来源与个人贡献边界：lab.py、环境和原 7 项测试来自 DevOps_E8_E10_20261031 参考包。新增输入思路与参考个人测试示例中的“头文件 include 失效”相关，本次扩充为完整 actual/declared/findings/added/resolved 与全量独立固定预期断言，并保存本人的真实持久运行证据。
实际验证命令/输入/结果：
- 容器 unittest discover：8 项 OK，退出0。
- E8 fixture → GCC baseline → 真实 BuildChecker 对象图基线 → 未变化复用：均退出0；报告 SUCCEEDED/build_exit_code=0，精确一MD一RD。
- 自主 config.h include extra.h：增量/全量分别满足固定完整预期，新增MD extra.h；两个目标保守刷新；退出0。
- 程序输出：第一次误用 project/app 退出127；定位 buildchecker/project/app 后输出1、退出0。保留 steps/06 和 06b，不把路径错误算作预期故障。
- 第一次恢复助手遗漏 step 函数，NameError 在自主场景开始前发生；后续仅补未执行步骤，完整说明见 helper-issues.md。
- 标准输入前后 SHA256 相同；源码补丁、工具版本、trace/进程归属、内部 Git 日志/bundle 已留存。
证据：/root/231880027/DevOps_A11-e8-e10/work/e8-A-manual.8YSjkh。
源码身份：基础 5cef53474d1987e432933a6010b9b18f24ecf29e + 未提交 test_profile.py 补丁 source.patch。

## E9

工具/模型/日期：Codex AI；GPT-6.1 Sol；2026-11-03。
输入上下文与问题：允许容器测试、样例内部 Git，依据 E9 A 手册和当前 scan 源码。
模型建议：不改算法，新增宏配置双向开关自主测试；把“Make 实际重编”和“依赖图复用”分开保存，按手册保留 C0–C3 内部历史及全部报告。
人工修改：以下为 AI 实际操作，不记作人工手写；尚无人工署名审核记录。AI 编辑 test_profile.py 新增 Student231880027E9Tests 一个方法和两个 subTest；通过 Docker 运行9方法；新 OUT 创建受测副本、内部提交、执行 Make 和 GCC 扫描、保存输入/哈希/命令/日志/状态/历史 bundle；更新本人的三文档。未声称人工手工编写或已有人审核。
采纳/拒绝及理由：采纳测试扩展、保留参考算法。fixture、scan、key规则来自参考包；E8 间接 include 测试保留。本轮个人测试固定条件编译输入，以不变 directives/recipes/compiler 隔离 flags 变化，并固定双向完整图、发现和差量预期。没有放宽预期或修改 lab.py。
实际验证命令/输入/结果：原7+E8自主1+E9自主1，共9方法 OK，退出0；标准 C1图复用/真实main重编，C2新增MD，C3消除两MD保留RD；各状态独立全量结果一致。自主启用/恢复均刷新两目标，仅Makefile输入变，恢复哈希与基线相同。所有本轮命令退出0。
证据：/root/231880027/DevOps_A11-e8-e10/work/e9-A-manual.HCnER6，source.patch包含本轮执行时E8+E9测试差异；外层基SHA仍5cef53474d1987e432933a6010b9b18f24ecf29e，未提交修改不能归属于该提交。
E9 图来自 GCC -MM，未冒充 strace；配置自主场景未运行 Make。未改公共环境/workflow，未外层 commit/push，未 GitHub 变更。

## E10

工具/模型/日期：Codex AI；GPT-6.1 Sol；2026-11-03。
输入上下文与问题：允许本轮Docker/单元测试及样例内部Git；保留已完成E8/E9，禁止外层commit/push及GitHub变更。
模型建议：沿手册六类各五次，保存完整配对报告；独立设计“移除间接include但保留leaf文件”的五次扩展，固定完整边/发现及resolved，标准与自主CSV分开。
人工修改：以下为 AI 实际操作，不记作人工手写；尚无人工署名审核记录。AI 新增Student231880027E10Tests一个方法，保留之前9方法；通过Docker运行10方法OK/退出0；创建新OUT、执行标准30次配对与自主5次配对、最终真实BuildChecker与程序输出验证；保存每步源码命令/日志/退出码、输入快照哈希、内部Git历史bundle、统计并更新本人三文档。
采纳/拒绝及理由：采纳独立场景与完整集合断言，保留参考lab.py、profile和六类矩阵。个人新增测试固定transitive baseline后移除leaf include，当前图不含leaf但leaf文件仍在；分别核对增量/全量固定actual/declared/findings，resolved仅leaf MD。无算法/环境/workflow修改。
实际验证命令/输入/结果：全10方法OK；标准30行、自主5行均完整一致；最终动态SUCCEEDED/build退出0，对象actual一致，仅unused RD；程序1。flags/header/自主增量中位数略慢，原始数据照实保留，未筛选重跑。
异常：创建OUT前只读SSH两次连接关闭，未执行实验写入；恢复后本轮driver全部退出0，连接异常未记作目标故障。
证据：/root/231880027/DevOps_A11-e8-e10/work/e10-A-manual.X82TUT；source.patch包含本轮实际E8/E9/E10测试差异，基SHA5cef53474d1987e432933a6010b9b18f24ecf29e不包含这些未提交改动。
计时限定scan/GCC路径，只有最终重检使用strace；自主未再跑动态BuildChecker。未改E8/E9 raw，未外层commit/push、未GitHub变更。
