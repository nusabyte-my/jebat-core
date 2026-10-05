"""config import tests — source parsing, conversion, merge, CLI."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from jebat_cli_new.config_import import (
    _convert,
    _load_source,
    _normalize_timeout,
    merge_servers,
    run_config_command,
)


def _write_source(tmp_path, payload, name="source.json"):
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


# ── Normalization ───────────────────────────────────────────────────

def test_convert_claude_stdio_entry():
    server = _convert(
        "context7",
        {"command": "npx", "args": ["-y", "@upstash/context7-mcp"], "env": {"API_KEY": "${CONTEXT7_KEY}"}},
    )
    assert server["transport"] == "stdio"
    assert server["command"] == "npx"
    assert server["args"] == ["-y", "@upstash/context7-mcp"]
    assert server["env"] == {"API_KEY": "${CONTEXT7_KEY}"}  # templates preserved
    assert server["timeout"] == 30


def test_convert_opencode_array_command():
    server = _convert(
        "skills",
        {"type": "local", "command": ["python", "server.py", "--port", "8123"], "environment": {"PYTHONUTF8": "1"}},
    )
    assert server["transport"] == "stdio"
    assert server["command"] == "python"
    assert server["args"] == ["server.py", "--port", "8123"]
    assert server["env"] == {"PYTHONUTF8": "1"}


def test_convert_remote_url_entry():
    server = _convert("jebat-mcp", {"type": "remote", "url": "https://jebat.online/mcp", "headers": {"X-API-Key": "k"}})
    assert server["transport"] == "http"
    assert server["url"] == "https://jebat.online/mcp"
    assert server["headers"] == {"X-API-Key": "k"}


def test_timeout_ms_units_normalized():
    assert _normalize_timeout(60000) == 60  # ms → s
    assert _normalize_timeout(45) == 45     # already seconds
    assert _normalize_timeout("junk") == 30
    assert _normalize_timeout(-5) == 30


def test_opencode_env_template_style_converted():
    server = _convert("srv", {"command": "x", "env": {"TOKEN": "{env:MY_TOKEN}"}})
    assert server["env"]["TOKEN"] == "${MY_TOKEN}"


# ── Source loading ──────────────────────────────────────────────────

def test_load_source_sniffs_mcpServers_shape(tmp_path):
    source = _write_source(tmp_path, {"mcpServers": {"srv": {"command": "uvx", "args": ["x"]}}})
    kind, path, servers = _load_source("claude", str(source))
    assert "claude" in kind
    assert set(servers) == {"srv"}


def test_load_source_sniffs_opencode_shape(tmp_path):
    source = _write_source(tmp_path, {"mcp": {"srv": {"type": "local", "command": ["n", "x"]}}})
    kind, path, servers = _load_source("opencode", str(source))
    assert kind == "opencode"
    assert set(servers) == {"srv"}


def test_load_source_missing_path_raises(tmp_path):
    import pytest

    with pytest.raises(FileNotFoundError):
        _load_source("claude", str(tmp_path / "nope.json"))


# ── Merge ───────────────────────────────────────────────────────────

def _config_with_existing(tmp_path, names):
    config_path = tmp_path / "config.yaml"
    config = {
        "mcp": {
            "servers": [
                {"name": n, "transport": "stdio", "command": "keep", "timeout": 30} for n in names
            ]
        }
    }
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return config_path


def test_merge_adds_and_skips_collisions(tmp_path):
    config_path = _config_with_existing(tmp_path, ["existing"])
    incoming = [
        {"name": "new-srv", "transport": "stdio", "command": "npx", "timeout": 30},
        {"name": "existing", "transport": "stdio", "command": "other", "timeout": 30},
    ]
    report = merge_servers(incoming, config_path, backup=False)
    assert report["added"] == ["new-srv"]
    assert report["skipped"] == ["existing"]
    saved = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    kept = next(s for s in saved["mcp"]["servers"] if s["name"] == "existing")
    assert kept["command"] == "keep"  # untouched without overwrite


def test_merge_overwrite_replaces_entry(tmp_path):
    config_path = _config_with_existing(tmp_path, ["srv"])
    incoming = [{"name": "srv", "transport": "stdio", "command": "replacement", "timeout": 10}]
    report = merge_servers(incoming, config_path, overwrite=True, backup=False)
    assert report["replaced"] == ["srv"]
    saved = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    entries = [s for s in saved["mcp"]["servers"] if s["name"] == "srv"]
    assert len(entries) == 1
    assert entries[0]["command"] == "replacement"


def test_merge_writes_timestamped_backup(tmp_path):
    config_path = _config_with_existing(tmp_path, [])
    incoming = [{"name": "ctx", "transport": "stdio", "command": "npx", "timeout": 30}]
    merge_servers(incoming, config_path, backup=True)
    assert list(tmp_path.glob("config.yaml.bak-*-import"))


# ── CLI end-to-end ──────────────────────────────────────────────────

def test_cli_import_writes_config(tmp_path, capsys):
    source = _write_source(tmp_path, {"mcpServers": {"ctx": {"command": "npx", "args": ["x"]}}})
    config_path = tmp_path / "config.yaml"

    rc = run_config_command(
        ["import", "-s", "claude", "--path", str(source), "--config", str(config_path)]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "added" in out and "ctx" in out
    saved = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert saved["mcp"]["servers"][0]["name"] == "ctx"


def test_cli_dry_run_writes_nothing(tmp_path, capsys):
    source = _write_source(tmp_path, {"mcpServers": {"ctx": {"command": "npx", "args": ["x"]}}})
    config_path = tmp_path / "config.yaml"

    rc = run_config_command(
        ["import", "-s", "claude", "--path", str(source), "--config", str(config_path), "--dry-run"]
    )
    assert rc == 0
    assert "dry" in capsys.readouterr().out.lower()
    assert not config_path.exists()


def test_cli_second_run_skips_collisions(tmp_path, capsys):
    source = _write_source(tmp_path, {"mcpServers": {"ctx": {"command": "npx", "args": ["x"]}}})
    config_path = tmp_path / "config.yaml"
    base = ["import", "-s", "claude", "--path", str(source), "--config", str(config_path)]

    assert run_config_command(base) == 0
    capsys.readouterr()
    assert run_config_command(base) == 0
    out = capsys.readouterr().out
    assert "skipped" in out and "ctx" in out
