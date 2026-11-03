# A11 E8–E10 公共入口

本组 A 轨道任务：EChecker。来源为 `DevOps_E8_E10_20261031.zip`（2026-10-31 版）的 `03_实验包`，手册为 `02_操作手册/00_公共准备.md`、A 轨道三份路线、`07_提交与排错.md` 和个人测试示例。完整材料放在服务器 `/root/devops-materials/DevOps_E8_E10/`，不要把助教示例结果当作本组证据。

## 分工与前后顺序

| Issue | 负责人 | 主要维护职责 | 个人共同必做 |
| --- | --- | --- | --- |
| [#29](https://github.com/MaxizYB/DevOps_A11/issues/29) | 241880439 / MaxizYB | 公共接入、环境/CI、E8基线衔接、评审合并、最终汇总 | E8/E9/E10、自主贡献、个人三份文档 |
| [#30](https://github.com/MaxizYB/DevOps_A11/issues/30) | 231880027 / tongqianpolan | scan/key、依赖更新、复用/刷新及发现变化 | 同上，不能仅做E9 |
| [#31](https://github.com/MaxizYB/DevOps_A11/issues/31) | 241880411 / andelutixia | 完整集合判定、E10矩阵/统计、动态交叉核对 | 同上，不能仅做E10 |

公共准备 PR 合并且 #29 发布可开工 main SHA 后，两位成员再开始。个人阶段未完成前 #29 不关闭；参考实现及公共 smoke 不替代个人贡献。三个阶段都按手册末尾做自主任务，建议每人每阶段至少一个自己的独立预期测试；E10扩展场景另测五次。

## 服务器目录

本次使用新克隆，避免覆盖旧工作区、历史证据和成员未提交修改：

| 学号 | 本阶段个人仓库 | 个人分支 | 镜像 |
| --- | --- | --- | --- |
| 241880439 | `/root/241880439/DevOps_A11-e8-e10` | `student/241880439/e8-e10` | `course-e8e10:241880439` |
| 231880027 | `/root/231880027/DevOps_A11-e8-e10` | `student/231880027/e8-e10` | `course-e8e10:231880027` |
| 241880411 | `/root/241880411/DevOps_A11-e8-e10` | `student/241880411/e8-e10` | `course-e8e10:241880411` |

三个克隆都指向 `https://github.com/MaxizYB/DevOps_A11.git`，不是新建三个远程仓库。旧 `DevOps_A11`、`buildchecker` 和带日期的复验目录不动。公共材料是只读来源；源码在本人克隆，原始输出在本人 `work/`。

## 新会话开工

公共基础已合并后，在本人目录确认 Git 身份、分支和 main SHA。以下把 SID 设置为本人数字学号：

```bash
SID=241880439
cd "/root/$SID/DevOps_A11-e8-e10"
git status --short --branch
git config --local user.name
source scripts/e8e10/github_session.sh
```

`github_session.sh` 来自教学包，只设置本会话 `GH_CONFIG_DIR=/root/devops-auth/$SID/github` 和仓库局部 helper。首次需本人在浏览器授权自己的 GitHub；不能借用组长令牌或将认证目录放进 Git。共享 root 下这只避免误用会话，不构成不同系统用户间的权限隔离。

工作区干净后才同步 main、建立个人分支；已存在个人分支时合入 main，不强制重建、reset 或覆盖未提交改动。按手册用本人已验证邮箱或隐私邮箱；公共准备不代替本人 GitHub 登录。

```bash
git switch main
git pull --ff-only origin main
git switch "student/$SID/e8-e10"
git merge --no-edit main
```

尚未构建，或环境定义发生变化时执行下列命令；首次由组长安排串行：

```bash
mkdir -p work
ENV_LOG="work/environment-build-$(date +%Y%m%d-%H%M%S).log"
python3 run_lab.py build > "$ENV_LOG" 2>&1
ENV_CODE=$?
tail -n 35 "$ENV_LOG"
printf 'ENV_BUILD_EXIT=%s\n' "$ENV_CODE"
```

必须确认退出0，再 `source scripts/e8e10/classroom_helpers.sh`、`lab_ready`。辅助脚本也可按原手册从材料目录 source；本仓库版本与材料来源在 `reference-source.json` 中核对。

## 个人实验路线

推荐按完整 A 轨道手册逐步执行。新会话或断线只恢复变量；不要重复创建已存在的样例或重复 commit。

```bash
source scripts/e8e10/classroom_helpers.sh
lab_ready
lab_new_run e8 A
```

随后按 `8_E8_A组.md` 的 `lab_python "$OUT" <<'PY'` 代码块操作，自动保存步骤日志、学生源码 SHA 和镜像 ID。E9、E10分别 `lab_new_run e9 A`、`lab_new_run e10 A`。完整分步路线已完成后，不必重复跑同一状态的一键演示。

如仅自检参考入口，可选下列另一条路线（不要与分步路线的路径混写）：

```bash
python3 run_lab.py e8 --track A --out work/e8-A-<唯一目录>
python3 run_lab.py e9 --track A --out work/e9-A-<唯一目录>
python3 run_lab.py e10 --track A --out work/e10-A-<唯一目录>
```

分步 E10 产物在 `OUT/matrix/`，一键 E10 的产物直接在 `OUT/`，后者不自动生成手册的 `performance-summary.csv`；统计必须按手册另做。E3历史与本包C0–C3含义不同，不能互换。

## 代码、镜像和证据的边界

- `labs/e8e10/lab.py`、`test_profile.py`：课程受限教学实现和7项参考测试，挂载到容器 `/course` 执行。修改它们通常无需重建未变化的环境。
- `labs/e8e10/environment/`：本阶段独立环境定义，BuildChecker参考实现随环境镜像打包在 `/app`。修改 Dockerfile、锁文件或这里的 BuildChecker 需要重建镜像；顶层旧 `services/buildchecker/` 并不会自动替换镜像内参考代码。
- `run_lab.py`：按数字 Git 学号选择镜像，在新 `work/` 子目录运行，容器禁网、带 SYS_PTRACE。
- `docs/students/<SID>/e8-e10/`：个人报告、ADR、AI_USAGE，空白模板见 `docs/templates/e8-e10/`；只提交本人真实完成的内容。
- `work/`、个人认证、密钥与最终压缩包不提交 Git，原始证据按手册另行下载备份。

当前仍用 `test_profile.py` 发现规则，新增类用本人学号命名，保留原测试，避免同名类覆盖；拆分文件需同步 CI 发现规则。A11不要求个人完成B轨道；通用参考CI回归两轨道仅为导入兼容性检查，不计作A11已交付B组任务。

## 资源差异与验收

手册建议至少4 GiB可见内存、40 GiB可用磁盘；本组 ECS 实际约3.54 GiB、66 GiB可用。2026-11-03组长确认无法扩容，同意按现有资源试跑并披露差异。没有把4改为3.5，没有声称资源建议全部满足。首次构建串行；记录真实失败、实际工具版本及镜像 ID。

原 E7 检查必须保留，新检查为 `e8e10-quality-gate`。新检查首次正常通过后才能按真实 App ID 追加为 main 必需检查。所有 PR 遵循实际非作者评审；上次一次性审批例外不自动适用。公共准备真实结果见 [环境记录](../evidence/e8-e10/environment-preparation-20261103.md)，最终状态以 #29 的发布记录为准。
