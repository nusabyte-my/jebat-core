"""JEBAT Session Search Tool — cross-session transcript recall.

Wraps the existing SessionManager.search_messages() FTS5 index so
the agent can recall past conversations without user intervention.

This mirrors Hermes' session_search tool: the agent can find what
was worked on in prior sessions, how bugs were fixed, what decisions
were made, etc.
"""

from __future__ import annotations

from typing import Any

from jebat.features.session import SessionManager
from jebat.tools import register_tool

# ── Singleton SessionManager ───────────────────────────────────────────────

_session_manager: SessionManager | None = None


def _get_manager() -> SessionManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


# ── Session Search ─────────────────────────────────────────────────────────

@register_tool(
    "session_search",
    schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query — keywords, phrases, or boolean expressions. "
                               "Use OR between keywords for broad recall, phrases for exact match, "
                               "prefix* for wildcard.",
            },
            "limit": {
                "type": "integer",
                "default": 5,
                "minimum": 1,
                "maximum": 20,
                "description": "Maximum number of matching sessions to return.",
            },
        },
        "required": ["query"],
    },
    safety_tier="auto",
    timeout=10,
    description="Search past conversation transcripts using FTS5 full-text search. "
                "Use this to recall what was worked on in prior sessions — how bugs were fixed, "
                "what decisions were made, what projects were discussed. Faster and cheaper "
                "than asking the user to repeat themselves.",
)
async def session_search(
    query: str,
    limit: int = 5,
) -> dict[str, Any]:
    """Search across all past session transcripts.

    Returns a list of matching sessions with snippets and metadata.
    If no results, the agent should tell the user it found nothing.
    """
    mgr = _get_manager()

    # If no query, list recent sessions instead (browse mode)
    if not query.strip():
        recent = mgr.list_sessions(limit=min(limit, 10))
        return {
            "status": "ok",
            "mode": "recent",
            "count": len(recent),
            "sessions": [
                {
                    "session_id": s.id,
                    "title": s.title or "(untitled)",
                    "created_at": s.created_at,
                    "updated_at": s.updated_at,
                    "messages": mgr.message_count(s.id),
                    "tokens": mgr.total_tokens(s.id),
                }
                for s in recent
            ],
        }

    # Full-text search
    results = mgr.search_messages(query, limit=limit)

    if not results:
        # Fallback: try listing recent sessions so agent can at least browse
        recent = mgr.list_sessions(limit=5)
        return {
            "status": "ok",
            "query": query,
            "mode": "no_results_fallback_recent",
            "count": len(recent),
            "sessions": [
                {
                    "session_id": s.id,
                    "title": s.title or "(untitled)",
                    "updated_at": s.updated_at,
                    "messages": mgr.message_count(s.id),
                }
                for s in recent
            ],
            "hint": "No exact matches found. Try different keywords or browse recent sessions listed above.",
        }

    # Build rich results with context
    formatted = []
    for r in results:
        session_id = r["session_id"]
        formatted.append({
            "session_id": session_id,
            "title": r["title"] or "(untitled)",
            "role": r["role"],
            "snippet": r["snippet"],
            "message_count": mgr.message_count(session_id),
        })

    return {
        "status": "ok",
        "query": query,
        "mode": "search",
        "count": len(formatted),
        "results": formatted,
    }


# ── Session History (for current session inspection) ──────────────────────

@register_tool(
    "session_history",
    schema={
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "Session ID to load history from. Get this from session_search results.",
            },
            "limit": {
                "type": "integer",
                "default": 20,
                "minimum": 1,
                "maximum": 100,
                "description": "Maximum number of messages to load (most recent).",
            },
        },
        "required": ["session_id"],
    },
    safety_tier="auto",
    timeout=10,
    description="Load the conversation history for a specific past session. "
                "Use this after session_search to read the full context of a relevant session.",
)
async def session_history(
    session_id: str,
    limit: int = 20,
) -> dict[str, Any]:
    """Load messages from a past session."""
    mgr = _get_manager()

    sess = mgr.get_session(session_id)
    if sess is None:
        return {"status": "not_found", "session_id": session_id}

    messages = mgr.load_history(session_id, limit=limit)
    return {
        "status": "ok",
        "session_id": session_id,
        "title": sess.title or "(untitled)",
        "created_at": sess.created_at,
        "message_count": len(messages),
        "total_messages_in_session": mgr.message_count(session_id),
        "messages": [
            {
                "role": m.role,
                "content": m.content[:500] if len(m.content) > 500 else m.content,
                "truncated": len(m.content) > 500,
                "tokens": m.tokens,
            }
            for m in messages
        ],
    }