"""Minimal E4 CLI. Dependency analysis is intentionally out of scope."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import __version__


def opened_header(trace: str, header: str = "config.h") -> bool:
    return any("openat(" in line and f'"{header}"' in line and "= -1" not in line for line in trace.splitlines())


def smoke(fixture: Path) -> dict[str, object]:
    if not (fixture / "Makefile").is_file():
        raise FileNotFoundError(f"fixture Makefile missing: {fixture}")
    with tempfile.TemporaryDirectory(prefix="e4-buildchecker-") as temp:
        project = Path(temp) / "project"
        shutil.copytree(fixture, project)
        subprocess.run(["make", "clean"], cwd=project, check=True, capture_output=True, text=True)
        traced = subprocess.run(
            ["strace", "-f", "-e", "trace=openat", "make"],
            cwd=project,
            capture_output=True,
            text=True,
            timeout=60,
        )
        app = subprocess.run([str(project / "app")], cwd=project, capture_output=True, text=True, timeout=10) if traced.returncode == 0 else None
        trace_lines = [line for line in traced.stderr.splitlines() if '"config.h"' in line][:8]
        result: dict[str, object] = {
            "make_exit_code": traced.returncode,
            "app_output": app.stdout.strip() if app else None,
            "config_h_opened": trace_lines,
            "trace_lines": len(traced.stderr.splitlines()),
            "passed": traced.returncode == 0 and app is not None and app.returncode == 0
            and app.stdout.strip() == "1" and opened_header(traced.stderr),
        }
        if traced.returncode != 0:
            result["error_tail"] = traced.stderr.splitlines()[-8:]
        return result


def default_fixture() -> Path:
    """Use the container copy when present, otherwise the repository fixture."""
    container_fixture = Path("fixtures/md-rd")
    return container_fixture if container_fixture.exists() else Path("fixtures/e3/md-rd")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="buildchecker")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("version")
    smoke_parser = commands.add_parser("smoke")
    smoke_parser.add_argument("--fixture", type=Path, default=default_fixture())
    args = parser.parse_args(argv)
    if args.command == "version":
        print(__version__)
        return 0
    try:
        result = smoke(args.fixture)
    except (FileNotFoundError, subprocess.SubprocessError) as error:
        result = {"passed": False, "error": str(error)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
