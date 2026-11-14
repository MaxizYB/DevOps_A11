# ADR-0004：在 E2 契约之上增加 E11–E12 编排层

## 状态

Accepted for A11 preparation; cross-group integration pending.

## 决策

保留 contracts/e2-interface-contract.md 作为 A11/B11 服务边界的规范契约，在其上增加 contracts/e11-e12-orchestration.md 定义实验包所需的五阶段编排 API。编排层使用 e11e12-1 内部阶段信封，并通过映射保留 E2 的提交、配置、产物哈希、幂等和错误语义。

## 原因

E12 要求 DRAFT、全量检测、增量检测、修复和重检使用同一轮真实产物；直接覆盖 E2 契约会破坏已有 A/B 消费者。因此新增组合层，明确阶段边界和未完成的跨组联调范围。

## 后果

- A11 可以先独立验收 E11-A、服务启动、路径安全和契约拒绝测试。
- B11 可以按同一公共文档实现 DRAFT/MDFixer，并在联调时接入阶段产物。
- E12 的真实联调、真实项目和服务器证据仍需由双方按记录完成，不能由课程生成 fixture 代替
