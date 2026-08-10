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

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from jebat.tools import register_tool
from jebat.features.memory import (
    EnhancedMemorySystem,
    MemoryType,
    AutoMimpi,
    SelfLearn,
)

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
        _memory = EnhancedMemorySystem()
        # Load any existing cross-session traces
        _memory._load()
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


def _project_context_filter() -> str:
    """The tag used to isolate this project's context memories."""
    return PROJECT_TAG


# ── mimpi_dream ─────────────────────────────────────────────────────────

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
    """Run a full dream cycle over project memory."""
    engine = _get_automimpi()
    try:
        report = await engine.dream(force=force)
        _get_memory()._save()
    except Exception as e:
        return {"status": "error", "error": f"{type(e).__name__}: {e}"}

    suggestions = []
    for s in report.suggestions:
        suggestions.append({
            "urgency": s.urgency.value,
            "type": s.suggestion_type.value,
            "title": s.title,
            "reason": s.reason,
            "action": s.action,
        })

    profile = report.profile
    return {
        "status": "ok",
        "date": report.date,
        "memories_processed": report.memories_processed,
        "patterns_extracted": report.patterns_extracted,
        "generalizations_created": report.generalizations_created,
        "memories_pruned": report.memories_pruned,
        "laksamana_quote": report.laksamana_quote,
        "profile": {
            "skill_level": profile.skill_level,
            "weak_areas": profile.weak_areas,
            "strong_areas": profile.strong_areas,
            "knowledge_gaps": profile.knowledge_gaps,
            "recommended_focus": profile.recommended_focus,
            "learning_velocity": round(profile.learning_velocity, 3),
            "consolidation_health": round(profile.consolidation_health, 3),
            "pattern_count": profile.pattern_count,
            "strategy_success_rates": profile.strategy_success_rates,
        },
        "suggestions": suggestions,
    }


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
        return {"status": "ok", **engine.get_status()}
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
        analysis = engine.analyze()
    except Exception as e:
        return {"status": "error", "error": f"{type(e).__name__}: {e}"}

    result = {
        "status": "ok",
        "project": _project_name(),
        "analysis": analysis,
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
    memory = _get_memory()
    project = _project_name()
    tags = {PROJECT_TAG, f"project:{project}", f"category:{category}"}
    try:
        trace = await memory.encode(
            content=f"[{project}][{category}] {fact}",
            memory_type=MemoryType.SEMANTIC,
            tags=tags,
            importance=importance,
        )
        memory._save()
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
        "count": len(facts[:limit]),
        "facts": facts[:limit],
    }


def _recall_project_facts(memory: EnhancedMemorySystem) -> List[Dict[str, Any]]:
    """Extract project-tagged traces as plain dicts."""
    import re
    _prefix_re = re.compile(r"^\[([^\]]+)\]\[([^\]]+)\]\s*(.*)$")
    facts = []
    for trace in memory.traces.values():
        if PROJECT_TAG not in trace.tags:
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
    if memory_id in memory.traces:
        del memory.traces[memory_id]
        # Clean up index maps
        for tid_set in memory.traces_by_type.values():
            tid_set.discard(memory_id)
        for tid_set in memory.traces_by_tag.values():
            tid_set.discard(memory_id)
        memory._save()
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
        analysis = engine.analyze()
        recommendations = analysis.get("recommendations", [])
    except Exception:
        recommendations = []

    return {
        "status": "ok",
        "project": project,
        "project_facts_by_category": by_cat,
        "total_project_facts": len(facts),
        "learning_recommendations": recommendations,
        "advice": [
            f"Project context learned: {len(facts)} facts across {len(by_cat)} categories.",
            f"Call mimpi_dream periodically to consolidate session learnings.",
            f"Call project_recall at session start to restore project memory.",
        ],
    }
