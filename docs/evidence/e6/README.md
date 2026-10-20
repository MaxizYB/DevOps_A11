# E6 A 轨道：全量依赖检测 MVP

E6 把 E5 的人工步骤变成 `buildchecker full-check`。程序在独立副本中执行 clean build，解析进程树和文件访问，读取 Make 数据库，生成两张图并求集合差。

## 命令

```sh
python3 scripts/lab_cloud.py e6 --out work/e6-before-<student-id>
python3 scripts/lab_cloud.py e6 --fixed --out work/e6-after-<student-id>
python3 scripts/verify_e6_evidence.py \
  --before work/e6-before-<student-id>/evidence/findings.json \
  --after work/e6-after-<student-id>/evidence/findings.json
```

每次必须使用新目录。每次 `e6` 的 evidence 至少包括 `findings.json`、`actual-graph.json`、`declared-graph.json`、`processes.json`、`make-db.txt`、`trace/`、输入哈希和 clean/build 日志。

## 实现边界

- 从 `clone`/`fork` 和 `execve` 重建构建任务，把 `cc` 的 `cc1`、`as` 子进程归到同一目标；
- 成功的读打开形成实际依赖，写打开或最终 rename 形成目标；项目外路径、系统路径、临时文件和失败打开被过滤；
- 从 Make 的 `# Files` 段提取声明依赖，展开 `.PHONY`，保留 order-only 依赖信息；
- 每个 recipe 只允许一个最终输出，多个输出、无法归属的路径或不支持的 trace 必须显式失败。

## 验收

原始样例必须精确报告 `MISSING(main.o, config.h)` 和 `REDUNDANT(main.o, unused.h)`，启用 `--fail-on-findings` 时工具退出码为 1。`--fixed` 只修改独立副本的 Makefile，复检结果必须为 `findings=[]`、工具退出码为 0，输入哈希只能变化 `Makefile`。
