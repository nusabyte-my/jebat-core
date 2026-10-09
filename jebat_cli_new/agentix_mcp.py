"""Agentix x MCP — draft a governed solution FROM a configured MCP server.

`jebat agentix from-mcp <server>` introspects the server's tool catalog and
asks the provider to write a solution around it. The solution's llm_tools
gain `mcp_describe` + `mcp_call`, so the ReAct loop drives the MCP server as
a first-class instrument. A tool-catalog snapshot (`mcp-snapshot.json`) is
stored next to the doctrine for diffing when the server updates.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from jebat_cli_new import mcp_bridge
from jebat_cli_new.agentix import _build, _deploy_local, _deploy_mcp
from jebat_cli_new.agentix_auto import (
    AgentixAutoError,
    complete_json,
    normalize_spec,
    write_solution,
)

MCP_TOOLS = ("mcp_describe", "mcp_call")
MAX_CATALOG_LINES = 90
MAX_DESC_CHARS = 140

_SYSTEM = (
    "You are JEBAT's solution architect. You wrap ONE MCP server into a small, "
    "governed agent solution. Ground every instruction in the tool catalog you "
    "are given; never invent tool names."
)

_INSTRUCTIONS = """\
Design ONE agent solution whose instrument is the MCP server {server!r}.

The solution's ReAct loop has these tools: read_file, write_file, search_files,
terminal, list_dir, mcp_describe (inspect a server's tool list with required
parameters) and mcp_call(server, tool, arguments) (invoke one server tool).

SERVER CATALOG ({tool_count} tools, snapshot):
{catalog}

Reply with ONLY a JSON object (no prose, no code fences) with exactly these keys:
- "name": kebab-case id 3-32 chars starting with a letter (e.g. "{example_name}").
- "description": one or two sentences for routing; end with a "Use for ..." clause. No double quotes inside.
- "doctrine": markdown for agent.md. Start with "# <Name> doctrine", then a "Mission:" line, a numbered "Method:" that names the EXACT server tools to call (call mcp_describe first when a tool's schema is unclear), and an "Output:" contract (what artifact is written where). Keep 120-1400 chars; no double quotes needed.
- "max_iterations": integer 6-20 (default 12).
- "jailed": true only if the solution should be confined to its own workspace/ directory; false when it works on the host repo/target.
"""


def _catalog_block(tools: List[Dict[str, Any]]) -> str:
    lines = []
    for tool in tools[:MAX_CATALOG_LINES]:
        name = str(tool.get("name") or "?")
        desc = " ".join(str(tool.get("description") or "").split())[:MAX_DESC_CHARS]
        required = tool.get("required") or []
        req = f" (required: {', '.join(map(str, required))})" if required else ""
        lines.append(f"- {name}{req}: {desc}")
    if len(tools) > MAX_CATALOG_LINES:
        lines.append(f"- ... {len(tools) - MAX_CATALOG_LINES} more tools (see mcp-snapshot.json)")
    return "\n".join(lines) or "- (server reported no tools)"


def draft_spec_from_mcp(
    server: str,
    tools: List[Dict[str, Any]],
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """One provider call: server + tool catalog -> drafted spec (raw)."""
    example = (server.lower().replace("_", "-") + "-ops")[:32].strip("-") or "mcp-ops"
    prompt = (
        _SYSTEM
        + "\n\n"
        + _INSTRUCTIONS.replace("{server}", server)
        .replace("{tool_count}", str(len(tools)))
        .replace("{catalog}", _catalog_block(tools))
        .replace("{example_name}", example)
    )
    return complete_json(prompt, provider=provider, model=model)


def from_mcp(
    server: str,
    *,
    name: Optional[str] = None,
    target_dir: Path | str = ".",
    deploy: str = "none",
    provider: Optional[str] = None,
    model: Optional[str] = None,
    draft: Optional[Dict[str, Any]] = None,
    tools_snapshot: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Introspect -> draft -> normalize -> write -> build (-> deploy).

    `draft` and `tools_snapshot` injection keep tests model-free and
    connection-free; the live path introspects the configured server.
    """
    server = str(server or "").strip()
    if not server:
        raise AgentixAutoError("server name is required (see `jebat agentix from-mcp --list`)")
    deploy = (deploy or "none").strip().lower()
    if deploy not in ("none", "local", "mcp", ""):
        raise AgentixAutoError(f"unknown deploy target {deploy!r} (none|local|mcp)")

    if tools_snapshot is not None:
        snapshot = tools_snapshot
    else:
        try:
            snapshot = mcp_bridge.describe_server(server)
        except mcp_bridge.MCPBridgeError as exc:
            raise AgentixAutoError(f"introspection failed: {exc}") from exc

    tools = list(snapshot.get("tools") or [])
    raw = (
        draft
        if draft is not None
        else draft_spec_from_mcp(server, tools, provider=provider, model=model)
    )
    spec = normalize_spec(raw, objective=f"MCP server {server!r}", name_override=name)
    for tool in MCP_TOOLS:
        if tool not in spec["tools"]:
            spec["tools"].append(tool)

    stamp = time.strftime("%Y-%m-%d")
    spec["doctrine"] = spec["doctrine"].rstrip() + (
        "\n\n---\n"
        f"Instrument: MCP server `{server}` ({len(tools)} tools as of {stamp}; catalog "
        "snapshot in `mcp-snapshot.json`). Drive it with "
        f'`mcp_describe("{server}")` for schemas, then '
        f'`mcp_call("{server}", "<tool>", {{ ... }})`. Prefer these tools over '
        "ad-hoc shell; never invent tool names."
    )

    sol = write_solution(spec, Path(target_dir))
    (sol / "mcp-snapshot.json").write_text(
        json.dumps(
            {
                "server": server,
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "protocol": snapshot.get("protocol"),
                "server_info": snapshot.get("server_info"),
                "tool_count": len(tools),
                "tools": tools,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
        newline="\n",
    )
    try:
        info = _build(sol)
    except SystemExit as exc:
        raise AgentixAutoError(
            f"drafted solution failed validation (kept for inspection at {sol}): {exc}"
        ) from exc

    outcome: Dict[str, Any] = {
        "spec": spec,
        "path": str(sol),
        "build": info,
        "mcp": {"server": server, "tool_count": len(tools)},
        "deploy": None,
    }
    if deploy == "local":
        outcome["deploy"] = _deploy_local(sol)
    elif deploy == "mcp":
        outcome["deploy"] = _deploy_mcp(sol)
    return outcome
