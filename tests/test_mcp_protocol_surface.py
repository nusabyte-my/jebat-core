"""Contract tests for the JEBAT MCP protocol surface."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from jebat.features.mcp.mcp_server import MCPServer
from jebat.tools import TOOL_REGISTRY, ToolDef

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.anyio
async def test_initialize_advertises_context_surfaces() -> None:
    server = MCPServer()

    response = await server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "clientInfo": {"name": "test-client", "version": "1"},
            },
        }
    )

    payload = json.loads(response or "{}")
    capabilities = payload["result"]["capabilities"]
    assert capabilities["resources"]["subscribe"] is True
    assert capabilities["prompts"]["listChanged"] is True
    assert payload["result"]["protocolVersion"] == "2025-03-26"


@pytest.mark.anyio
async def test_resources_and_prompts_provide_workflow_context() -> None:
    server = MCPServer()
    await server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-06-18"},
        }
    )

    resources = json.loads(
        await server.handle_request(
            {"jsonrpc": "2.0", "id": 2, "method": "resources/list", "params": {}}
        )
        or "{}"
    )
    prompts = json.loads(
        await server.handle_request(
            {"jsonrpc": "2.0", "id": 3, "method": "prompts/list", "params": {}}
        )
        or "{}"
    )

    assert {item["uri"] for item in resources["result"]["resources"]} >= {
        "jebat://workflow",
        "jebat://tools",
    }
    assert {item["name"] for item in prompts["result"]["prompts"]} >= {
        "plan-act-verify-remember",
    }


@pytest.mark.anyio
async def test_dangerous_tool_call_returns_machine_readable_approval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = MCPServer()
    await server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-06-18"},
        }
    )

    async def dangerous_handler() -> str:
        return "must not execute"

    monkeypatch.setitem(
        TOOL_REGISTRY,
        "dangerous-test-tool",
        ToolDef(
            name="dangerous-test-tool",
            handler=dangerous_handler,
            safety_tier="dangerous",
        ),
    )
    response = await server._handle_tools_call(  # noqa: SLF001
        {"name": "dangerous-test-tool", "arguments": {}}
    )

    assert response["isError"] is True
    assert response["structuredContent"]["status"] == "approval_required"
    assert response["structuredContent"]["safetyTier"] == "dangerous"


def test_stdio_entrypoint_completes_initialize_handshake() -> None:
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2025-03-26"},
    }

    completed = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "jebat-mcp"), "--transport", "stdio"],
        input=json.dumps(request) + "\n",
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        check=False,
        timeout=30,
    )

    # The server may push unsolicited notifications after the handshake
    # (e.g. notifications/advisorReady), so select the response by id rather
    # than taking the last line — that is what a conforming client does.
    assert completed.returncode == 0
    frames = [json.loads(line) for line in completed.stdout.strip().splitlines() if line.strip()]
    response = next(f for f in frames if f.get("id") == 1)
    assert response["result"]["protocolVersion"] == "2025-03-26"


def test_canonical_cli_mcp_serve_completes_initialize_handshake() -> None:
    """`jebat mcp serve` (the command in every shipped IDE config) must speak
    MCP on stdout without printing a banner or dropping into the REPL."""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2025-03-26"},
    }

    completed = subprocess.run(
        [sys.executable, "-m", "jebat_cli_new", "mcp", "serve", "--transport", "stdio"],
        input=json.dumps(request) + "\n",
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        check=False,
        timeout=60,
    )

    assert completed.returncode == 0
    frames = [json.loads(line) for line in completed.stdout.strip().splitlines() if line.strip()]
    response = next(f for f in frames if f.get("id") == 1)
    assert response["result"]["serverInfo"]["name"] == "jebat-mcp-server"
    assert response["result"]["protocolVersion"] == "2025-03-26"


@pytest.mark.anyio
async def test_tools_allowlist_trims_tools_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """JEBAT_MCP_TOOLS_ALLOW exposes only the listed tools; unset means all."""
    monkeypatch.setitem(
        TOOL_REGISTRY,
        "allowlist-visible-tool",
        ToolDef(name="allowlist-visible-tool", description="in"),
    )
    monkeypatch.setitem(
        TOOL_REGISTRY,
        "allowlist-hidden-tool",
        ToolDef(name="allowlist-hidden-tool", description="out"),
    )
    monkeypatch.setenv("JEBAT_MCP_TOOLS_ALLOW", "allowlist-visible-tool, other")

    server = MCPServer()
    await server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-06-18"},
        }
    )
    listed = json.loads(
        await server.handle_request(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        )
        or "{}"
    )
    names = {tool["name"] for tool in listed["result"]["tools"]}

    assert "allowlist-visible-tool" in names
    assert "allowlist-hidden-tool" not in names
    # Pagination must stay consistent with the trimmed set.
    assert "nextCursor" not in listed["result"]

    # Calls to trimmed tools are not found — same as unknown tools.
    call = await server._handle_tools_call(  # noqa: SLF001
        {"name": "allowlist-hidden-tool", "arguments": {}}
    )
    assert call["isError"] is True
    assert "not found" in call["content"][0]["text"].lower()

    # Unset env var restores the full registry.
    monkeypatch.delenv("JEBAT_MCP_TOOLS_ALLOW")
    server2 = MCPServer()
    await server2.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-06-18"},
        }
    )
    full = json.loads(
        await server2.handle_request(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        )
        or "{}"
    )
    full_names = {tool["name"] for tool in full["result"]["tools"]}
    assert "allowlist-hidden-tool" in full_names
