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

    response = json.loads(completed.stdout.strip().splitlines()[-1])
    assert completed.returncode == 0
    assert response["result"]["protocolVersion"] == "2025-03-26"
