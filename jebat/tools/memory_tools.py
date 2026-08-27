"""JEBAT Memory Tools — agent-callable memory operations.

Exposes MemoryManager.store/search/delete/forget as registered tools so
the agent can persist facts across sessions without user intervention.
"""

from __future__ import annotations

from typing import Any

from jebat.core.memory import MemoryLayer, MemoryManager
from jebat.tools import register_tool

# ── Singleton MemoryManager instance ─────────────────────────────────────
# Created lazily and shared across all tool calls. The in-memory store
# persists for the lifetime of the agent process.
_memory_manager: MemoryManager | None = None


def _get_manager() -> MemoryManager:
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager


# ── Memory Store ─────────────────────────────────────────────────────────

@register_tool(
    "memory_store",
    schema={
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The fact, preference, or information to remember. Be concise — one sentence is ideal.",
            },
            "category": {
                "type": "string",
                "enum": ["user", "memory"],
                "default": "memory",
                "description": "'user' for personal details about the user, 'memory' for environment facts and lessons learned.",
            },
            "importance": {
                "type": "string",
                "enum": ["critical", "high", "medium", "low"],
                "default": "medium",
                "description": "How important this memory is. Critical/high memories survive longer.",
            },
        },
        "required": ["content"],
    },
    safety_tier="auto",
    timeout=10,
    description="Save a durable fact to memory. The agent uses this to remember user preferences, "
                "environment details, project conventions, and lessons learned across sessions.",
)
async def memory_store(
    content: str,
    category: str = "memory",
    importance: str = "medium",
) -> dict[str, Any]:
    """Store a memory."""
    mgr = _get_manager()

    # Map category to memory layer
    layer_map = {
        "user": MemoryLayer.M3_CONCEPTUAL,   # User facts are permanent
        "memory": MemoryLayer.M2_SEMANTIC,   # Environment facts are long-lived
    }
    layer = layer_map.get(category, MemoryLayer.M2_SEMANTIC)

    try:
        memory_id = await mgr.store(
            content=content,
            layer=layer,
        )
        return {
            "status": "stored",
            "memory_id": memory_id,
            "category": category,
            "layer": layer.value,
            "content_preview": content[:100],
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ── Memory Search ─────────────────────────────────────────────────────────

@register_tool(
    "memory_search",
    schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query to find relevant memories. Use keywords, not full sentences.",
            },
            "category": {
                "type": "string",
                "enum": ["user", "memory", "all"],
                "default": "all",
                "description": "Filter by category: 'user' for personal details, 'memory' for environment facts, 'all' for everything.",
            },
            "limit": {
                "type": "integer",
                "default": 5,
                "minimum": 1,
                "maximum": 20,
                "description": "Maximum number of results to return.",
            },
        },
        "required": ["query"],
    },
    safety_tier="auto",
    timeout=10,
    description="Search saved memories. Use this to recall user preferences, environment setup, "
                "project conventions, or past lessons before answering or taking action.",
)
async def memory_search(
    query: str,
    category: str = "all",
    limit: int = 5,
) -> dict[str, Any]:
    """Search for memories."""
    mgr = _get_manager()

    try:
        results = mgr.search(query=query, user_id="default", limit=limit)
    except Exception as e:
        return {"status": "error", "error": str(e), "results": []}

    # Filter by category if requested
    if category != "all":
        target_layer = MemoryLayer.M3_CONCEPTUAL if category == "user" else MemoryLayer.M2_SEMANTIC
        results = [r for r in results if r.layer == target_layer]

    formatted = []
    for mem in results[:limit]:
        formatted.append({
            "memory_id": mem.memory_id,
            "content": mem.content,
            "layer": mem.layer.value,
            "heat": round(mem.heat.calculate(), 3),
            "created": mem.created_at.isoformat(),
        })

    return {
        "status": "ok",
        "query": query,
        "count": len(formatted),
        "results": formatted,
    }


# ── Memory Forget ─────────────────────────────────────────────────────────

@register_tool(
    "memory_forget",
    schema={
        "type": "object",
        "properties": {
            "memory_id": {
                "type": "string",
                "description": "The memory_id to forget. Get this from memory_search results.",
            },
        },
        "required": ["memory_id"],
    },
    safety_tier="confirm",  # Deletion requires user confirmation
    timeout=10,
    description="Delete a memory by its ID. Use when information is outdated, wrong, "
                "or the user asks to forget something.",
)
async def memory_forget(memory_id: str) -> dict[str, Any]:
    """Delete a memory by ID."""
    mgr = _get_manager()

    # Find and remove the memory from all layers
    removed = False
    for layer in MemoryLayer:
        mems = mgr.memories[layer]
        for i, mem in enumerate(mems):
            if mem.memory_id == memory_id:
                mgr.memories[layer].pop(i)
                removed = True
                break
        if removed:
            break

    if removed:
        return {"status": "deleted", "memory_id": memory_id}
    return {"status": "not_found", "memory_id": memory_id}


# ── Memory Stats ──────────────────────────────────────────────────────────

@register_tool(
    "memory_stats",
    schema={
        "type": "object",
        "properties": {},
    },
    safety_tier="auto",
    timeout=5,
    description="Get memory system statistics: total memories, breakdown by layer, consolidation status.",
)
async def memory_stats() -> dict[str, Any]:
    """Get memory statistics."""
    mgr = _get_manager()
    return mgr.get_stats()