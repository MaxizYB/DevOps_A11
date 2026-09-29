# E4 Evidence

E4 的运行证据不写入仓库的固定目录；每次 `make doctor/build/test/smoke/scan/all` 都在被忽略的 `work/<UTC timestamp>/` 生成一组文件。

## 成功运行必须保留

| 文件 | 内容 |
| --- | --- |
| `env.json` | 系统、CPU、内存、磁盘、Docker、Git 身份和源码 SHA |
| `build.log` | 固定 digest 镜像构建输出 |
| `image.json` | 构建镜像 ID 和元数据 |
| `toolchain.lock` | 镜像内实际 gcc/make/strace/git 版本 |
| `test.log` | 容器内 pytest 结果 |
| `smoke.json` | E3 MD/RD 冒烟结果、`config.h` 打开证据和程序输出 |
| `secret-scan.txt` | 工作区、Git 历史和镜像密钥扫描结果 |

E4 还需要两名组员在各自克隆中使用同一个模板提交 SHA 运行 `make all`，在 Issue/PR 或课程记录中写下两个成功证据目录及对照结论。`work/` 原始日志默认不提交；E5 需要重新保存完整 `strace -ff` 和 `make -p` 证据。

`work/` 根目录使用 sticky-bit 共享写权限，便于容器内 UID 10001 在 `/app/work` 留存 E5 证据；每名学生仍应在自己的学号目录独立克隆，不共用同一个工作树。

## 当前本地状态

当前开发机没有可用 Docker daemon，因此本地只能完成 Python 单测、CLI 冒烟、契约回归和静态检查。镜像构建、容器内测试、镜像扫描以及两名 ECS 组员的重跑必须在服务器上完成后再把 E4 Issue 标记为完成。
