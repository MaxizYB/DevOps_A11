"""Record the host and tools needed to repeat E4 on the group server."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIN_CPU = 2
MIN_MEMORY_KIB = int(3.5 * 1024**2)
MIN_DISK_BYTES = 40 * 1024**3


def command(args: list[str]) -> tuple[int, str]:
    try:
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=15)
    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        return 1, str(error)
    return result.returncode, (result.stdout or result.stderr).strip()


def collect() -> dict[str, object]:
    problems: list[str] = []
    warnings: list[str] = []
    tools: dict[str, object] = {}
    checks = {
        "git": ["git", "--version"],
        "docker_client": ["docker", "--version"],
        "docker_server": ["docker", "info", "--format", "{{.ServerVersion}}"],
        "docker_compose": ["docker", "compose", "version"],
        "docker_buildx": ["docker", "buildx", "version"],
        "make": ["make", "--version"],
        "python": [sys.executable, "--version"],
    }
    for name, args in checks.items():
        code, output = command(args)
        tools[name] = {"available": code == 0, "version": output.splitlines()[0] if output else ""}
        if code != 0 and name != "docker_buildx":
            problems.append(f"{name} unavailable")
        elif code != 0:
            warnings.append("docker_buildx unavailable; install Docker Buildx before relying on buildx-only commands")

    _, student_id = command(["git", "config", "--local", "user.name"])
    _, email = command(["git", "config", "--local", "user.email"])
    _, commit = command(["git", "rev-parse", "HEAD"])
    _, dirty = command(["git", "status", "--porcelain"])
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", student_id):
        problems.append("local git user.name must be a nonempty student ID without spaces")
    elif not student_id.isdigit():
        warnings.append("local git user.name is not numeric; set it to your student ID on ECS")
    if not email or "@" not in email:
        problems.append("local git user.email is missing")
    if len(commit) != 40:
        problems.append("source commit is unavailable")
    if dirty:
        warnings.append("worktree is not clean; use a fresh clone for acceptance")

    disk = shutil.disk_usage(ROOT)
    if disk.free < MIN_DISK_BYTES:
        problems.append("less than 40 GiB free disk space")
    memory_kib = None
    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        match = re.search(r"^MemTotal:\s+(\d+) kB", meminfo.read_text(), re.MULTILINE)
        if match:
            memory_kib = int(match.group(1))
            if memory_kib < MIN_MEMORY_KIB:
                problems.append("less than 3.5 GiB visible memory")
    if (os.cpu_count() or 0) < MIN_CPU:
        problems.append("fewer than 2 visible CPUs")

    env_file = ROOT / ".env"
    if env_file.exists() and env_file.stat().st_mode & 0o077:
        problems.append(".env permissions are broader than 600")

    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "host": {"system": platform.system(), "release": platform.release(), "machine": platform.machine(), "cpu_count": os.cpu_count(), "memory_kib": memory_kib, "disk_free_bytes": disk.free},
        "source": {"commit": commit, "git_user_name": student_id, "git_user_email": email, "dirty": bool(dirty)},
        "tools": tools,
        "problems": problems,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", "--out", dest="output", required=True, type=Path)
    args = parser.parse_args()
    report = collect()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("环境自检：通过" if not report["problems"] else "环境自检：失败")
    for problem in report["problems"]:
        print(f"问题：{problem}")
    for warning in report["warnings"]:
        print(f"警告：{warning}")
    print(f"证据：{args.output}")
    return 0 if not report["problems"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
