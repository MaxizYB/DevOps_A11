# 决策记录

## E8

背景与约束：2026-11-03，231880027 的 E8 A 历史图基线与复用。仓库 /root/231880027/DevOps_A11-e8-e10，分支 student/231880027/e8-e10。仅新增自主测试与个人证据；不修改参考算法、公共 workflow/环境；本次实验运行未执行外层提交或推送。

选择与替代方案：
1. 按手册先保存 GCC baseline，再由真实 BuildChecker actual-graph.json 投影 main.o/helper.o 覆写历史 actual，保留 gcc-baseline.json 供审计。避免只凭 GCC 报告声称真实 trace 基线。
2. 保留参考全目标保守失效策略。自主输入仅在 config.h 增加 include extra.h，固定完整实际/声明/发现及差量预期，并与全量 GCC 扫描分别比较。暂不实施按目标刷新，避免把 E9 优化带入 E8。
3. 使用预建 course-e8e10:231880027 工具镜像和宿主仓库挂载；源码修改无需重建环境。记录基础 SHA + 未提交测试补丁及文件哈希，不把基础提交误当完整个人版本。
4. 保留原始路径错误和纠正证据，不重跑已有状态步骤。真实 BuildChecker 在 buildchecker/project 构建，程序从该路径执行。

A：缓存失效由参考 key 中项目根目录 .c/.h 文件名及预处理行、Make 制表符配方、CFLAGS、GCC 版本首行决定；声明每次重新解析，但本次自主测试不改变声明。相同 key 下未变化图两目标复用；头文件 include 变化两个目标刷新。
代价与覆盖范围：两个对象、受限 Make/GCC 配置；全目标刷新安全但可能多扫。没有证明跨目录、任意 Make、复杂配置和全量动态增量替换。自主扩展的全量对照是 GCC -MM，不是第二次 strace。E8 不包含性能测量。

验证命令与实际证据：见个人报告“重放方法”，以及 /root/231880027/DevOps_A11-e8-e10/work/e8-A-manual.8YSjkh/steps/ 的 command.json/stdout/stderr/result.json。
8 项单测 OK；真实报告 SUCCEEDED/build_exit_code=0；未变化两目标复用；程序纠正路径输出 1/退出0；标准输入哈希完全相同；自主固定完整预期及增量/全量一致。补丁未外层提交。原错误路径退出127保留，不计为算法故障。

## E9

背景与约束：保留 E8 全部证据，另建 work/e9-A-manual.HCnER6，按手册完成 C0–C3；新增一个 MODE 宏双向切换方法，不修改算法或公共配置。
选择与替代方案：标准项目和自主配置项目分离；标准 C1/C2 使用 1.05 秒 mtime 间隔并保存真实 Make 日志，同时用 GCC -MM scan 保存图复用/刷新结果。C3 只修声明并重新比较，保留 RD。
A：配置场景源码预处理指令固定，仅 CFLAGS -O0 → -O0 -DMODE=1 → -O0。启用新增 MD extra.h，恢复消除该 MD；完整 actual/declared/findings 及 added/resolved 均按固定值断言，且 key.directives/recipes/compiler 不变。
代价与覆盖范围：维持全目标保守刷新，不追求目标级优化；配置场景不执行 Make，不能把 scan 刷新等同 Make 重编。E9 图均采自 GCC -MM，没有新的动态 strace 证据。
验证命令与实际证据：全9测试 OK/退出0；标准 C1/2/3 与全量三项一致；标准输入每次仅预期文件改变；自主恢复哈希与基线完全一致。精确命令与证据见个人报告 E9 节和上述 OUT。

## E10

背景与约束：完成手册六场景×五次标准矩阵，独立增加移除间接include场景×五次；不修改公共30行协议或lab.py。
选择与替代方案：同一场景五次保持同一旧报告，避免rolling cache把后四次改成不同实验；完整固定actual/declared/findings与增量/全量同时断言。header时虽然依赖集合未新增，预处理结构仍改变，保持两目标保守刷新。
A：个人新增测试仅移除extra.h中的leaf include，保留leaf文件；固定当前图为main/config/extra，resolved仅leaf MD；与E8添加边、E9配置开关分开。
计时：分别保存标准30行、自主5行及两路径中位数/min/max，接受增量略慢的真实结果。计时仅scan，不能混同动态clean build或论文速度。
验证命令与实际证据：10方法OK；标准30行及自主5行完整集合一致；最终真实BuildChecker对象投影通过，SUCCEEDED/build_exit_code=0，仅unused.h RD，程序1。证据根work/e10-A-manual.X82TUT，基础SHA+未提交测试补丁见个人报告。
代价与覆盖范围：受限两对象Make/GCC profile、全目标保守刷新、5次微型输入固定测量顺序；不推广为任意构建正确性或通用性能结论。
