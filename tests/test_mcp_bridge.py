"""Tests for the MCP bridge (mcp_describe / mcp_call) and the from-mcp foundry.

Everything runs against tests/mock_mcp_server.py through a temp config file
(JEBAT_MCP_CONFIG), so no real MCP server or provider is touched.
"""

import json
import sys
import textwrap
from pathlib import Path

import pytest

from jebat_cli_new import mcp_bridge
from jebat_cli_new.agentix_auto import AgentixAutoError
from jebat_cli_new.agentix_mcp import from_mcp

MOCK_SERVER = Path(__file__).resolve().parent / "mock_mcp_server.py"


@pytest.fixture()
def mock_config(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        textwrap.dedent(
            f"""\
            mcp:
              mock:
                transport: stdio
                command: {sys.executable}
                args: ["{MOCK_SERVER.as_posix()}"]
                enabled: true
                timeout: 20
              gated:
                transport: stdio
                command: {sys.executable}
                args: ["{MOCK_SERVER.as_posix()}"]
                enabled: true
                timeout: 20
                require_approval: true
              offline:
                transport: stdio
                command: {sys.executable}
                args: ["{MOCK_SERVER.as_posix()}"]
                enabled: false
            """
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("JEBAT_MCP_CONFIG", str(cfg))
    return cfg


def test_list_servers_reports_transport_and_flags(mock_config):
    names = {s["name"]: s for s in mcp_bridge.list_servers()}
    assert set(names) == {"mock", "gated", "offline"}
    assert names["mock"]["transport"] == "stdio"
    assert names["mock"]["enabled"] is True
    assert names["offline"]["enabled"] is False
    assert names["gated"]["require_approval"] is True
    assert mcp_bridge.server_requires_approval("gated") is True
    assert mcp_bridge.server_requires_approval("mock") is False


def test_describe_lists_tools_with_annotations(mock_config):
    info = mcp_bridge.describe_server("mock")
    tools = {t["name"]: t for t in info["tools"]}
    assert info["tool_count"] == 2
    assert set(tools) == {"echo", "write_note"}
    assert tools["echo"]["read_only_hint"] is True
    assert tools["write_note"]["read_only_hint"] is False
    assert tools["write_note"]["required"] == ["path", "text"]
    assert info["server_info"]["name"] == "mock-mcp"


def test_call_echo_returns_text(mock_config):
    out = mcp_bridge.call_tool("mock", "echo", {"text": "hello mcp"})
    assert out["is_error"] is False
    assert out["text"] == "hello mcp"


def test_call_write_note_writes_file(mock_config, tmp_path):
    target = tmp_path / "note.txt"
    out = mcp_bridge.call_tool("mock", "write_note", {"path": str(target), "text": "hi"})
    assert out["is_error"] is False
    assert target.read_text(encoding="utf-8") == "hi"


def test_call_unknown_tool_reports_error_text(mock_config):
    out = mcp_bridge.call_tool("mock", "nope", {})
    assert out["is_error"] is True
    assert "unknown tool" in out["text"]


def test_execute_tool_surface(mock_config, monkeypatch):
    from jebat_cli_new.tools import HANDLERS, TOOL_DEFINITIONS, execute_tool

    assert "mcp_describe" in HANDLERS and "mcp_call" in HANDLERS
    names = {d["name"] for d in TOOL_DEFINITIONS}
    assert {"mcp_describe", "mcp_call"} <= names

    described = execute_tool("mcp_describe", {"server": "mock"}, yolo=True)
    assert "echo" in described and "write_note" in described

    called = execute_tool(
        "mcp_call", {"server": "mock", "tool": "echo", "arguments": {"text": "via execute"}},
        yolo=True,
    )
    assert "via execute" in called


def test_execute_tool_unknown_server_is_error_string(mock_config):
    from jebat_cli_new.tools import execute_tool

    out = execute_tool("mcp_call", {"server": "ghost", "tool": "x", "arguments": {}}, yolo=True)
    assert out.startswith("[MCP_ERROR]")
    assert "unknown MCP server" in out


# ── from-mcp foundry ─────────────────────────────────────────────────────────

VALID_DRAFT = {
    "name": "mock-ops",
    "description": "Runs mock operations over the mock MCP server. Use for mock, echo, or note tasks.",
    "doctrine": (
        "# Mock-ops doctrine\n\n"
        "Mission: exercise the mock server with evidence for every claim.\n\n"
        "Method:\n1. mcp_describe the server.\n2. mcp_call echo for the input text.\n\n"
        "Output: note.md with the echoed text and the exact calls made."
    ),
    "tools": ["read_file", "write_file"],
    "max_iterations": 8,
    "jailed": False,
}

SNAPSHOT = {
    "server": "mock",
    "protocol": "2024-11-05",
    "server_info": {"name": "mock-mcp", "version": "0.0.1"},
    "tool_count": 2,
    "tools": [
        {"name": "echo", "description": "Echo back the provided text.", "required": ["text"], "read_only_hint": True},
        {"name": "write_note", "description": "Write text to a file path.", "required": ["path", "text"], "read_only_hint": False},
    ],
}


def test_from_mcp_with_injected_draft(tmp_path):
    outcome = from_mcp(
        "mock",
        target_dir=tmp_path,
        draft=VALID_DRAFT,
        tools_snapshot=SNAPSHOT,
    )
    spec = outcome["spec"]
    assert spec["name"] == "mock-ops"
    assert "mcp_describe" in spec["tools"] and "mcp_call" in spec["tools"]
    sol = Path(outcome["path"])
    assert (sol / "mcp-snapshot.json").is_file()
    snapshot = json.loads((sol / "mcp-snapshot.json").read_text(encoding="utf-8"))
    assert snapshot["tool_count"] == 2
    doctrine = (sol / "agent.md").read_text(encoding="utf-8")
    assert "mcp_call" in doctrine and "mcp-snapshot.json" in doctrine
    manifest = (sol / "agentix.yaml").read_text(encoding="utf-8")
    assert "mcp_describe" in manifest and "mcp_call" in manifest
    assert outcome["build"]["manifest_sha256"]


def test_from_mcp_introspects_live_server(mock_config, tmp_path):
    # No snapshot injection: the real (mock) server is spawned for tools/list.
    outcome = from_mcp("mock", target_dir=tmp_path, draft=VALID_DRAFT)
    assert outcome["mcp"]["tool_count"] == 2
    assert (Path(outcome["path"]) / "mcp-snapshot.json").is_file()


def test_from_mcp_unknown_server_raises(mock_config, tmp_path):
    with pytest.raises(AgentixAutoError):
        from_mcp("nope", target_dir=tmp_path, draft=VALID_DRAFT)


def test_from_mcp_rejects_bad_deploy(tmp_path):
    with pytest.raises(AgentixAutoError):
        from_mcp("mock", target_dir=tmp_path, deploy="vps", draft=VALID_DRAFT, tools_snapshot=SNAPSHOT)
    assert list(tmp_path.iterdir()) == []
