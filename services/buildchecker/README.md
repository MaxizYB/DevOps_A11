# BuildChecker

This module is the boundary for A group's full dependency detection work. Its owner will implement and test the module through the corresponding Issue.

The initial framework intentionally includes no source code, executable configuration, or interface contract. Shared data formats belong to the group leader's contract task.

```text
src/    future implementation
tests/  future verification
```

## E2 接口边界

BuildChecker 负责在固定 commit 和固定构建配置下处理 `FULL_CHECK` 任务。公共请求、响应、状态、错误和产物字段定义在 [`contracts/e2-interface-contract.md`](../../contracts/e2-interface-contract.md) 中，BuildChecker 不单独定义公共契约。

BuildChecker 专用的产物样例位于 [`examples/`](examples/)：

- `actual-graph.example.json`
- `declared-graph.example.json`
- `error-report.example.json`

EChecker 读取 `ACTUAL_GRAPH`，并检查其中的 commit 和 `configuration_id`。MDFixer 只读取 `ERROR_REPORT` 中的 `MISSING` 检测结果，不读取 `REDUNDANT`。

`examples/` 中的文件是接口交接样例，不是真实检测器输出，也不作为准确率证据。检测器实现属于后续阶段。
