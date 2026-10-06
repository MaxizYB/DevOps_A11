import json
import subprocess
from pathlib import Path

import pytest

from buildchecker.cli import main, opened_header
from scripts.e4.secret_scan import findings, workspace_files


def test_version(capsys):
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip() == "0.4.0"


def test_opened_header_accepts_successful_open():
    assert opened_header('openat(AT_FDCWD, "config.h", O_RDONLY) = 3')


def test_opened_header_rejects_failed_open():
    assert not opened_header('openat(AT_FDCWD, "config.h", O_RDONLY) = -1 ENOENT')


def test_missing_fixture_reports_failure(capsys, tmp_path: Path):
    assert main(["smoke", "--fixture", str(tmp_path)]) == 1
    assert json.loads(capsys.readouterr().out)["passed"] is False


def test_permission_error_reports_json(monkeypatch, capsys):
    from buildchecker import cli

    def denied(fixture):
        raise PermissionError(13, "Permission denied", "/tmp/project/app")

    monkeypatch.setattr(cli, "smoke", denied)
    assert main(["smoke"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["passed"] is False
    assert result["error_type"] == "PermissionError"
    assert "tmpfs" in result["hint"]


def test_secret_finding_is_redacted():
    fake = "sk-" + "demo" + "1234567890abcdefghijk"
    result = findings("demo", f'api_key = "{fake}"\n'.encode())
    assert result
    assert "sk-d" in result[0]
    assert "demo1234567890" not in result[0]


@pytest.mark.parametrize("ending", [b"\n", b"\r\n", b""])
def test_private_key_header_is_detected_without_leaking_value(ending):
    header = b"-----BEGIN " + b"PRIVATE KEY-----"
    result = findings("demo", header + ending)
    assert result
    assert "PRIVATE KEY" not in result[0]


def test_private_key_source_example_is_not_reported():
    source = b'result = findings("demo", b"-----BEGIN ' + b'PRIVATE KEY-----\\n")\n'
    assert findings("workspace/test_cli.py", source) == []
    assert findings("git-history", b"+" + source) == []


def test_private_key_in_history_is_reported():
    patch = b"+-----BEGIN " + b"PRIVATE KEY-----\n+ZGVtbw==\n"
    assert findings("git-history", patch)


def test_private_key_in_image_env_is_reported(monkeypatch, tmp_path: Path):
    from scripts.e4 import secret_scan

    private_env = "KEY=-----BEGIN " + "PRIVATE KEY-----\nZGVtbw==\n"

    def output(args, required=True):
        if args[:3] == ["docker", "image", "inspect"]:
            return json.dumps([private_env]).encode()
        return b""

    monkeypatch.setattr(secret_scan, "ROOT", tmp_path)
    monkeypatch.setattr(secret_scan, "run", output)
    assert any("image-env" in finding for finding in secret_scan.scan("test-image"))


def test_local_env_is_not_scanned_as_a_leak(monkeypatch, tmp_path: Path):
    from scripts.e4 import secret_scan

    fake = "sk-" + "demo" + "1234567890abcdefghijk"
    (tmp_path / ".env").write_text(f'api_key="{fake}"\n')
    (tmp_path / "leak-demo.txt").write_text(f'api_key="{fake}"\n')
    monkeypatch.setattr(secret_scan, "ROOT", tmp_path)
    assert [path.name for path in workspace_files()] == ["leak-demo.txt"]


def test_workspace_includes_untracked_files_and_excludes_ignored_files(monkeypatch, tmp_path: Path):
    from scripts.e4 import secret_scan

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text("*.zip\n")
    (tmp_path / "lab.zip").write_bytes(b"local package")
    (tmp_path / "leak-demo.txt").write_text("untracked file\n")
    monkeypatch.setattr(secret_scan, "ROOT", tmp_path)
    assert {path.name for path in workspace_files()} == {".gitignore", "leak-demo.txt"}
