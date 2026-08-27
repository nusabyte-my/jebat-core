"""JEBAT Todo Tool — agent-callable session task tracking.

The agent uses this to break complex work into tracked steps, maintain
progress visibility across turns, and demonstrate thoroughness.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jebat.tools import register_tool

# ── Persistent Store ─────────────────────────────────────────────────────

_TODO_DIR = Path.home() / ".jebat" / "todos"
_TODO_DIR.mkdir(parents=True, exist_ok=True)


def _todo_file(session_id: str) -> Path:
    """Get the todo file for a session."""
    safe = session_id.replace("/", "_").replace("\\", "_").replace(":", "_")
    return _TODO_DIR / f"{safe}.json"


def _load(session_id: str) -> list[dict[str, Any]]:
    """Load todos for a session. Returns empty list if none."""
    fp = _todo_file(session_id)
    if fp.exists():
        try:
            return json.loads(fp.read_text())
        except (json.JSONDecodeError, IOError):
            return []
    return []


def _save(session_id: str, todos: list[dict[str, Any]]) -> None:
    """Save todos to disk."""
    fp = _todo_file(session_id)
    fp.write_text(json.dumps(todos, indent=2))


# ── Tool Handlers ────────────────────────────────────────────────────────

@register_tool(
    "todo",
    schema={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["set", "add", "update", "remove", "clear", "list"],
                "description": "What to do with the todo list: 'set' replaces the entire list with items, 'add' appends items, 'update' changes status/content of existing items by id, 'remove' deletes items by id, 'clear' empties the list, 'list' shows current state (no items needed).",
            },
            "items": {
                "type": "array",
                "description": "Todo items array. Required for 'set' and 'add'. Each item: {id: string, content: string, status: 'pending'|'in_progress'|'completed'|'cancelled'}.",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Unique item identifier (kebab-case, e.g. 'fix-auth', 'add-docs')"},
                        "content": {"type": "string", "description": "What needs to be done"},
                        "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "cancelled"], "description": "Current status"},
                    },
                    "required": ["id", "content", "status"],
                },
            },
            "ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Item IDs to remove (for action='remove').",
            },
            "session_id": {
                "type": "string",
                "default": "default",
                "description": "Session identifier to scope the todo list. Use 'default' for the current session.",
            },
        },
        "required": ["action"],
    },
    safety_tier="auto",
    timeout=10,
    description="Manage a session task list. Use for complex multi-step tasks: break work into "
                "bite-sized items, mark them complete as you go, and add new items when the "
                "plan changes. Keeps you organized and visible to the user.",
)
async def todo(
    action: str,
    items: list[dict[str, Any]] | None = None,
    ids: list[str] | None = None,
    session_id: str = "default",
) -> dict[str, Any]:
    """Manage session-level task tracking."""
    todos = _load(session_id)

    if action == "list":
        return {
            "action": "list",
            "session_id": session_id,
            "count": len(todos),
            "todos": todos,
            "summary": _status_summary(todos),
        }

    elif action == "set":
        # Full replacement
        new_todos = items or []
        _validate_items(new_todos)
        _save(session_id, new_todos)
        return {
            "action": "set",
            "session_id": session_id,
            "count": len(new_todos),
            "todos": new_todos,
        }

    elif action == "add":
        # Merge: update existing by id, add new ones
        new_items = items or []
        existing_ids = {t["id"] for t in todos}
        for item in new_items:
            if item["id"] in existing_ids:
                # Update existing — only validate if it's a full item
                if "content" in item or item.get("status", "ok") == "ok":
                    if "content" not in item and "status" not in item:
                        raise ValueError(f"Update item must have at least 'content' or 'status': {item}")
                for i, t in enumerate(todos):
                    if t["id"] == item["id"]:
                        todos[i] = {**t, **item}
                        break
            else:
                _validate_item(item)  # Full validation for new items
                todos.append(item)
        _save(session_id, todos)
        return {
            "action": "add",
            "session_id": session_id,
            "added": len([item for item in new_items if item["id"] not in existing_ids]),
            "updated": len([item for item in new_items if item["id"] in existing_ids]),
            "count": len(todos),
            "todos": todos,
        }

    elif action == "update":
        # Update existing items by id
        updated = 0
        if items:
            item_map = {it["id"]: it for it in items}
            for i, t in enumerate(todos):
                if t["id"] in item_map:
                    todos[i] = {**t, **item_map[t["id"]]}
                    updated += 1
        _save(session_id, todos)
        return {
            "action": "update",
            "session_id": session_id,
            "updated": updated,
            "count": len(todos),
            "todos": todos,
        }

    elif action == "remove":
        # Remove by id
        remove_set = set(ids or [])
        if not remove_set:
            return {"action": "remove", "error": "No ids provided", "count": len(todos)}
        removed = len(remove_set)
        todos = [t for t in todos if t["id"] not in remove_set]
        _save(session_id, todos)
        return {
            "action": "remove",
            "session_id": session_id,
            "removed": removed,
            "count": len(todos),
            "todos": todos,
        }

    elif action == "clear":
        _save(session_id, [])
        return {"action": "clear", "session_id": session_id, "count": 0}

    return {"error": f"Unknown action: {action}"}


def _validate_items(items: list[dict[str, Any]]) -> None:
    """Validate multiple items — each must be a complete item."""
    for item in items:
        _validate_item(item)


def _validate_item(item: dict[str, Any]) -> None:
        if "id" not in item or "content" not in item or "status" not in item:
            raise ValueError(f"Item missing required fields (id, content, status): {item}")
        status = item["status"]
        if status not in ("pending", "in_progress", "completed", "cancelled"):
            raise ValueError(f"Invalid status '{status}'. Use: pending, in_progress, completed, cancelled")


def _status_summary(todos: list[dict[str, Any]]) -> str:
    """Human-readable status summary."""
    by_status: dict[str, int] = {}
    for t in todos:
        s = t.get("status", "pending")
        by_status[s] = by_status.get(s, 0) + 1

    parts = []
    if by_status.get("in_progress"):
        parts.append(f"{by_status['in_progress']} in progress")
    if by_status.get("pending"):
        parts.append(f"{by_status['pending']} pending")
    if by_status.get("completed"):
        parts.append(f"{by_status['completed']} completed")
    if by_status.get("cancelled"):
        parts.append(f"{by_status['cancelled']} cancelled")

    if not parts:
        return "No tasks"
    return ", ".join(parts)