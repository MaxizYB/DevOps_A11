#!/usr/bin/env python3
"""Capture a portable E3 build-environment manifest without external packages."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TOOL_COMMANDS: dict[str, list[str]] = {
    "git": ["git", "--version"],
    "make": ["make", "--version"],
    "cc": ["cc", "--version"],
    "python3": [sys.executable, "--version"],
    "strace": ["strace", "--version"],
}


def utc_now() -> str:
    """Return an ISO 8601 timestamp without machine-local timezone ambiguity."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def compact_output(stdout: str, stderr: str) -> str | None:
    """Keep the version line useful while avoiding arbitrary command output capture."""

    for line in (stdout + "\n" + stderr).splitlines():
        text = line.strip()
        if text:
            return text
    return None


def inspect_tool(command: list[str]) -> dict[str, Any]:
    executable = command[0]
    path = shutil.which(executable)
    report: dict[str, Any] = {
        "command": command,
        "path": path,
        "available": path is not None,
        "returncode": None,
        "version": None,
    }
    if path is None:
        return report

    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except OSError as error:
        report["available"] = False
        report["error"] = str(error)
        return report
    except subprocess.TimeoutExpired:
        report["error"] = "version command timed out after 10 seconds"
        return report

    report["returncode"] = completed.returncode
    report["version"] = compact_output(completed.stdout, completed.stderr)
    return report


def build_manifest() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "captured_at": utc_now(),
        "host": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
        },
        "tools": {
            name: inspect_tool(command)
            for name, command in TOOL_COMMANDS.items()
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture operating-system and E3 tool-version evidence."
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the JSON manifest to this path instead of standard output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = build_manifest()
    rendered = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        sys.stdout.write(rendered)
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"Wrote E3 environment manifest: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
