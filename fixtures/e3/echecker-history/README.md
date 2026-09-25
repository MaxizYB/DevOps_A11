# EChecker History Fixture

此目录保存 [#7](https://github.com/MaxizYB/DevOps_A11/issues/7) 的 C0/C1/C2 增量检测基线材料。

## 内容

- `snapshots/C0/`：声明依赖和实际依赖一致的基线提交，clean build 输出 `10`。
- `snapshots/C1/`：新增 `feature.h` 并让 `main.c` 使用它，但 `Makefile` 仍只声明 `main.c config.h`，clean build 输出 `12`，人工 Oracle 标记 `main.o -> feature.h` 为 `MISSING`。
- `snapshots/C2/`：源码保持 C1，只把 `CFLAGS` 从 `-O0` 改为 `-O0 -DMODE=7`；保留 C1 产物时普通增量输出仍为 `12`，clean build 输出 `19`。
- `create_history.py`：将上述快照生成到 `work/e3/` 下的真实 Git 仓库，并连续提交为 C0、C1、C2。

## 生成真实历史

从仓库根目录运行：

```powershell
conda run -n devops python fixtures\e3\echecker-history\create_history.py
```

脚本会创建 `work/e3/20260924T020000Z-issue-7-echecker-history/repo/`，并在其中生成真实 Git 历史和 tag：

- `C0`
- `C1`
- `C2`

生成后的嵌套 Git 仓库、编译产物和原始日志只保存在 `work/e3/`，不提交到本仓库。可提交的 SHA、命令、Oracle 和观察摘要写入 `docs/evidence/e3/echecker/`。
