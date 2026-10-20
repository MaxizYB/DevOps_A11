# BuildChecker

This module is the boundary for A group's full dependency detection work. E4 supplies the reproducible container; E5 records the raw build trace and Make database, and E6 adds the auditable teaching-profile detector.

Shared data formats belong to the group leader's E2 contract task. E4's environment entry point is `buildchecker.cli`.

```text
buildchecker/  CLI (`version`, `smoke`, `full-check`)
tests/        service and E6 detector tests
src/          reserved for later production detector work
```

## E2 接口边界

BuildChecker 负责在固定 commit 和固定构建配置下处理 `FULL_CHECK` 任务。公共请求、响应、状态、错误和产物字段定义在 [`contracts/e2-interface-contract.md`](../../contracts/e2-interface-contract.md) 中，BuildChecker 不单独定义公共契约。

BuildChecker 专用的产物样例位于 [`examples/`](examples/)：

- `actual-graph.example.json`
- `declared-graph.example.json`
- `error-report.example.json`

EChecker 读取 `ACTUAL_GRAPH`，并检查其中的 commit 和 `configuration_id`。MDFixer 只读取 `ERROR_REPORT` 中的 `MISSING` 检测结果，不读取 `REDUNDANT`。

`examples/` 中的文件是接口交接样例，不是真实检测器输出，也不作为准确率证据。检测器实现属于后续阶段。

## E4 运行边界

- `PYTHONPATH=services/buildchecker python -m buildchecker version` reports the scaffold version locally; the container sets this path automatically.
- `PYTHONPATH=services/buildchecker python -m buildchecker smoke` rebuilds the E3 MD/RD fixture in a temporary directory under the container, traces `make` with `strace`, and checks that `config.h` was opened and the program prints `1`.
- The E4 `version`/`smoke` path does not claim to implement the E6 `ACTUAL_GRAPH`, `DECLARED_GRAPH`, or MD/RD analysis.
- Run from the repository root with `make all`; each run writes its evidence to a new ignored `work/<UTC timestamp>/` directory.

## E5–E7 运行边界

- `python3 scripts/lab_cloud.py e5 --out work/<run>` runs the full E5 trace in a Linux ECS container and preserves `trace/`, `make-db.txt`, build stderr and program output.
- `python3 scripts/lab_cloud.py e6 --out work/<run>` runs `full-check`; `--fixed` changes only an isolated fixture copy for the repair comparison.
- `python3 scripts/lab_cloud.py gate --out work/<run>` runs three original checks, one fixed check and three explicit failure scenarios. `tests/e7/` validates the gate oracle independently.
- This is an auditable teaching profile for the single GNU Make fixture. It is not a claim to reproduce the paper's complete benchmark or to implement the later REST service.
