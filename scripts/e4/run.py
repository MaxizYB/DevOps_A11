"""Run E4 checks and keep each invocation's evidence together."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "work"
COMMAND_TIMEOUT = 600


def new_run_dir() -> Path:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    WORK.mkdir(parents=True, exist_ok=True)
    WORK.chmod(0o1777)
    path = WORK / run_id
    path.mkdir(parents=True, exist_ok=False)
    # The Compose service runs as UID 10001.  Keep the per-run evidence
    # directory writable when a later E5 command writes through /app/work.
    path.chmod(0o777)
    return path


def identity() -> str:
    result = subprocess.run(["git", "config", "--local", "user.name"], cwd=ROOT, capture_output=True, text=True)
    value = result.stdout.strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", value):
        raise RuntimeError("set local git user.name to your student ID")
    return value


def environment() -> dict[str, str]:
    env = os.environ.copy()
    env["STUDENT_ID"] = identity()
    env["COMPOSE_PROJECT_NAME"] = f"e4-buildchecker-{env['STUDENT_ID'].lower()}"
    return env


def execute(
    args: list[str],
    output: Path | None = None,
    env: dict[str, str] | None = None,
    stderr: Path | None = None,
    timeout: int | None = COMMAND_TIMEOUT,
) -> None:
    def run(stdout, errors):
        try:
            return subprocess.run(args, cwd=ROOT, env=env, stdout=stdout, stderr=errors, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as error:
            raise RuntimeError(f"{' '.join(args[:3])} timed out after {timeout}s") from error

    if output:
        with output.open("w", encoding="utf-8") as log:
            if stderr:
                with stderr.open("w", encoding="utf-8") as errors:
                    result = run(log, errors)
            else:
                result = run(log, subprocess.STDOUT)
    else:
        result = run(None, None)
    if result.returncode:
        raise RuntimeError(f"{' '.join(args[:3])} failed with exit code {result.returncode}; see {output or 'terminal'}")


def ensure_env() -> None:
    target = ROOT / ".env"
    if target.exists():
        return
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as output:
        output.write((ROOT / ".env.example").read_bytes())


def doctor(run_dir: Path) -> None:
    execute([sys.executable, "scripts/e4/doctor.py", "--output", str(run_dir / "env.json")])


def build(run_dir: Path, env: dict[str, str]) -> None:
    ensure_env()
    build_env = dict(env)
    build_env["BUILDKIT_PROGRESS"] = "plain"
    execute(["docker", "compose", "build", "buildchecker"], run_dir / "build.log", build_env)
    image = f"e4-buildchecker:{env['STUDENT_ID']}"
    execute(["docker", "image", "inspect", image], run_dir / "image.json", env, run_dir / "image.stderr.log")
    execute(["docker", "compose", "run", "--rm", "-T", "--interactive=false", "--no-deps", "buildchecker", "cat", "/opt/toolchain.lock"], run_dir / "toolchain.lock", env, run_dir / "toolchain.stderr.log")


def test(run_dir: Path, env: dict[str, str]) -> None:
    execute(["docker", "compose", "run", "--rm", "-T", "--interactive=false", "--no-deps", "buildchecker", "pytest", "-q", "-p", "no:cacheprovider", "services/buildchecker/tests"], run_dir / "test.log", env)


def smoke(run_dir: Path, env: dict[str, str]) -> None:
    execute(["docker", "compose", "run", "--rm", "-T", "--interactive=false", "--no-deps", "buildchecker", "python", "-m", "buildchecker", "smoke"], run_dir / "smoke.json", env, run_dir / "smoke.stderr.log")
    data = json.loads((run_dir / "smoke.json").read_text(encoding="utf-8"))
    if not data.get("passed"):
        raise RuntimeError("smoke result is not passed; see smoke.json")


def scan(run_dir: Path, env: dict[str, str]) -> None:
    image = f"e4-buildchecker:{env['STUDENT_ID']}"
    execute([sys.executable, "scripts/e4/secret_scan.py", "--image", image], run_dir / "secret-scan.txt", env)


def shell(run_dir: Path, env: dict[str, str]) -> None:
    ensure_env()
    execute(["docker", "compose", "run", "--rm", "--no-deps", "--user", f"{os.getuid()}:{os.getgid()}", "-e", "HOME=/tmp", "-v", f"{WORK}:/app/work", "buildchecker", "sh"], env=env, timeout=None)


def lock(run_dir: Path, env: dict[str, str]) -> None:
    base_image = subprocess.run(
        ["sed", "-n", "s/^ARG BASE_IMAGE=//p", "services/buildchecker/Dockerfile"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    execute(
        [
            "docker", "run", "--rm", "--user", f"{os.getuid()}:{os.getgid()}", "-e", "HOME=/tmp",
            "-v", f"{ROOT}:/src", "-w", "/src", base_image, "sh", "-c",
            "python3 -m venv /tmp/v && /tmp/v/bin/pip install -q uv==0.12.19 && "
            "/tmp/v/bin/uv pip compile requirements-dev.in --generate-hashes "
            "--python-version 3.13 --python-platform linux -o requirements-dev.lock",
        ],
        run_dir / "lock.log",
        env,
    )


def clean(run_dir: Path, env: dict[str, str]) -> None:
    image = f"e4-buildchecker:{env['STUDENT_ID']}"
    execute(["docker", "image", "rm", image], run_dir / "clean.log", env)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("all", "doctor", "build", "test", "smoke", "scan", "shell", "lock", "clean"))
    args = parser.parse_args()
    run_dir = new_run_dir()
    print(f"E4 证据目录：{run_dir.relative_to(ROOT)}", flush=True)
    try:
        if args.step == "all":
            doctor(run_dir)
            env = environment()
            for step in (build, test, smoke, scan):
                print(f"E4: {step.__name__}", flush=True)
                step(run_dir, env)
        elif args.step == "doctor":
            doctor(run_dir)
        else:
            globals()[args.step](run_dir, environment())
    except (OSError, RuntimeError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f"E4 失败：{error}", file=sys.stderr)
        return 1
    print(f"E4 完成：{run_dir.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
