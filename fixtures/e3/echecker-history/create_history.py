#!/usr/bin/env python3
"""Create the #7 C0/C1/C2 EChecker history fixture under work/e3."""

from __future__ import annotations

import os
import json
import shutil
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SNAPSHOTS = ROOT / "fixtures" / "e3" / "echecker-history" / "snapshots"
RUN_DIR = ROOT / "work" / "e3" / "20260924T020000Z-issue-7-echecker-history"
REPO_DIR = RUN_DIR / "repo"


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


def commit_snapshot(label: str, message: str) -> str:
    replace_tree(SNAPSHOTS / label, REPO_DIR)
    run(["git", "add", "."], REPO_DIR)
    run(["git", "commit", "-m", message], REPO_DIR, label=label)
    run(["git", "tag", "-f", label], REPO_DIR)
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(REPO_DIR),
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return result.stdout.strip()


def verify_history(shas: dict[str, str]) -> dict[str, object]:
    make = find_make()
    clean_command = [make, "clean"]
    if make == "mingw32-make":
        clean_command.append("RM=cmd /C del /Q /F")
    steps: list[dict[str, object]] = []

    def checked(args: list[str]) -> dict[str, object]:
        step = capture(args, REPO_DIR)
        steps.append(step)
        require_success(step)
        return step

    checked(["git", "-c", "advice.detachedHead=false", "checkout", "C0"])
    checked(clean_command)
    checked([make])
    c0_output = checked([str(REPO_DIR / "app.exe")])["stdout"].strip()

    checked(["git", "-c", "advice.detachedHead=false", "checkout", "C1"])
    checked(clean_command)
    checked([make])
    c1_output = checked([str(REPO_DIR / "app.exe")])["stdout"].strip()

    checked(["git", "-c", "advice.detachedHead=false", "checkout", "C2"])
    c2_command = checked([make, "-n", "-B", "main.o"])["stdout"].strip()
    checked([make])
    c2_incremental_output = checked([str(REPO_DIR / "app.exe")])["stdout"].strip()
    checked(clean_command)
    checked([make])
    c2_clean_output = checked([str(REPO_DIR / "app.exe")])["stdout"].strip()

    summary = {
        "repo": str(REPO_DIR),
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

    (RUN_DIR / "verification_summary.json").write_text(
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
    (RUN_DIR / "verification.log").write_text("\n".join(lines), encoding="utf-8")
    return summary


def main() -> int:
    if RUN_DIR.exists():
        shutil.rmtree(RUN_DIR, onerror=remove_readonly)
    REPO_DIR.mkdir(parents=True)

    run(["git", "-c", "init.defaultBranch=main", "-c", "core.autocrlf=false", "init"], REPO_DIR)
    shas = {
        "C0": commit_snapshot("C0", "C0 baseline declared dependencies"),
        "C1": commit_snapshot("C1", "C1 add missing feature dependency"),
        "C2": commit_snapshot("C2", "C2 change compile flags only"),
    }

    print(f"created: {REPO_DIR}")
    for label, sha in shas.items():
        print(f"{label}: {sha}")
    summary = verify_history(shas)
    print(f"verification: {RUN_DIR / 'verification_summary.json'}")
    print(f"outputs: {summary['outputs']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
