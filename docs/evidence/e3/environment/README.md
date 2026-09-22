# E3 Environment Manifests

每个实际运行环境使用 `local-YYYY-MM-DD.json` 命名。若同一天存在多个不同配置，在日期后加入简短后缀，例如 `local-2026-09-22-gcc16.json`。

清单由 `scripts/e3/capture_environment.py` 生成。配置会影响构建结果时，负责人必须据此创建或说明对应的 `configuration_id`。
