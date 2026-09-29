import json
from pathlib import Path

from buildchecker.cli import main, opened_header
from scripts.e4.secret_scan import findings


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


def test_secret_finding_is_redacted():
    fake = "sk-" + "demo" + "1234567890abcdefghijk"
    result = findings("demo", f'api_key = "{fake}"\n'.encode())
    assert result
    assert "sk-d" in result[0]
    assert "demo1234567890" not in result[0]
