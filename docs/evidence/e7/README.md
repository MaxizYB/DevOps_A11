# E7 A 轨道：正确性、故障和 CI 门禁

E7 验证 E6 不是只对一个成功样例有效，并用 GitHub 分支保护证明失败代码不能进入 `main`。云端结果和 GitHub Actions artifact 都要保留；不要用本地单测替代 ECS 结果。

## 成员实际运行记录

- [231880027：2026-10-20 ECS 验证、自主测试与证据索引](e7-20261020-test-cloud-validation.md)：独立判定 7 项已打包入镜像并在容器内通过；镜像 pytest 共 22 项（15 项服务测试＋7 项判定测试）、八项门禁通过，附实际证据路径与重放命令。

## 云端门禁

```sh
python3 -m unittest discover -s tests/e7 -v
python3 scripts/lab_cloud.py gate --out work/e7-<student-id>
```

门禁包含一项服务测试、三次原始检测、一次修复后检测，以及构建失败、多输出和超时三个故障场景。整体 `gate-result.json` 及 `results.csv` 必须逐项对应，所有 `passed` 为 true，整体退出码为 0。故障场景返回非零是预期工具行为，只要状态和错误码符合 oracle 即算该场景通过；超时还必须核对运行容器已清理。

## GitHub Actions

`.github/workflows/e7-quality-gate.yml` 在 push、pull request 和手动触发时：

1. 检出触发提交并保存 SHA；
2. 运行独立判定测试、源码/历史密钥扫描；
3. 构建固定环境镜像并扫描镜像；
4. 运行真实 E7 门禁；
5. 无论成功失败都上传 `work/ci/` artifact。

首次正常 CI 通过后，组长配置 `e7-a-quality-gate` 为 main 必需检查，启用 strict 和管理员约束。随后用错误测试预期创建故意失败 PR，实际尝试普通合并并保存拒绝日志；在同一 PR 修正预期，等待最新 SHA 的 CI 通过后再合并。报告必须区分测试 oracle 修正和算法修复。
