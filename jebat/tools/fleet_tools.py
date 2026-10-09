"""NusaByte fleet tools — route work onto the agentix task bus (nusabyte-hermes).

The fleet control room lives at ``D:/nusabyte-hermes`` (override with
``NUSABYTE_FLEET_ROOT``); it mirrors the VPS bus at ``/srv/agent-bus``. The bus
is a file queue per agent:

    bus/tasks/<queue>/{inbox,working,outbox,archive}/

Tools:
- ``fleet_agents``   -> parse ``bus/registry/agents.yaml`` (codename, role, queue, docs)
- ``fleet_tasks``    -> stage counts / file listings per agent queue
- ``fleet_dispatch`` -> write a task brief into ``<queue>/inbox/`` (bus-global
                        ``TASK-YYYY-MM-DD-NNN`` ids, nb-bus compatible)

Dispatch writes files: confirm tier. Reads stay auto. Conventions mirror
``templates/task-bus/task-template.md`` and ``bin/nb-bus`` (task ids are the
bus-wide max across every stage, so two writers cannot mint the same id).
"""

from __future__ import annotations

import asyncio
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from jebat.tools import register_tool

DEFAULT_FLEET_ROOT = Path("D:/nusabyte-hermes")
STAGES = ("inbox", "working", "outbox", "archive")
TASK_ID_RE = re.compile(r"^TASK-(\d{4}-\d{2}-\d{2})-(\d{3})")
DEFAULT_APPROVALS = (
    "publishing",
    "pushing commits",
    "rotating credentials",
    "destructive operations",
)


def _fleet_root() -> Path:
    raw = os.environ.get("NUSABYTE_FLEET_ROOT", "").strip()
    return Path(raw) if raw else DEFAULT_FLEET_ROOT


def _require_bus() -> Path:
    root = _fleet_root()
    if not (root / "bus" / "tasks").is_dir():
        raise ValueError(
            f"fleet bus not found at {root / 'bus' / 'tasks'} — set "
            "NUSABYTE_FLEET_ROOT to the nusabyte-hermes checkout"
        )
    return root


def _load_registry(root: Path) -> Dict[str, Dict[str, Any]]:
    reg = root / "bus" / "registry" / "agents.yaml"
    if not reg.is_file():
        return {}
    data = yaml.safe_load(reg.read_text(encoding="utf-8"))
    agents = (data or {}).get("agents") or {}
    return {str(slug): (entry or {}) for slug, entry in agents.items()}


def _queue_of(root: Path, entry: Dict[str, Any], slug: str) -> str:
    task_queue = str(entry.get("task_queue") or "")
    return Path(task_queue).name if task_queue else slug.removeprefix("nusabyte-")


def _resolve_queue(root: Path, agent: str) -> tuple[str, str]:
    """Accept a registry slug (nusabyte-finance) or a bare queue name (finance)."""
    agent = str(agent or "").strip()
    if not agent:
        raise ValueError("agent is required (registry slug or queue name)")
    registry = _load_registry(root)
    if agent in registry:
        queue = _queue_of(root, registry[agent], agent)
        if (root / "bus" / "tasks" / queue).is_dir():
            return agent, queue
        raise ValueError(f"registry agent {agent!r} points at missing queue {queue!r}")
    if (root / "bus" / "tasks" / agent).is_dir():
        return agent, agent
    known = ", ".join(sorted(_queue_of(root, e, s) for s, e in registry.items())) or "(none)"
    raise ValueError(f"unknown agent or queue {agent!r} — queues: {known}")


def _next_task_id(root: Path) -> str:
    tasks = root / "bus" / "tasks"
    day = time.strftime("%Y-%m-%d")
    best = 0
    for path in tasks.rglob(f"TASK-{day}-*"):
        match = TASK_ID_RE.match(path.name)
        if match and match.group(1) == day:
            best = max(best, int(match.group(2)))
    return f"TASK-{day}-{best + 1:03d}"


def _slugify(text: str, limit: int = 40) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return slug[:limit].strip("-") or "task"


def _render_task(
    task_id: str,
    agent: str,
    title: str,
    body: str,
    context: str,
    requested_by: str,
    priority: str,
    approvals: List[str],
) -> str:
    lines = [
        "---",
        f"task_id: {task_id}",
        f"created_at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        "created_by: jebat-agentix",
        f"assigned_to: {agent}",
        f"requested_by: {requested_by}",
        f"priority: {priority}",
        "status: ready",
        "requires_approval_before:",
    ]
    lines += [f"  - {item}" for item in approvals]
    lines += [
        "---",
        "",
        "# Task",
        "",
        title.strip() or "(untitled)",
        "",
        "# Context",
        "",
        (context.strip() or "Add relevant context and paths."),
        "",
        "# Constraints",
        "",
        "- Do not expose secrets.",
        "- Do not perform destructive operations without approval.",
        "- Respect the agent's forbidden_work list in bus/registry/agents.yaml.",
        "",
        "# Expected Output",
        "",
        "- Findings",
        "- Files changed or artifacts created",
        "- Risks and assumptions",
        "- Recommended next action",
        "",
    ]
    if body.strip():
        lines += ["# Body", "", body.strip(), ""]
    return "\n".join(lines)


@register_tool(
    "fleet_agents",
    schema={"type": "object", "properties": {}},
    safety_tier="auto",
    timeout=30,
    description="List the NusaByte agentix fleet from bus/registry/agents.yaml "
                "(slug, codename, role, queue, docs, allowed/forbidden work). "
                "Use before fleet_dispatch to pick the right specialist.",
)
async def fleet_agents() -> Dict[str, Any]:
    """List the fleet registry (nusabyte-hermes control room)."""

    def _run() -> Dict[str, Any]:
        root = _require_bus()
        registry = _load_registry(root)
        return {
            "root": str(root),
            "count": len(registry),
            "agents": [
                {
                    "slug": slug,
                    "codename": entry.get("codename"),
                    "role": entry.get("role"),
                    "queue": _queue_of(root, entry, slug),
                    "docs": entry.get("docs"),
                    "gateway_url": entry.get("gateway_url"),
                    "allowed_work": entry.get("allowed_work") or [],
                    "forbidden_work": entry.get("forbidden_work") or [],
                }
                for slug, entry in sorted(registry.items())
            ],
        }

    try:
        return await asyncio.to_thread(_run)
    except Exception as exc:  # noqa: BLE001 — surface as tool error payload
        return {"error": str(exc)}


@register_tool(
    "fleet_tasks",
    schema={
        "type": "object",
        "properties": {
            "agent": {
                "type": "string",
                "description": "Optional registry slug (nusabyte-finance) or queue name (finance). Omit for a bus-wide count.",
            },
            "stage": {
                "type": "string",
                "enum": ["inbox", "working", "outbox", "archive"],
                "description": "Only list files for this stage (default: counts for all stages).",
            },
        },
    },
    safety_tier="auto",
    timeout=60,
    description="Inspect the NusaByte task bus: per-agent stage counts, or the file "
                "list for one agent/stage (inbox backlog, results in outbox).",
)
async def fleet_tasks(agent: str = "", stage: str = "") -> Dict[str, Any]:
    """Count/list task files on the fleet bus."""

    def _run() -> Dict[str, Any]:
        root = _require_bus()
        tasks = root / "bus" / "tasks"
        if agent:
            slug, queue = _resolve_queue(root, agent)
            base = tasks / queue
            if stage:
                if stage not in STAGES:
                    raise ValueError(f"stage must be one of {STAGES}")
                files = sorted(p.name for p in (base / stage).glob("*") if p.is_file())
                return {"agent": slug, "queue": queue, "stage": stage, "files": files}
            return {
                "agent": slug,
                "queue": queue,
                "stages": {
                    s: sorted(p.name for p in (base / s).glob("*") if p.is_file())
                    for s in STAGES
                },
            }
        bus: Dict[str, Dict[str, int]] = {}
        totals = {s: 0 for s in STAGES}
        for queue_dir in sorted(tasks.iterdir()):
            if not queue_dir.is_dir():
                continue
            counts = {
                s: sum(1 for p in (queue_dir / s).glob("*") if p.is_file()) if (queue_dir / s).is_dir() else 0
                for s in STAGES
            }
            if any(counts.values()):
                bus[queue_dir.name] = counts
                for s in STAGES:
                    totals[s] += counts[s]
        return {"root": str(root), "queues_with_tasks": bus, "totals": totals}

    try:
        return await asyncio.to_thread(_run)
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


@register_tool(
    "fleet_dispatch",
    schema={
        "type": "object",
        "properties": {
            "agent": {
                "type": "string",
                "description": "Registry slug (nusabyte-finance) or queue name (finance).",
            },
            "title": {"type": "string", "description": "One-line task title — the brief headline."},
            "context": {"type": "string", "description": "Context, paths, inputs the specialist needs."},
            "body": {"type": "string", "description": "Optional extra task details (appended as a Body section)."},
            "requested_by": {"type": "string", "default": "humm1ngb1rd"},
            "priority": {"type": "string", "enum": ["low", "normal", "high"], "default": "normal"},
            "requires_approval_before": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Extra approval gates appended to the defaults (publishing, pushing commits, rotating credentials, destructive operations).",
            },
        },
        "required": ["agent", "title"],
    },
    safety_tier="confirm",
    timeout=60,
    description="Write a task brief into the NusaByte fleet bus inbox "
                "(bus/tasks/<queue>/inbox/TASK-YYYY-MM-DD-NNN-title.md, nb-bus "
                "compatible; ids are bus-global). Writing does NOT execute the task — "
                "specialists claim it from the bus.",
)
async def fleet_dispatch(
    agent: str,
    title: str,
    context: str = "",
    body: str = "",
    requested_by: str = "humm1ngb1rd",
    priority: str = "normal",
    requires_approval_before: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a task file on the fleet bus inbox."""

    def _run() -> Dict[str, Any]:
        root = _require_bus()
        slug, queue = _resolve_queue(root, agent)
        priority_value = (priority or "normal").strip().lower()
        if priority_value not in ("low", "normal", "high"):
            raise ValueError("priority must be low, normal, or high")
        approvals = list(DEFAULT_APPROVALS)
        for item in requires_approval_before or []:
            item = str(item).strip()
            if item and item not in approvals:
                approvals.append(item)
        task_id = _next_task_id(root)
        filename = f"{task_id}-{_slugify(title)}.md"
        inbox = root / "bus" / "tasks" / queue / "inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        path = inbox / filename
        path.write_text(
            _render_task(task_id, slug, title, body, context, requested_by, priority_value, approvals),
            encoding="utf-8",
            newline="\n",
        )
        return {
            "task_id": task_id,
            "agent": slug,
            "queue": queue,
            "path": str(path),
            "approvals": approvals,
            "next": f"specialist claims it: nb-bus claim {task_id} (result via nb-bus report {task_id} <file>)",
        }

    try:
        return await asyncio.to_thread(_run)
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}
