# E6 A 轨道：全量依赖检测 MVP

E6 把 E5 的人工步骤变成 `buildchecker full-check`。程序在独立副本中执行 clean build，解析进程树和文件访问，读取 Make 数据库，生成两张图并求集合差。

Issue [#21](https://github.com/MaxizYB/DevOps_A11/issues/21) 的实现说明、边界修复、测试结果和证据索引见 [E6 实现与验证记录](issue-21-validation.md)。

## 命令

```sh
python3 scripts/lab_cloud.py e6 --out work/e6-before-<student-id>
python3 scripts/lab_cloud.py e6 --fixed --out work/e6-after-<student-id>
python3 scripts/verify_e6_evidence.py \
  --before work/e6-before-<student-id>/evidence/findings.json \
  --after work/e6-after-<student-id>/evidence/findings.json
```

每次必须使用新目录。每次 `e6` 的 evidence 至少包括 `findings.json`、`actual-graph.json`、`declared-graph.json`、`processes.json`、`make-db.txt`、`trace/`、输入哈希和 clean/build 日志。

## 范围与验收

教学范围为单个 Make 进程、每 recipe 一个最终输出，以成功读打开作为实际依赖观察。不支持的路径或进程行为显式返回 `UNSUPPORTED`。

原始样例必须精确报告 `MISSING(main.o, config.h)` 和 `REDUNDANT(main.o, unused.h)`，启用 `--fail-on-findings` 时工具退出码为 1。`--fixed` 只修改独立副本的 Makefile，复检结果必须为 `findings=[]`、工具退出码为 0，输入哈希只能变化 `Makefile`。
