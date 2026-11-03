# E8–E10 公共准备记录（2026-11-03）

关联 #29，原仓库基线 `c28342bd194abf3f666bf4302b36d8db65b9a476`。本记录属于公共环境接入，不代表三名学生已完成个人实验。

## 已确认的资源与授权

- ECS：本组既有 Linux 主机；宿主 Git 2.34.1、Python 3.10.12、Docker 29.8.1、Compose 5.5.1。
- `/proc/meminfo` / free 可见内存约3623 MiB（3.54 GiB），根文件系统约66 GiB可用。
- 材料建议至少4 GiB可见内存与40 GiB可用磁盘；磁盘满足，内存低于建议。
- 2026-11-03组长明确回复“服务器就这么大，基本改不了，直接跑，可以说明”，因此只按现有资源串行试跑，不修改门槛、不调整云规格、不冒称完全满足资源建议。
- 原个人仓库和未提交改动保留，公共准备将使用各学号目录下的新克隆。

## 真实准备与验证

构建/公共自检源码为 `6bda191f47f0844ba78dc957ccb685da97a242d3`，通过完整 Git bundle 在各学号下新建 `DevOps_A11-e8-e10`；origin改为本组GitHub地址，旧克隆/未提交修改保持原样。本次先以detached提交做准备验证，PR #32 合并前不创建或发布“来自最新main”的个人分支。

- 材料已解压到 `/root/devops-materials/DevOps_E8_E10/`；ZIP SHA256：`9ac10fc8dbd10258f139647f4f9861f815936aed49f733d9d18082a15eb3f259`。
- 已安装 unzip 6.0、GitHub CLI 2.100.0，支持手册的run list --branch/--commit/--json等选项。最终使用官方发布的 amd64 deb，SHA256：`698c8d88cc19cc92bfe96bad58d10b2a5b274c52433d6dc57799c81f6139d5fc`，本地及云端校验一致。
- 安装中保留网络/兼容性故障边界：直接下载TLS超时，开发机可执行文件不兼容服务器ABI后已撤回，未修改glibc；最终校验官方deb后安装并成功运行，不将失败尝试算成通过。
- 三个镜像由组长公共准备自动化串行构建，不冒充成员个人运行或个人贡献。各克隆均保存本次source-manifest、实际命令、stdout/stderr和退出码。

| 学号 / 镜像标签后缀 | 实际image ID | 构建 | 参考测试 | helper |
| --- | --- | --- | --- | --- |
| 241880439 | `sha256:47e2ec8d350d9a250cc737a6d6f38e94d90cd66d92a8a3e94f8a19b90d3dc715` | exit 0 | 7 tests OK | lab_ready通过 |
| 231880027 | `sha256:16f347864cce0ee92773e6aafd356ff31fea52fce0711fe49cf22f9cf476b0ca` | exit 0 | 7 tests OK | lab_ready通过 |
| 241880411 | `sha256:ce7292ddf56c6038f9be6ead1c67b52bdcc11cf561c5867af6fdd3bfc8efc8cc` | exit 0 | 7 tests OK | lab_ready通过 |

三个标签为 `course-e8e10:<学号>`。实测容器：Python 3.13.14、GCC 14.2.0、Make 4.4.1、strace 6.13、pytest 8.4.2；包版本及Python依赖见各自toolchain输出。相同环境配方不保证manifest image ID相同，逐次以inspect为准。

组长克隆另完成A轨道三个一键参考入口公共smoke，均exit 0；E10 `gate.json` 为 `passed=true, rows=30`。这些不是三名学生已经完成手册分步、自主用例和个人报告的证明。

## CI与门禁

- 公共初始SHA的旧E7 PR运行：[41565288408](https://github.com/MaxizYB/DevOps_A11/actions/runs/41565288408)，success。
- 同一SHA的新E8–E10 PR运行：[41565287972](https://github.com/MaxizYB/DevOps_A11/actions/runs/41565287972)，success，artifact已下载；包含通用参考A/B六入口回归，不计作A11完成B轨道。
- `e8e10-quality-gate` 实测App ID为15368；首次通过后追加必需检查，保留 `e7-a-quality-gate`、strict、管理员约束、一名非作者批准与最后推送审批。保护前后快照在原始证据中。
- 文档记录提交会触发新CI，最终以PR #32最新head为准；PR尚未获非作者批准时不能宣称已合并或发布成员ready。

## 原始证据与下一步

服务器：每个新克隆 `work/public-environment-20261103/`（build、image、toolchain、reference-tests、helper、source-manifest与result）；组长同目录含smoke-e8/e9/e10。已下载到本地 `work/e8-e10-20261103/remote/<学号>/`；CI与保护配置在 `work/e8-e10-20261103/github/`，均不纳入Git。

三人的Git数字学号已设置；邮箱以本人已验证地址/隐私邮箱再次确认为准。各人GitHub浏览器认证仍需本人完成，未共享/部署组长Token。PR合并后还需同步真正main、建立各自手册分支、确认环境定义未变再发布可开工SHA；这一步不等于个人实验完成。
