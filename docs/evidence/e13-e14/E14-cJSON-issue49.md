# E14：B11 cJSON 同 target 四服务修复预检

执行者：A11 组长 241880439 / MaxizYB，Codex 辅助。日期：2026-11-19 UTC（本机 America/Los_Angeles 为 2026-11-18）。关联 Issue #49、PR #50。

这是未合并修复分支的缺陷复测，不是最终 RC 验收，不替代 #45 的成员独立成果。

## 固定版本与输入

- 执行源码：b5f66f3bc52ab20364141ce193cd873d2d653973；云端独立克隆跟踪文件干净。运行驱动和网络源覆盖作为独立实验 harness 另存。
- B11 项目 base：cf0d87a095becada87336ed786f11070e9a037b5。
- B11 项目 target：f0c8fa4f812abe50964956cd0580ab963430ba35。
- 候选：B11 原始 cjson-b-e13.Dockerfile，SHA256 f8cbb53146b9453b8530f8a549696f6d44c6b51bd44fea04675a710c1768bbe7；候选字节未修改。
- 镜像：course-e11e12:241880439，ID sha256:548752eeae6ae6ea598e0a5aa9e26874bb27c3065b22e554e800a6595b1e8d53。源码通过只读版本挂载运行，不把旧镜像 ID 等同于新代码 SHA。
- 云端：/root/241880439/DevOps_A11-e14-issue49-20261119；证据 work/e14-issue49-cloud-20261119-mirror。
- 原始证据本地：work/e14-issue49-20261118/collected/；下载归档 cloud-evidence.tar.gz 的 SHA256 为 87cb9dff94e0aaf0a49787369ce82804c14fb932788a4833e5e30a68002beb1a。

## 前后结果

|检查|实际结果|
|---|---|
|修复前同 target|2dc4fe4 的编排器拒绝 cJSON：Unsupported teaching project profile；原件在 before-fix/|
|本地及云端单测|旧 E11/E12 68 项、新 E13/E14 34 项通过；包含真实 GCC/Make/strace 回归|
|四容器健康|运行前后四角色均 healthy，compose-health-before/after 原始记录保留|
|正常五阶段|draft→full-check→incremental-check→repair→recheck 全成功；验证 accepted=true，最终 findings=[]，程序验证输出 1|
|正常任务|job-c4c2d0a813084df999f1e310bacf7dc1；trace-41d995e5af7d43f8b0793f62c7097a29；1659 个产物哈希、字节数和阶段身份核验通过|
|超时|build_timeout=0.01；外层 FAILED、DRAFT 内层 TIMED_OUT、HTTP422/TIMEOUT；job-2c267f9d859a4977aa402aa86ed9a810|
|恢复|新任务 job-01e821ff03ec4893b67ad2b22c0cbc15；trace-260a87af0bbe4449893e347ce63de320；五阶段成功、1659 个产物再次通过|
|任务隔离|正常/失败/恢复的 job 和 trace 均不同；四角色日志均包含正常和恢复任务标识|
|输入保持|B11 repo HEAD、工作区状态、Makefile/test.c 字节、候选与 bundle 哈希前后相同|
|清理|只关闭 e14-49-241880439 Compose 项目；原 a11-e12-cjson-20261115 服务继续运行|

## 两项基础设施记录

1. 直连 Docker Hub 的首次构建因固定 digest 元数据请求超时失败，完整保留 work/e14-issue49-cloud-20261119/，不写成项目或算法失败，也不删原件。第二次仅用 BuildKit source policy 将该镜像引用映射到 m.daocloud.io，保留原 tag 和相同 digest；没有改 B11 Dockerfile、共享 Docker daemon 或公网监听。source-policy.json、compose.mirror.yaml 与 run_cloud_v2.py 随完整证据归档。正式复现须保留这一环境差异。
2. 运行目录原始扫描退出 1：4254 个文本、72 个命中、0 错误。72 项均逐条比对为两个 cJSON 上游 Unity 文件的固定 HTTP 测试字段；文件在 base/target 未变，每份副本字节与 Git 原件相同。判读清单为 runtime-fixture-review.json。不修改扫描器，不声称零命中。

## CI 与后续边界

修复源码 b5f66f3 的 push/PR 两组检查全部绿色。E13/E14 integration gate 分别为 44450995592、44451107977；E8–E10 首次因清华源 HTTP403 失败，44450995494、44451107900 的第 2 次实际运行成功，未跳过测试或降低门禁。

PR #50 尚待真实组员审阅和合并，#45 的独立记录尚缺，前置 PR #42/#47 未最终进入 main。完整 E13 门禁通过并合并后，仍须在固定最终提交重跑固定样例、A11/B11 项目和故障恢复，才能发布 v0.9-rc。本次没有发布标签或 Release。
