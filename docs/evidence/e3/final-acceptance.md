# E3 Final Acceptance

- 关联 Issue：#5、#6、#7
- 收尾 PR 的输入 main：`3031b3dc9eaf9e401290ff26e1b79362688b438c`
- 验收范围：E3 基线 fixture、人工 Oracle、实际行为证据和可重放入口

## BuildChecker MD/RD

- Fixture：`fixtures/e3/md-rd/`
- Oracle：`fixtures/e3/md-rd/oracle.json`，来源为 `MANUAL_ORACLE`
- 环境：`docs/evidence/e3/environment/local-2026-09-24.json`
- 预期与实际：初始输出 `1`；修改 `config.h` 后普通增量仍为 `1`；clean build 输出 `2`；修改 `unused.h` 后重新编译且输出保持 `2`。
- 复现：按 `fixtures/e3/md-rd/README.md` 将 fixture 复制到新的 `work/e3/<run-id>/project/` 后执行四步命令。
- 收尾复核：`work/e3/20260925T044000Z-issue-6-md-rd/project/`，组长独立复现输出 `1 / 1 / 2 / 2`，与人工 Oracle 一致。

## EChecker C0/C1/C2

- Fixture：`fixtures/e3/echecker-history/`
- Oracle：`docs/evidence/e3/echecker/oracle.json`，来源为 `INSTRUCTOR_ORACLE`
- 环境：`docs/evidence/e3/environment/local-2026-09-25-gcc16.json`；成员先前的 Ubuntu/GCC 11 环境记录仍保留。
- 收尾复现运行目录：`work/e3/20260925T043526Z-issue-7-echecker-history/`
- 收尾复现的 SHA：C0 `242df6090df69b2c1e61ac422030ae901eac715c`，C1 `7f5e4341e938e890fa71b6d219ef51437d5cea1f`，C2 `fb03409e287fde67af2f707e689cf1c38a36ff51`。
- 收尾复现的行为：C0 clean `10`；C1 clean `12`；保留 C1 产物进入 C2 的普通增量 `12`；C2 clean `19`。
- 生成入口：`python3 fixtures/e3/echecker-history/create_history.py`。脚本每次使用新的 UTC 运行目录，不覆盖既有原始日志。

## Shared checks

```text
python3 scripts/e3/validate_e3_framework.py       PASS
python3 scripts/validate_contract.py              PASS
python3 -m py_compile scripts/e3/*.py             PASS
python3 -m json.tool < each submitted JSON        PASS
git diff --check                                  PASS
```

人工 Oracle、实际命令记录和未来检测器输出分别保存；当前仓库没有声称 BuildChecker/EChecker 算法已经实现。
