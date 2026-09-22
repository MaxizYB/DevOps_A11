# C0/C1/C2 Snapshots

[#7](https://github.com/MaxizYB/DevOps_A11/issues/7) 将在此处建立生成历史的快照或等价脚本：

- `C0`：声明正确、clean build 输出 10 的基线。
- `C1`：新增 `feature.h` 使用但遗漏声明依赖、clean build 输出 12 的版本。
- `C2`：仅改变编译命令为 `-DMODE=7`、保留 C1 源码的版本。

快照目录不是 Git 仓库本身；真实历史必须在 `work/e3/` 生成并记录 SHA。
