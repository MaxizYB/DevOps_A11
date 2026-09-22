# E3 Evidence

本目录保存 E3 的可提交证据摘要。原始 clone、编译产物、嵌套 Git 仓库和大日志留在 [`work/e3/`](../../../work/e3/README.md)，不要直接提交。

## 三类记录必须分开

| 类别 | 含义 | 保存位置 |
| --- | --- | --- |
| 人工 Oracle | 根据源码、Makefile 和课程要求给出的预期；必须标明来源 | fixture 或本目录的 `oracle.*` |
| 实际观察 | 本机执行命令后的退出码、输出和行为 | 本目录的 `commands.*`、`observations.*`、`failures.*` |
| 工具输出 | 后续 BuildChecker/EChecker 的真实报告 | 对应模块目录，注明工具版本和运行 Job |

## 标准目录

```text
docs/evidence/e3/
├── environment/                 # 环境清单
├── buildchecker/                # #6 的 Oracle 和实际观察摘要
├── echecker/                    # #7 的 SHA、Oracle 和实际观察摘要
└── baseline-record-template.md  # 每次基线记录模板
```

每一份基线记录必须包含：项目来源或生成方法、完整 commit SHA、环境或 `configuration_id`、命令、退出码、标准输出/错误位置、预期 Oracle、实际观察、失败原因和下一步。使用 [`baseline-record-template.md`](baseline-record-template.md) 作为起点。

## 当前环境清单

使用以下命令记录每个实际运行环境：

```bash
python3 scripts/e3/capture_environment.py \
  --output docs/evidence/e3/environment/local-YYYY-MM-DD.json
```

清单只记录操作系统/CPU、Python 和课程所需工具的版本及可用性，不记录主机名、用户名或环境变量。
