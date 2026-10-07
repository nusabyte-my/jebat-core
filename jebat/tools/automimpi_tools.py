"""JEBAT autoMimpi + SelfLearn MCP Tools.

Exposes the dream cycle engine and adaptive learning engine to IDE MCP clients:

- mimpi_dream          — Run a dream cycle (consolidate + profile + suggestions)
- mimpi_status         — autoMimpi engine status (dream count, memory health)
- selflearn_analyze    — Full self-learning analysis (skills, gaps, retention)
- project_remember     — Remember durable project context (stack, conventions, env)
- project_recall       — Recall project context stored via project_remember
- project_forget       — Remove a specific project memory
- adapt_environment    — Get adaptation recommendations for the current project

The engine persists cross-session to ~/.jebat/memory/ (traces.json) so the IDE
remembers the project between sessions and adapts as the codebase evolves.
"""

from __future__ import annotations

import json
import os
import asyncio
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from jebat.tools import register_tool
from jebat.features.memory import (
    EnhancedMemorySystem,
    MemoryType,
    AutoMimpi,
    SelfLearn,
)
from jebat.features.memory.automimpi import project_traces
from jebat.features.memory.learning_advisor import LearningAdvisor, redact_learning_text

MEMORY_BASE_DIR = Path.home() / ".jebat" / "memory"

# ── Singleton engine ────────────────────────────────────────────────────
# Persisted across tool calls for the lifetime of the MCP server process.
# Storage defaults to ~/.jebat/memory/ (traces.json) — cross-session.
_memory: Optional[EnhancedMemorySystem] = None
_automimpi: Optional[AutoMimpi] = None
_selflearn: Optional[SelfLearn] = None

# Project context is tagged with PROJECT_TAG so project_remember/recall can
# isolate it from general memories.
PROJECT_TAG = "project"

# Which project are we operating on? Derived from cwd each call so the same
# MCP server works across multiple project folders.
PROJECT_FILES = [
    "package.json", "pyproject.toml", "requirements.txt", "go.mod",
    "Cargo.toml", "pom.xml", "build.gradle", "composer.json",
    "mix.exs", "Gemfile", "pubspec.yaml", "AGENTS.md", "README.md",
]


def _project_name() -> str:
    """Best-effort project name from the current working directory."""
    return Path(os.getcwd()).name or "workspace"


def _get_memory() -> EnhancedMemorySystem:
    global _memory
    if _memory is None:
        _memory = EnhancedMemorySystem(storage_path=MEMORY_BASE_DIR)
    return _memory

def _get_automimpi() -> AutoMimpi:
    global _automimpi
    if _automimpi is None:
        _automimpi = AutoMimpi(_get_memory())
    return _automimpi


def _get_selflearn() -> SelfLearn:
    global _selflearn
    if _selflearn is None:
        _selflearn = SelfLearn(_get_memory())
    return _selflearn


def _get_learning_advisor() -> LearningAdvisor:
    from jebat.features.wiki.wiki_rag import _get_store

    return LearningAdvisor(_get_memory(), _get_store(), str(Path.cwd().resolve()))


def _project_context_filter() -> str:
    """The tag used to isolate this project's context memories."""
    return PROJECT_TAG


# ── mimpi_dream ─────────────────────────────────────────────────────────

def _workspace_dream_state_path() -> Path:
    """Workspace mirror of dream state: <cwd>/memory/.dream-state.json.

    The JEBAT skill's dream-gate check reads THIS file, so it keeps its path and
    camelCase schema for compatibility. Its values are a *view* of the canonical
    state in the dream engine — it is not a second ledger.
    """
    return Path(os.getcwd()) / "memory" / ".dream-state.json"


def _mirror_dream_state_to_workspace() -> Optional[str]:
    """Refresh the workspace bootstrap file from the canonical dream state.

    Reads the canonical state from disk rather than the in-memory engine, so the
    mirror cannot report a stale counter. Atomic write (tmp + os.replace) so a
    reader never sees a half file. Returns the mirror path on success, raises on
    failure — callers may treat mirror failure as non-fatal but must surface it.
    """
    from jebat.features.memory.automimpi import load_dream_state

    state = load_dream_state()
    last = state.get("last_dream")
    path = _workspace_dream_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "lastDreamAt": last,
        "lastScanAt": last,
        "sessionsSinceDream": state.get("sessions_since_dream", 0),
        "totalDreams": state.get("dream_count", 0),
    }
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(tmp, path)
    return str(path)


@register_tool(
    "mimpi_dream",
    schema={
        "type": "object",
        "properties": {
            "force": {
                "type": "boolean",
                "default": False,
                "description": "Force a full consolidation cycle even if recently run.",
            },
        },
    },
    safety_tier="auto",
    timeout=60,
    description="Run JEBAT's dream cycle: consolidate memories, extract patterns, "
                "assess learning profile, and produce personalized suggestions. "
                "This is how JEBAT 'remembers the project' — call it to turn "
                "recent session activity into durable knowledge.",
)
async def mimpi_dream(force: bool = False) -> dict[str, Any]:
    """Consolidate the active project's evidence and persist its report in the KB."""
    engine = _get_automimpi()
    root = str(Path.cwd().resolve())
    try:
        advisor = _get_learning_advisor()
        previous = await asyncio.to_thread(advisor.kb.search_learning, root, "", "dream", 1)
        if previous["records"]:
            from datetime import datetime, timezone
            last = datetime.fromtimestamp(previous["records"][0]["created_at"], timezone.utc)
            engine._last_scope_dream[(_project_name(), root)] = last
        report = await engine.dream(force=force, project=_project_name(), project_root=root)
    except Exception as exc:
        return {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
    payload = asdict(report)
    for suggestion in payload["suggestions"]:
        suggestion["type"] = suggestion.pop("suggestion_type").value
        suggestion["urgency"] = suggestion["urgency"].value
    payload.update(status="ok" if report.status == "completed" else "skipped", project=_project_name(), project_root=root)
    if report.status == "completed":
        try:
            payload["kb_record_id"] = await asyncio.to_thread(advisor.record_dream, report, engine.dream_count)
            payload["dream_state_mirror"] = _mirror_dream_state_to_workspace()
        except Exception as exc:
            # Consolidation already committed: do not report it as rolled back.
            payload.update(status="partial", persistence_error=f"{type(exc).__name__}: {exc}")
    return payload


# ── mimpi_status ────────────────────────────────────────────────────────

@register_tool(
    "mimpi_status",
    schema={
        "type": "object",
        "properties": {},
    },
    safety_tier="auto",
    timeout=10,
    description="Get autoMimpi engine status: dream count, memory count, patterns, "
                "generalizations, and last dream timestamp.",
)
async def mimpi_status() -> dict[str, Any]:
    """Get autoMimpi status."""
    engine = _get_automimpi()
    try:
        return {"status": "ok", **engine.get_status(), "counter_scope": "shared memory store", "project_root": str(Path.cwd().resolve()),
                "kb": await learning_kb_status()}
    except Exception as e:
        return {"status": "error", "error": f"{type(e).__name__}: {e}"}


# ── selflearn_analyze ───────────────────────────────────────────────────

@register_tool(
    "selflearn_analyze",
    schema={
        "type": "object",
        "properties": {
            "include_project": {
                "type": "boolean",
                "default": True,
                "description": "Also return project-specific context facts from memory.",
            },
        },
    },
    safety_tier="auto",
    timeout=30,
    description="Analyze JEBAT's self-learning state: skill assessment by domain, "
                "knowledge coverage, learning velocity, retention health, and "
                "recommendations. Use to adapt behavior to the current project.",
)
async def selflearn_analyze(include_project: bool = True) -> dict[str, Any]:
    """Full self-learning analysis."""
    engine = _get_selflearn()
    memory = _get_memory()
    try:
        analysis = engine.analyze(_project_name(), str(Path.cwd().resolve()))
    except Exception as e:
        return {"status": "error", "error": f"{type(e).__name__}: {e}"}

    result: Dict[str, Any] = {
        "status": "ok",
        "project": _project_name(),
        "analysis": analysis,
        "project_root": str(Path.cwd().resolve()),
    }
    if include_project:
        project_facts = _recall_project_facts(memory)
        if project_facts:
            result["project_facts"] = project_facts
    return result


# ── project_remember ────────────────────────────────────────────────────

@register_tool(
    "project_remember",
    schema={
        "type": "object",
        "properties": {
            "fact": {
                "type": "string",
                "description": "A durable project fact to remember, e.g. "
                    "'uses React 19 + Vite, builds with `npm run build`' or "
                    "'prefers env var JEBAT_API_KEY'. One concise fact per call.",
            },
            "category": {
                "type": "string",
                "enum": ["stack", "command", "convention", "environment", "gotcha", "goal", "other"],
                "default": "other",
                "description": "Category tag for this project fact.",
            },
            "importance": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "default": 0.5,
                "description": "Importance 0-1. High-importance facts survive consolidation.",
            },
        },
        "required": ["fact"],
    },
    safety_tier="auto",
    timeout=10,
    description="Remember a durable fact about the current project: stack, build "
                "commands, conventions, environment quirks, gotchas, or goals. "
                "The IDE recalls these via project_recall in future sessions.",
)
async def project_remember(fact: str, category: str = "other", importance: float = 0.5) -> dict[str, Any]:
    """Store a project context fact as a tagged semantic memory."""
    import math
    if not isinstance(fact, str) or not fact.strip() or len(fact) > 16000:
        raise ValueError("fact must contain 1 to 16000 characters")
    if not isinstance(category, str) or not category.strip() or len(category) > 128:
        raise ValueError("category must be a bounded non-empty string")
    if isinstance(importance, bool) or not isinstance(importance, (int, float)) or not math.isfinite(importance) or not 0 <= importance <= 1:
        raise ValueError("importance must be a finite value from 0 to 1")
    fact = redact_learning_text(fact)
    memory = _get_memory()
    project = _project_name()
    tags = {PROJECT_TAG, f"project:{project}", f"category:{category}"}
    try:
        trace = await memory.encode(
            context={"project_root": str(Path.cwd().resolve())},
            content=f"[{project}][{category}] {fact}",
            memory_type=MemoryType.SEMANTIC,
            tags=tags,
            importance=importance,
        )
        return {
            "status": "stored",
            "memory_id": trace.trace_id,
            "project": project,
            "category": category,
            "fact": fact,
        }
    except Exception as e:
        return {"status": "error", "error": f"{type(e).__name__}: {e}"}


# ── project_recall ──────────────────────────────────────────────────────

@register_tool(
    "project_recall",
    schema={
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": ["stack", "command", "convention", "environment", "gotcha", "goal", "other", "all"],
                "default": "all",
                "description": "Filter project facts by category.",
            },
            "query": {
                "type": "string",
                "description": "Optional keyword filter, e.g. 'build' to find build commands.",
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 50,
                "default": 20,
                "description": "Max facts to return.",
            },
        },
    },
    safety_tier="auto",
    timeout=10,
    description="Recall durable facts about the current project that were stored "
                "with project_remember. Call this at the start of a session to "
                "remember the project's stack, commands, conventions, and gotchas.",
)
async def project_recall(category: str = "all", query: str = "", limit: int = 20) -> dict[str, Any]:
    """Recall project context facts from memory."""
    memory = _get_memory()
    facts = _recall_project_facts(memory)

    # Filter by category
    if category != "all":
        facts = [f for f in facts if f["category"] == category]

    # Filter by keyword
    if query:
        q = query.lower()
        facts = [f for f in facts if q in f["content"].lower() or q in f["category"]]

    facts.sort(key=lambda f: f["strength"], reverse=True)
    return {
        "status": "ok",
        "project": _project_name(),
        "project_root": str(Path.cwd().resolve()),
        "count": len(facts[:limit]),
        "facts": facts[:limit],
    }


def _recall_project_facts(memory: EnhancedMemorySystem) -> List[Dict[str, Any]]:
    """Extract only traces explicitly tagged for the active server project."""
    import re
    _prefix_re = re.compile(r"^\[([^\]]+)\]\[([^\]]+)\]\s*(.*)$")
    facts = []
    project_tag = f"project:{_project_name()}"
    for trace in project_traces(memory, _project_name(), str(Path.cwd().resolve())):
        if PROJECT_TAG not in trace.tags or project_tag not in trace.tags:
            continue
        content = trace.content
        category = "other"
        body = content
        m = _prefix_re.match(content)
        if m:
            category = m.group(2)
            body = m.group(3)
        facts.append({
            "memory_id": trace.trace_id,
            "category": category,
            "content": body,
            "importance": trace.importance,
            "strength": round(trace.calculate_current_strength(), 3),
            "last_accessed": trace.last_accessed.isoformat() if trace.last_accessed else None,
        })
    return facts


# ── project_forget ──────────────────────────────────────────────────────

@register_tool(
    "project_forget",
    schema={
        "type": "object",
        "properties": {
            "memory_id": {
                "type": "string",
                "description": "memory_id from project_recall results.",
            },
        },
        "required": ["memory_id"],
    },
    safety_tier="confirm",
    timeout=10,
    description="Forget a single project fact by its memory_id.",
)
async def project_forget(memory_id: str) -> dict[str, Any]:
    """Delete a project memory by ID."""
    memory = _get_memory()
    allowed = {t.trace_id for t in project_traces(memory, _project_name(), str(Path.cwd().resolve())) if PROJECT_TAG in t.tags}
    if memory_id in allowed:
        memory.forget(memory_id)
        return {"status": "deleted", "memory_id": memory_id}
    return {"status": "not_found", "memory_id": memory_id}


# ── adapt_environment ───────────────────────────────────────────────────

@register_tool(
    "adapt_environment",
    schema={
        "type": "object",
        "properties": {},
    },
    safety_tier="auto",
    timeout=30,
    description="Produce environment-adaptation guidance: how JEBAT should operate "
                "in this project based on learned project context and self-learning "
                "analysis. Combines project facts with learning recommendations.",
)
async def adapt_environment() -> dict[str, Any]:
    """Combine project context + self-learning into adaptation guidance."""
    memory = _get_memory()
    project = _project_name()

    facts = _recall_project_facts(memory)
    by_cat: Dict[str, List[str]] = {}
    for f in facts:
        by_cat.setdefault(f["category"], []).append(f["content"])

    # Self-learning recommendations
    engine = _get_selflearn()
    try:
        analysis = engine.analyze(project, str(Path.cwd().resolve()))
        recommendations = analysis.get("recommendations", [])
    except Exception as exc:
        return {"status": "error", "error": f"{type(exc).__name__}: {exc}"}

    return {
        "status": "ok",
        "project": project,
        "project_facts_by_category": by_cat,
        "total_project_facts": len(facts),
        "learning_recommendations": recommendations,
        "advice": [
            f"Project context learned: {len(facts)} facts across {len(by_cat)} categories.",
            "Call mimpi_dream periodically to consolidate session learnings.",
            "Call project_recall at session start to restore project memory.",
        ],
    }


# ── selflearn_tool_guidance ─────────────────────────────────────────────

@register_tool(
    "selflearn_tool_guidance",
    description="Get SelfLearn guidance for a specific tool or domain. Returns confidence level and any learned patterns.",
    safety_tier="auto",
    schema={
        "type": "object",
        "properties": {
            "tool_name": {"type": "string", "description": "Tool or domain to get guidance for"},
        },
        "required": ["tool_name"],
    },
)
async def selflearn_tool_guidance(tool_name: str) -> dict[str, Any]:
    if not isinstance(tool_name, str) or not tool_name.strip():
        raise ValueError("tool_name must be a non-empty string")
    project, root = _project_name(), str(Path.cwd().resolve())
    analysis = _get_selflearn().analyze(project, root)
    needle = tool_name.casefold()
    relevant = {name: info for name, info in analysis["skill_assessment"].items() if needle in name.casefold() or name.casefold() in needle}
    related = [t for t in project_traces(_get_memory(), project, root) if needle in t.content.casefold() or any(needle in tag.casefold() for tag in t.tags)]
    failures = [t for t in related if "failure" in t.tags]
    return {"tool": tool_name, "project_root": root, "skill_match": relevant,
            "confidence": None, "confidence_basis": "No verified task-outcome probability is available",
            "related_memories": len(related), "evidence_ids": [t.trace_id for t in related[:10]],
            "recorded_failures": len(failures),
            "recommendation": "review_prerequisites" if len(failures) >= 3 else "verify_results" if related else "new_territory",
            "velocity": analysis["learning_velocity"]}


# ── mimpi_record_failure ────────────────────────────────────────────────

@register_tool(
    "mimpi_record_failure",
    description="Record a tool failure pattern. After 3+ similar failures, generates a suggestion to avoid the pattern.",
    safety_tier="auto",
    schema={
        "type": "object",
        "properties": {
            "tool_name": {"type": "string"},
            "error": {"type": "string"},
            "context": {"type": "string", "description": "What was being attempted"},
        },
        "required": ["tool_name", "error"],
    },
)
async def mimpi_record_failure(tool_name: str, error: str, context: str = "") -> dict[str, Any]:
    import re
    if not isinstance(tool_name, str) or not re.fullmatch(r"[\w.:-]{1,128}", tool_name):
        raise ValueError("tool_name must be a bounded tool identifier")
    if not isinstance(error, str) or not error.strip() or not isinstance(context, str):
        raise ValueError("error must be non-empty and context must be text")
    project, root = _project_name(), str(Path.cwd().resolve())
    trace, similar = _get_automimpi().record_failure(tool_name, error, context, project, root)
    result = {"recorded": True, "memory_id": trace.trace_id, "similar_failures": len(similar), "project_root": root}
    if len(similar) >= 3:
        result["warning"] = f"Review {tool_name} prerequisites: {len(similar)} recorded failures"
    return result


# ── session_learning_commit ─────────────────────────────────────────────

@register_tool(
    "session_learning_commit",
    description="Commit session learnings to memory. Call at end of a session to extract and store key facts.",
    safety_tier="auto",
    schema={
        "type": "object",
        "properties": {
            "summary": {"type": "string", "description": "Summary of what was learned in this session"},
            "key_facts": {"type": "array", "items": {"type": "string"}, "description": "Key facts to remember"},
            "session_id": {"type": "string", "description": "Session identifier"},
        },
        "required": ["summary"],
    },
)
async def session_learning_commit(summary: str, key_facts: Optional[List[str]] = None, session_id: str = "") -> dict[str, Any]:
    if not isinstance(summary, str) or not summary.strip() or len(summary) > 16000:
        raise ValueError("summary must contain 1 to 16000 characters")
    if not isinstance(session_id, str) or len(session_id) > 256:
        raise ValueError("session_id must be a string of at most 256 characters")
    if key_facts is not None and (not isinstance(key_facts, list) or len(key_facts) > 50 or not all(isinstance(fact, str) and fact.strip() and len(fact) <= 16000 for fact in key_facts)):
        raise ValueError("key_facts must contain at most 50 non-empty strings of at most 16000 characters")
    ids = _get_automimpi().commit_session_learning(
        redact_learning_text(summary), [redact_learning_text(fact) for fact in key_facts or []],
        session_id, _project_name(), str(Path.cwd().resolve()),
    )
    return {"committed": len(ids), "memory_ids": ids, "project": _project_name()}


@register_tool(
    "learning_advisor",
    description="Generate project-scoped, evidence-cited learning recommendations and retain them in the KB; no model call or action execution.",
    schema={"type": "object", "properties": {
        "focus": {"type": "string", "maxLength": 500, "description": "Optional tool or domain filter"},
        "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 5},
    }},
    safety_tier="auto", timeout=30,
)
async def learning_advisor(focus: str = "", limit: int = 5) -> dict[str, Any]:
    advisor = _get_learning_advisor()
    return await asyncio.to_thread(advisor.advise, focus, limit)


@register_tool(
    "learning_feedback",
    description="Record explicit helpful, unhelpful, or dismissed feedback for advice in this project, with supporting evidence; does not modify source facts.",
    schema={"type": "object", "properties": {
        "record_id": {"type": "string"},
        "outcome": {"type": "string", "enum": ["helpful", "unhelpful", "dismissed"]},
        "evidence": {"type": "string", "minLength": 1, "maxLength": 4000},
    }, "required": ["record_id", "outcome", "evidence"]},
    safety_tier="confirm", timeout=10,
)
async def learning_feedback(record_id: str, outcome: str, evidence: str) -> dict[str, Any]:
    return await asyncio.to_thread(_get_learning_advisor().feedback, record_id, outcome, evidence)


@register_tool(
    "learning_kb_search",
    description="Search persisted AutoMimpi reports and learning advice in the active project's KB database using literal full-text terms.",
    schema={"type": "object", "properties": {
        "query": {"type": "string", "maxLength": 2000},
        "kind": {"type": "string", "enum": ["", "dream", "advice"], "default": ""},
        "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
    }}, safety_tier="auto", timeout=15,
)
async def learning_kb_search(query: str = "", kind: str = "", limit: int = 10) -> dict[str, Any]:
    advisor = _get_learning_advisor()
    return await asyncio.to_thread(advisor.kb.search_learning, advisor.project_root, query, kind, limit)


@register_tool(
    "learning_kb_status",
    description="Show persisted project-scoped dream/advice counts and explicit feedback counts from the existing KB database.",
    schema={"type": "object", "properties": {}}, safety_tier="auto", timeout=10,
)
async def learning_kb_status() -> dict[str, Any]:
    advisor = _get_learning_advisor()
    return await asyncio.to_thread(advisor.kb.learning_status, advisor.project_root)
