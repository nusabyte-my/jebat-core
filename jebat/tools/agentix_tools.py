"""Agentix solution tools — list, create, and deploy agent solutions over MCP.

Exposes the Agentix lifecycle so any connected client (Claude Code, Cursor,
VS Code, jebat itself) can grow new governed solutions without a terminal:

- agentix_list   -> specialist catalog + locally registered solutions (read-only)
- agentix_create -> scaffold from a specialist template, or auto-draft from an
                    objective through the configured provider, then build
- agentix_deploy -> register locally, or return the paste-ready MCP client
                    config that serves the solution as a tool

Creation writes files (and may call a model), so the two write tools sit at
the confirm tier; listing stays auto.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from jebat.tools import register_tool


def _catalog() -> List[Dict[str, str]]:
    from jebat_cli_new.agentix import MANIFEST_NAME, SPECIALISTS_DIR, _load_manifest

    entries: List[Dict[str, str]] = []
    if not SPECIALISTS_DIR.is_dir():
        return entries
    for path in sorted(SPECIALISTS_DIR.iterdir()):
        if not (path / MANIFEST_NAME).is_file():
            continue
        try:
            mf = _load_manifest(path)
        except Exception:  # noqa: BLE001 — skip unreadable catalog entries
            continue
        entries.append(
            {
                "name": str(mf.get("name", path.name)),
                "description": str(mf.get("description", "")).strip(),
            }
        )
    return entries


def _registry() -> Dict[str, Any]:
    import json

    from jebat_cli_new.agentix import REGISTRY_PATH

    if not REGISTRY_PATH.is_file():
        return {}
    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — a corrupt registry must not kill listing
        return {}
    return data if isinstance(data, dict) else {}


def _deploy_after_build(sol: Path, deploy: str) -> Optional[str]:
    deploy = (deploy or "none").strip().lower()
    if deploy in ("", "none"):
        return None
    from jebat_cli_new.agentix import _deploy_local, _deploy_mcp

    if deploy == "local":
        return _deploy_local(sol)
    if deploy == "mcp":
        return _deploy_mcp(sol)
    raise ValueError(f"unknown deploy target {deploy!r} (none|local|mcp)")


@register_tool(
    "agentix_list",
    schema={"type": "object", "properties": {}},
    safety_tier="auto",
    timeout=30,
    description="List JEBAT Agentix specialist templates and locally registered "
                "solutions. Use before agentix_create to discover templates; use "
                "agentix_deploy to register a drafted solution for `jebat agentix run`.",
)
async def agentix_list() -> Dict[str, Any]:
    """List the Agentix specialist catalog and the local solution registry."""

    def _run() -> Dict[str, Any]:
        from jebat_cli_new.agentix import REGISTRY_PATH

        registry = _registry()
        return {
            "specialists": _catalog(),
            "registry": {
                name: {
                    "path": entry.get("path"),
                    "template": entry.get("template"),
                    "runtime": entry.get("runtime", "llm"),
                    "built_at": entry.get("built_at"),
                    "sha": entry.get("manifest_sha256"),
                }
                for name, entry in sorted(registry.items())
                if isinstance(entry, dict)
            },
            "registry_path": str(REGISTRY_PATH),
        }

    return await asyncio.to_thread(_run)


@register_tool(
    "agentix_create",
    schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "kebab-case solution name (3-32 chars, starts with a letter).",
            },
            "objective": {
                "type": "string",
                "description": "What the solution should do — when set, a new reflex/llm solution is drafted by the configured provider (auto mode).",
            },
            "from_specialist": {
                "type": "string",
                "description": "Copy an existing specialist template instead of drafting (see agentix_list). Mutually exclusive with objective.",
            },
            "dir": {
                "type": "string",
                "description": "Target directory for the solution folder (default: current working directory).",
            },
            "deploy": {
                "type": "string",
                "enum": ["none", "local", "mcp"],
                "default": "none",
                "description": "'local' registers the built solution; 'mcp' returns the paste-ready MCP client config that serves it as a tool.",
            },
            "provider": {"type": "string", "description": "Optional provider override for the drafting call."},
            "model": {"type": "string", "description": "Optional model override for the drafting call."},
        },
        "required": ["name"],
    },
    safety_tier="confirm",
    timeout=300,
    description="Create a JEBAT Agentix solution: scaffold from a specialist template "
                "or auto-draft one from an objective (writes files, builds, validates).",
)
async def agentix_create(
    name: str,
    objective: str = "",
    from_specialist: str = "",
    dir: str = ".",
    deploy: str = "none",
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Create + build an Agentix solution (specialist copy or auto-draft)."""

    def _run() -> Dict[str, Any]:
        from jebat_cli_new.agentix import _build, _scaffold_from_specialist

        target = Path(dir or ".").resolve()
        if from_specialist:
            sol = _scaffold_from_specialist(str(from_specialist), str(name), target)
            info = _build(sol)
            return {
                "mode": "specialist",
                "path": str(sol),
                "build": info,
                "deploy": _deploy_after_build(sol, deploy),
            }
        if objective:
            from jebat_cli_new.agentix_auto import auto_create

            outcome = auto_create(
                str(objective),
                name=str(name),
                target_dir=target,
                deploy=deploy,
                provider=provider,
                model=model,
            )
            return {"mode": "auto", **outcome}
        raise ValueError("pass objective (auto-draft) or from_specialist (copy template)")

    try:
        return await asyncio.to_thread(_run)
    except (Exception, SystemExit) as exc:  # agentix signals errors via SystemExit
        return {"error": str(exc)}


@register_tool(
    "agentix_deploy",
    schema={
        "type": "object",
        "properties": {
            "solution": {
                "type": "string",
                "description": "Solution directory path or a locally registered name.",
            },
            "target": {
                "type": "string",
                "enum": ["local", "mcp"],
                "default": "local",
                "description": "'local' registers the solution for `jebat agentix run`; 'mcp' returns the MCP client config serving it as a tool.",
            },
        },
        "required": ["solution"],
    },
    safety_tier="confirm",
    timeout=120,
    description="Deploy a built Agentix solution: 'local' registers it in the local "
                "registry; 'mcp' returns the paste-ready MCP client config that serves "
                "it as an agentix_run tool.",
)
async def agentix_deploy(solution: str, target: str = "local") -> Dict[str, Any]:
    """Deploy (register locally or emit MCP config) a built solution."""

    def _run() -> Dict[str, Any]:
        from jebat_cli_new.agentix import _deploy, _resolve_solution

        sol = _resolve_solution(str(solution))
        return {
            "solution": str(sol),
            "target": str(target),
            "result": _deploy(sol, str(target), "72.62.255.206"),
        }

    try:
        return await asyncio.to_thread(_run)
    except (Exception, SystemExit) as exc:
        return {"error": str(exc)}
