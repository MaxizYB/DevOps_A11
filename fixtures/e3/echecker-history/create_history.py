#!/usr/bin/env python3
"""Create the #7 C0/C1/C2 EChecker history fixture under work/e3."""

from __future__ import annotations

import os
import json
import shutil
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SNAPSHOTS = ROOT / "fixtures" / "e3" / "echecker-history" / "snapshots"
RUN_ROOT = ROOT / "work" / "e3"


GIT_DATES = {
    "C0": "2026-09-24T00:00:00+08:00",
    "C1": "2026-09-24T00:01:00+08:00",
    "C2": "2026-09-24T00:02:00+08:00",
}


def git_env(label: str | None = None) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_NAME": "A11 EChecker Fixture",
            "GIT_AUTHOR_EMAIL": "a11-echecker@example.invalid",
            "GIT_COMMITTER_NAME": "A11 EChecker Fixture",
            "GIT_COMMITTER_EMAIL": "a11-echecker@example.invalid",
        }
    )
    if label is not None:
        env["GIT_AUTHOR_DATE"] = GIT_DATES[label]
        env["GIT_COMMITTER_DATE"] = GIT_DATES[label]
    return env


def run(args: list[str], cwd: Path, label: str | None = None) -> None:
    subprocess.run(args, cwd=str(cwd), env=git_env(label), check=True)


def capture(args: list[str], cwd: Path) -> dict[str, object]:
    result = subprocess.run(
        args,
        cwd=str(cwd),
        env=git_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return {
        "command": args,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def require_success(step: dict[str, object]) -> None:
    if step["returncode"] != 0:
        command = " ".join(str(part) for part in step["command"])
        raise RuntimeError(f"command failed: {command}\n{step['stderr']}")


def find_make() -> str:
    for candidate in ("mingw32-make", "make"):
        if shutil.which(candidate):
            return candidate
    raise RuntimeError("neither mingw32-make nor make is available")


def replace_tree(source: Path, destination: Path) -> None:
    for child in destination.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    for child in source.iterdir():
        target = destination / child.name
        if child.is_dir():
            shutil.copytree(child, target)
        else:
            shutil.copy2(child, target)


def remove_readonly(function, path, _exc_info) -> None:
    os.chmod(path, stat.S_IWRITE)
    function(path)


def create_run_dir() -> tuple[Path, Path]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = RUN_ROOT / f"{run_id}-issue-7-echecker-history"
    suffix = 1
    while run_dir.exists():
        run_dir = RUN_ROOT / f"{run_id}-{suffix}-issue-7-echecker-history"
        suffix += 1
    repo_dir = run_dir / "repo"
    repo_dir.mkdir(parents=True)
    return run_dir, repo_dir


def commit_snapshot(label: str, message: str, repo_dir: Path) -> str:
    replace_tree(SNAPSHOTS / label, repo_dir)
    run(["git", "add", "."], repo_dir)
    run(["git", "commit", "-m", message], repo_dir, label=label)
    run(["git", "tag", label], repo_dir)
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo_dir),
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return result.stdout.strip()


def verify_history(shas: dict[str, str], run_dir: Path, repo_dir: Path) -> dict[str, object]:
    make = find_make()
    clean_command = [make, "clean"]
    if make == "mingw32-make":
        clean_command.append("RM=cmd /C del /Q /F")
    steps: list[dict[str, object]] = []

    def checked(args: list[str]) -> dict[str, object]:
        step = capture(args, repo_dir)
        steps.append(step)
        require_success(step)
        return step

    checked(["git", "-c", "advice.detachedHead=false", "checkout", "C0"])
    checked(clean_command)
    checked([make])
    c0_output = checked([str(repo_dir / "app.exe")])["stdout"].strip()

    checked(["git", "-c", "advice.detachedHead=false", "checkout", "C1"])
    checked(clean_command)
    checked([make])
    c1_output = checked([str(repo_dir / "app.exe")])["stdout"].strip()

    checked(["git", "-c", "advice.detachedHead=false", "checkout", "C2"])
    c2_command = checked([make, "-n", "-B", "main.o"])["stdout"].strip()
    checked([make])
    c2_incremental_output = checked([str(repo_dir / "app.exe")])["stdout"].strip()
    checked(clean_command)
    checked([make])
    c2_clean_output = checked([str(repo_dir / "app.exe")])["stdout"].strip()

    summary = {
        "repo": str(repo_dir),
        "make_command": make,
        "commits": shas,
        "outputs": {
            "C0_clean": c0_output,
            "C1_clean": c1_output,
            "C2_incremental_from_C1_products": c2_incremental_output,
            "C2_clean": c2_clean_output,
        },
        "c2_forced_main_o_command": c2_command,
        "steps": steps,
    }

    (run_dir / "verification_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    lines = []
    for step in steps:
        lines.append(f"$ {' '.join(str(part) for part in step['command'])}")
        if step["stdout"]:
            lines.append(str(step["stdout"]).rstrip())
        if step["stderr"]:
            lines.append(str(step["stderr"]).rstrip())
        lines.append(f"exit={step['returncode']}")
        lines.append("")
    (run_dir / "verification.log").write_text("\n".join(lines), encoding="utf-8")
    return summary


def main() -> int:
    run_dir, repo_dir = create_run_dir()

    run(["git", "-c", "init.defaultBranch=main", "-c", "core.autocrlf=false", "init"], repo_dir)
    shas = {
        "C0": commit_snapshot("C0", "C0 baseline declared dependencies", repo_dir),
        "C1": commit_snapshot("C1", "C1 add missing feature dependency", repo_dir),
        "C2": commit_snapshot("C2", "C2 change compile flags only", repo_dir),
    }

    print(f"created: {repo_dir}")
    for label, sha in shas.items():
        print(f"{label}: {sha}")
    summary = verify_history(shas, run_dir, repo_dir)
    print(f"verification: {run_dir / 'verification_summary.json'}")
    print(f"outputs: {summary['outputs']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
