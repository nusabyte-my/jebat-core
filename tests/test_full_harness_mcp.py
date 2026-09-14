from __future__ import annotations

import json
import pytest
from jebat.features.mcp.mcp_server import MCPServer
from jebat.tools import TOOL_REGISTRY


@pytest.fixture(autouse=True)
def ensure_server_tools():
    server = MCPServer()
    server._ensure_tools_loaded()
    return server


def test_ghost_database_tools_registered():
    """Verify that Ghost database tools are registered in TOOL_REGISTRY."""
    ghost_tools = [t for t in TOOL_REGISTRY.keys() if t.startswith("ghost.") or t.startswith("ghost_")]
    assert len(ghost_tools) >= 14, f"Expected at least 14 Ghost tools, found {len(ghost_tools)}"
    assert "ghost.sql" in TOOL_REGISTRY or "ghost_sql" in TOOL_REGISTRY
    assert "ghost.status" in TOOL_REGISTRY or "ghost_status" in TOOL_REGISTRY
    assert "ghost.create" in TOOL_REGISTRY or "ghost_create" in TOOL_REGISTRY
    assert "ghost.checkpoint.create" in TOOL_REGISTRY or "ghost_checkpoint_create" in TOOL_REGISTRY

def test_agent_execute_tool_registered():
    """Verify that the autonomous agent_execute tool is registered."""
    assert "agent_execute" in TOOL_REGISTRY
    tool = TOOL_REGISTRY["agent_execute"]
    assert "autonomous" in tool.description.lower() or "react" in tool.description.lower()
    assert "task" in tool.schema["properties"]


@pytest.mark.asyncio
async def test_dynamic_mcp_resources_list():
    """Verify that dynamic memory and database resources are announced."""
    server = MCPServer()
    res = await server._handle_resources_list({})
    uris = [item["uri"] for item in res.get("resources", [])]
    assert "jebat://workflow" in uris
    assert "jebat://tools" in uris
    assert "jebat://memory/project" in uris
    assert "jebat://memory/dream" in uris
    assert "jebat://database/schema" in uris


@pytest.mark.asyncio
async def test_dynamic_mcp_resources_read():
    """Verify that dynamic resources return valid structured data."""
    server = MCPServer()

    # 1. Project memory
    proj_res = await server._handle_resources_read({"uri": "jebat://memory/project"})
    assert len(proj_res["contents"]) == 1
    proj_data = json.loads(proj_res["contents"][0]["text"])
    assert "project" in proj_data
    assert "facts" in proj_data

    # 2. Dream state
    dream_res = await server._handle_resources_read({"uri": "jebat://memory/dream"})
    assert len(dream_res["contents"]) == 1
    dream_data = json.loads(dream_res["contents"][0]["text"])
    assert "dream_count" in dream_data

    # 3. Database schema
    schema_res = await server._handle_resources_read({"uri": "jebat://database/schema"})
    assert len(schema_res["contents"]) == 1
    schema_text = schema_res["contents"][0]["text"]
    assert "schema" in schema_text.lower() or "table" in schema_text.lower() or "--" in schema_text

@pytest.mark.asyncio
async def test_jsonrpc_mcp_dispatch_tools_call():
    """Verify full end-to-end JSON-RPC dispatch through handle_request()."""
    server = MCPServer()
    # 1. Initialize server
    init_req = {
        "jsonrpc": "2.0",
        "id": "init-1",
        "method": "initialize",
        "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "test", "version": "1.0"}},
    }
    await server.handle_request(init_req)

    # 2. Call tool
    req = {
        "jsonrpc": "2.0",
        "id": "req-101",
        "method": "tools/call",
        "params": {
            "name": "project_remember",
            "arguments": {
                "fact": "Automated harness unit test memory",
                "category": "other",
                "importance": 0.6,
            },
        },
    }
    resp_raw = await server.handle_request(req)
    assert resp_raw is not None
    resp = json.loads(resp_raw)
    assert "result" in resp
    content = resp["result"]["content"][0]["text"]
    assert "stored" in content
