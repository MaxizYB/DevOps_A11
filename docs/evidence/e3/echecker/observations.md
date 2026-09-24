# EChecker C0/C1/C2 Observations

## 项目与版本

- 关联 Issue：#7
- 样例类型：C0-C1-C2
- 项目来源或生成脚本：`fixtures/e3/echecker-history/create_history.py`
- 运行目录：`work/e3/20260924T020000Z-issue-7-echecker-history/`
- configuration_id 或等价配置：`cfg-linux-ubuntu22-gcc11-o0-v1`

## 实际观察

| 检查项 | 预期 | 实际 | 结论 |
| --- | --- | --- | --- |
| C0 clean build | 输出 `10` | 输出 `10` | 通过 |
| C1 clean build | 输出 `12` | 输出 `12` | 通过 |
| C2 保留 C1 产物普通增量构建 | 输出 `12` | 输出 `12` | 通过 |
| C2 clean build | 输出 `19` | 输出 `19` | 通过 |
| C2 强制预览 `main.o` 命令 | 包含 `-DMODE=7` | `gcc -O0 -DMODE=7 -c main.c -o main.o` | 通过 |

## Oracle 对照

- C0 的声明依赖为 `main.c config.h`，实际包含也只有 `config.h`，本例范围内无 MD。
- C1 新增 `feature.h` 且 `main.c` 包含它，但 `Makefile` 的 `main.o` 依赖仍为 `main.c config.h`，因此 `main.o -> feature.h` 是 `MISSING`。
- C2 没有改变 C1 的源码或依赖声明，只改变 `CFLAGS` 为 `-O0 -DMODE=7`；因此 MD Oracle 仍存在，且命令变化会导致 clean build 行为从 `12` 变为 `19`。

## EChecker Baseline 说明

后续 EChecker 以 C0 的实际依赖图作为 baseline：

- `base_commit = 8dfd90625e9d6f4598649ac3c956bbe46941e393`
- `baseline.commit = 8dfd90625e9d6f4598649ac3c956bbe46941e393`
- `baseline.configuration_id = cfg-linux-ubuntu22-gcc11-o0-v1`

比较 C0 到 C1 时，预期新增一个 `MISSING` 发现：`main.o -> feature.h`。比较 C1 到 C2 时，该 `MISSING` 发现仍为当前发现，但不是新增发现；C2 的重点是记录编译命令变化造成的增量构建输出 `12` 与 clean build 输出 `19` 的差异。
