# E3 基线框架校验记录

- 日期：2026-09-22
- 关联 Issue：#5
- 分支：`docs/5-e3-baseline-governance`
- 范围：E3 目录、环境、证据和任务模板；不包含 #6 的 MD/RD 样例或 #7 的 C0/C1/C2 历史。

## 运行环境

- 环境清单：[`environment/local-2026-09-22-gcc16.json`](environment/local-2026-09-22-gcc16.json)
- 操作系统 / CPU：Linux 6.18.40-2-lts / x86_64
- Git：2.55.0
- GNU Make：4.4.1
- C 编译器：GCC 16.2.1
- Python：3.14.7
- `strace`：7.0，可用

## 校验命令

```bash
python3 scripts/e3/capture_environment.py \
  --output docs/evidence/e3/environment/local-2026-09-22-gcc16.json
python3 scripts/e3/validate_e3_framework.py
python3 -m py_compile scripts/e3/capture_environment.py scripts/e3/validate_e3_framework.py
git diff --check
```

## 实际结果

```text
PASS E3 framework validation: 14 required files, 1 environment manifest(s)
```

校验确认 E3 Issue 模板、ADR、Backlog、fixture/work/evidence 边界、证据模板、环境清单和环境采集脚本均存在且结构有效。`work/e3/` 的原始运行输出默认被忽略，只有说明文件受版本控制。

## 后续输入

- #6 在 `fixtures/e3/md-rd/` 与 `docs/evidence/e3/buildchecker/` 填入 MD/RD fixture、Oracle 和实际运行证据。
- #7 在 `fixtures/e3/echecker-history/` 与 `docs/evidence/e3/echecker/` 填入 C0/C1/C2 生成步骤、真实 SHA、Oracle 和实际运行证据。
- 两项任务合并后，#5 将在干净副本执行 README 中的命令并完成汇总验收。
