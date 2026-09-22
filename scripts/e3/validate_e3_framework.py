#!/usr/bin/env python3
"""Validate the E3 baseline framework before module-specific fixtures are added."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REQUIRED_PATHS = (
    ".github/ISSUE_TEMPLATE/e3-task.md",
    "docs/adr/0002-e3-baseline-evidence-layout.md",
    "docs/backlog/e3-backlog.md",
    "docs/evidence/e3/README.md",
    "docs/evidence/e3/baseline-record-template.md",
    "docs/evidence/e3/buildchecker/README.md",
    "docs/evidence/e3/echecker/README.md",
    "docs/evidence/e3/environment/README.md",
    "fixtures/e3/README.md",
    "fixtures/e3/md-rd/README.md",
    "fixtures/e3/echecker-history/README.md",
    "fixtures/e3/echecker-history/snapshots/README.md",
    "work/e3/README.md",
    "scripts/e3/capture_environment.py",
)
REQUIRED_TOOLS = ("git", "make", "cc", "python3", "strace")
TEMPLATE_HEADINGS = (
    "项目与版本",
    "环境与配置",
    "预期 Oracle",
    "命令与结果",
    "实际观察",
    "失败与下一步",
)


class ValidationError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def read_text(relative_path: str) -> str:
    path = ROOT / relative_path
    require(path.is_file(), f"missing required file: {relative_path}")
    return path.read_text(encoding="utf-8")


def validate_required_paths() -> int:
    for relative_path in REQUIRED_PATHS:
        require((ROOT / relative_path).is_file(), f"missing required file: {relative_path}")
        print(f"PASS path: {relative_path}")
    return len(REQUIRED_PATHS)


def validate_ignored_work_area() -> None:
    gitignore = read_text(".gitignore")
    require("/work/e3/*" in gitignore, "work/e3 raw outputs are not ignored")
    require("!/work/e3/README.md" in gitignore, "work/e3 README is not retained")
    print("PASS work area: raw E3 outputs are ignored while its README is tracked")


def validate_templates() -> None:
    issue_template = read_text(".github/ISSUE_TEMPLATE/e3-task.md")
    require("阶段：E3" in issue_template, "E3 issue template does not declare E3")
    for heading in TEMPLATE_HEADINGS:
        require(
            heading in read_text("docs/evidence/e3/baseline-record-template.md"),
            f"baseline record template is missing section: {heading}",
        )
    print("PASS templates: E3 Issue and evidence templates contain required fields")


def validate_backlog() -> None:
    backlog = read_text("docs/backlog/e3-backlog.md")
    for issue_number in ("#5", "#6", "#7"):
        require(issue_number in backlog, f"E3 backlog does not track {issue_number}")
    print("PASS backlog: #5, #6, and #7 are tracked")


def validate_manifest(path: Path) -> None:
    try:
        manifest: Any = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValidationError(f"invalid environment manifest {path.relative_to(ROOT)}: {error}") from error

    require(isinstance(manifest, dict), "environment manifest must be an object")
    for key in ("schema_version", "captured_at", "host", "tools"):
        require(key in manifest, f"environment manifest is missing: {key}")
    require(isinstance(manifest["host"], dict), "environment manifest host must be an object")
    require(isinstance(manifest["tools"], dict), "environment manifest tools must be an object")
    for tool in REQUIRED_TOOLS:
        report = manifest["tools"].get(tool)
        require(isinstance(report, dict), f"environment manifest is missing tool: {tool}")
        require(isinstance(report.get("available"), bool), f"tool availability is invalid: {tool}")
    print(f"PASS environment: {path.relative_to(ROOT)}")


def validate_environment_manifests() -> int:
    directory = ROOT / "docs/evidence/e3/environment"
    manifests = sorted(directory.glob("*.json"))
    require(manifests, "no E3 environment manifest has been captured")
    for manifest in manifests:
        validate_manifest(manifest)
    return len(manifests)


def main() -> int:
    try:
        path_count = validate_required_paths()
        validate_ignored_work_area()
        validate_templates()
        validate_backlog()
        manifest_count = validate_environment_manifests()
    except (OSError, ValidationError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print(
        "PASS E3 framework validation: "
        f"{path_count} required files, {manifest_count} environment manifest(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
