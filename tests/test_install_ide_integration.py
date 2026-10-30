"""Integration checks for opt-in IDE pairing during JEBAT installation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "install-ide-integration.py"


def run(home: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--home", str(home), "--command", "jebat", "--arg", "mcp", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_auto_detects_kiro_and_preserves_existing_configuration(tmp_path: Path) -> None:
    path = tmp_path / ".kiro" / "settings" / "mcp.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"theme": "dark", "mcpServers": {"other": {"command": "other"}}}))
    result = run(tmp_path)
    assert result.returncode == 0, result.stderr
    config = json.loads(path.read_text())
    assert config["theme"] == "dark"
    assert config["mcpServers"]["other"] == {"command": "other"}
    assert config["mcpServers"]["jebat"]["args"] == ["mcp"]
    assert list(path.parent.glob("mcp.json.bak-jebat-*"))


def test_opt_out_detects_nothing_and_writes_nothing(tmp_path: Path) -> None:
    result = run(tmp_path)
    assert result.returncode == 0
    assert "no files changed" in result.stdout
    assert list(tmp_path.iterdir()) == []


def test_invalid_json_is_not_overwritten(tmp_path: Path) -> None:
    path = tmp_path / ".kiro" / "settings" / "mcp.json"
    path.parent.mkdir(parents=True)
    path.write_text("{broken")
    result = run(tmp_path)
    assert result.returncode == 1
    assert path.read_text() == "{broken"
    assert not list(path.parent.glob("*.bak-jebat-*"))


def test_mcp_pair_cli_uses_same_safe_merge(tmp_path: Path, monkeypatch) -> None:
    from jebat_cli_new.mcp_command import run_mcp_command

    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    (tmp_path / ".kiro" / "settings").mkdir(parents=True)
    assert run_mcp_command(["pair", "--ide", "kiro"]) == 0
    path = tmp_path / ".kiro" / "settings" / "mcp.json"
    config = json.loads(path.read_text())
    assert config["mcpServers"]["jebat"]["command"] == "jebat"
    assert config["mcpServers"]["jebat"]["args"] == ["mcp", "serve", "--transport", "stdio"]
    path.unlink()
    assert run_mcp_command(["pair", "--list"]) == 0
    assert not path.exists()
