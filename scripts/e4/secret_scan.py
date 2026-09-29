"""Scan staged/tracked content, repository history, and the built image."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PATTERNS = (
    re.compile(rb"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{36,}"),
    re.compile(rb"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(rb"(?i)(?:api[_-]?key|access[_-]?token|secret|password|passwd)\s*[:=]\s*['\"]?([A-Za-z0-9_./+=-]{20,})"),
)


def run(args: list[str], required: bool = True) -> bytes:
    result = subprocess.run(args, cwd=ROOT, capture_output=True)
    if required and result.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(args[:2])}")
    return result.stdout


def findings(label: str, data: bytes) -> list[str]:
    if b"\0" in data:
        return []
    matches: list[str] = []
    for pattern in PATTERNS:
        for match in pattern.finditer(data):
            secret = match.group(1) if match.lastindex else match.group(0)
            line = data.count(b"\n", 0, match.start()) + 1
            matches.append(f"{label}:{line}: {secret[:4].decode('ascii', 'replace')}… (redacted)")
    return matches


def workspace_files() -> list[Path]:
    """Return files in the checkout, excluding Git internals and E4 output."""
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if ".git" in relative.parts or "work" in relative.parts:
            continue
        if path.name == ".env" or (path.name.startswith(".env.") and path.name != ".env.example"):
            continue
        files.append(path)
    return files


def scan(image: str) -> list[str]:
    issues: list[str] = []
    paths = [p for p in run(["git", "ls-files", "--cached", "-z"]).split(b"\0") if p]
    if any(Path(p.decode()).name == ".env" or (Path(p.decode()).name.startswith(".env.") and Path(p.decode()).name != ".env.example") for p in paths):
        issues.append("tracked .env file")
    env_file = ROOT / ".env"
    if env_file.exists() and env_file.stat().st_mode & 0o077:
        issues.append(".env permissions are broader than 600")
    for local in workspace_files():
        path = local.relative_to(ROOT).as_posix()
        issues.extend(findings(f"workspace/{path}", local.read_bytes()))
    for raw_path in paths:
        path = raw_path.decode("utf-8", "surrogateescape")
        staged = run(["git", "show", f":{path}"], required=False)
        issues.extend(findings(f"index/{path}", staged))
    issues.extend(findings("git-history", run(["git", "log", "--all", "--format=", "-p"])))
    issues.extend(findings("image-history", run(["docker", "history", "--no-trunc", "--format", "{{.CreatedBy}}", image])))
    issues.extend(findings("image-env", run(["docker", "image", "inspect", "--format", "{{json .Config.Env}}", image])))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    args = parser.parse_args()
    try:
        issues = scan(args.image)
    except (OSError, RuntimeError) as error:
        print(f"密钥检查：无法完成（{error}）")
        return 2
    if issues:
        print("密钥检查：发现问题")
        for issue in sorted(set(issues)):
            print(issue)
        return 1
    print("密钥检查：未发现问题")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
