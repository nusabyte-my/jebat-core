"""Contract tests for the JEBAT MCP protocol surface."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from jebat.features.mcp import mcp_resources, mcp_server
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


@pytest.mark.anyio
async def test_skills_are_listed_and_readable_as_skill_resources() -> None:
    """Every SKILL.md is exposed as skill://<store>/<name> and readable back."""
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

    skill_uris = sorted(
        item["uri"]
        for item in resources["result"]["resources"]
        if item["uri"].startswith("skill://")
    )
    assert skill_uris, "expected at least one skill:// resource"
    assert any(uri.startswith("skill://tokguru/") for uri in skill_uris)

    templates = {t["uriTemplate"] for t in resources["result"]["resourceTemplates"]}
    assert "skill://{path}" in templates

    # Read the first skill back — content must be the raw SKILL.md.
    read = json.loads(
        await server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "resources/read",
                "params": {"uri": skill_uris[0]},
            }
        )
        or "{}"
    )
    contents = read["result"]["contents"]
    assert contents and contents[0]["mimeType"] == "text/markdown"
    assert contents[0]["text"].startswith("---")
    assert "name:" in contents[0]["text"]

    # Unknown skill URIs report a readable error, not an empty result.
    missing = json.loads(
        await server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "resources/read",
                "params": {"uri": "skill://tokguru/does-not-exist"},
            }
        )
        or "{}"
    )
    assert "Skill not found" in missing["result"]["contents"][0]["text"]


@pytest.mark.anyio
async def test_wiki_pages_are_listed_and_readable_as_wiki_resources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`wiki://` mirrors `skill://`: one resource per page file, plus a template.

    Pages are read from the markdown files rather than WikiStore's index, since
    the tool surface writes those files without updating that index.
    """
    wiki_root = tmp_path / "wiki"
    pages = wiki_root / "pages"
    pages.mkdir(parents=True)
    (pages / "erawan-qpos-operational-invariants.md").write_text(
        "# Wiki: Erawan QPOS Operational Invariants\n"
        "**Tags**: erawan-qsys, invariants\n"
        "**Updated**: 2026-09-23\n\n"
        "Group checkout uses a running number.\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("JEBAT_WIKI_DIR", str(wiki_root))
    # The index cache lives in mcp_resources since the P2-4 split.
    monkeypatch.setattr(mcp_resources, "_WIKI_INDEX", None)

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

    listed = resources["result"]["resources"]
    wiki_uris = [item["uri"] for item in listed if item["uri"].startswith("wiki://")]
    assert wiki_uris == ["wiki://erawan-qpos-operational-invariants"]

    entry = next(i for i in listed if i["uri"] == wiki_uris[0])
    assert entry["name"] == "Wiki: Erawan QPOS Operational Invariants"
    assert entry["mimeType"] == "text/markdown"
    assert "erawan-qsys" in entry["description"]

    templates = {t["uriTemplate"] for t in resources["result"]["resourceTemplates"]}
    assert "wiki://{slug}" in templates

    read = json.loads(
        await server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "resources/read",
                "params": {"uri": wiki_uris[0]},
            }
        )
        or "{}"
    )
    contents = read["result"]["contents"]
    assert contents and contents[0]["mimeType"] == "text/markdown"
    assert contents[0]["text"].startswith("# Wiki: Erawan QPOS")

    # Clients do not always have the slug; a title must resolve too.
    by_title = json.loads(
        await server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "resources/read",
                "params": {"uri": "wiki://Erawan QPOS Operational Invariants"},
            }
        )
        or "{}"
    )
    assert "running number" in by_title["result"]["contents"][0]["text"]

    # Unknown pages report a readable error, not an empty result.
    missing = json.loads(
        await server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "resources/read",
                "params": {"uri": "wiki://does-not-exist"},
            }
        )
        or "{}"
    )
    assert "Wiki page not found" in missing["result"]["contents"][0]["text"]


@pytest.mark.anyio
async def test_default_registry_exposes_jev_laya_and_skill_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With no allowlist configured, the full registry — including the Jev/Laya
    typed-decision (advisor) tools and skill_manage — is what clients see."""
    monkeypatch.delenv("JEBAT_MCP_TOOLS_ALLOW", raising=False)
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

    assert {
        "advisor_classify",
        "advisor_verify",
        "advisor_score",
        "advisor_decide",
        "advisor_gate",
        "skill_manage",
    } <= names
    assert len(names) >= 100, "unrestricted tools/list should expose the full registry"
