"""JEBAT Todo tool — simple task tracking persisted to JSON.

Provides async functions for managing a personal todo list:
- add_todo(content: str) -> dict
- list_todos() -> list[dict]
- remove_todo(todo_id: str) -> dict
- update_todo_status(todo_id: str, status: str) -> dict
- clear_todos() -> dict

Todos are stored as a JSON array in ~/.jebat/todos.json.
Each todo: {id: str, content: str, status: str}
Status values: pending, in_progress, completed, cancelled.
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List

# Storage path
TODO_FILE = Path.home() / ".jebat" / "todos.json"


def _ensure_todo_dir() -> None:
    """Ensure the ~/.jebat directory exists."""
    TODO_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load_todos() -> List[Dict[str, Any]]:
    """Load todos from JSON file, return empty list if missing or invalid."""
    if not TODO_FILE.exists():
        return []
    try:
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, OSError):
        return []


def _save_todos(todos: List[Dict[str, Any]]) -> None:
    """Save todos to JSON file (atomic write)."""
    _ensure_todo_dir()
    temp = TODO_FILE.with_suffix(".tmp")
    with open(temp, "w", encoding="utf-8") as f:
        json.dump(todos, f, indent=2, ensure_ascii=False)
    temp.replace(TODO_FILE)


async def add_todo(content: str) -> Dict[str, Any]:
    """Add a new todo with pending status."""
    _ensure_todo_dir()
    todos = _load_todos()
    todo = {
        "id": str(uuid.uuid4()),
        "content": content.strip(),
        "status": "pending",
    }
    todos.append(todo)
    _save_todos(todos)
    return todo


async def list_todos() -> List[Dict[str, Any]]:
    """Return all todos."""
    return _load_todos()


async def remove_todo(todo_id: str) -> Dict[str, Any]:
    """Remove a todo by ID. Returns the removed todo or error."""
    todos = _load_todos()
    for i, t in enumerate(todos):
        if t["id"] == todo_id:
            removed = todos.pop(i)
            _save_todos(todos)
            return removed
    return {"error": f"Todo not found: {todo_id}"}


async def update_todo_status(todo_id: str, status: str) -> Dict[str, Any]:
    """Update a todo's status. Valid statuses: pending, in_progress, completed, cancelled."""
    valid = {"pending", "in_progress", "completed", "cancelled"}
    if status not in valid:
        return {"error": f"Invalid status: {status}. Must be one of {sorted(valid)}"}
    todos = _load_todos()
    for t in todos:
        if t["id"] == todo_id:
            t["status"] = status
            _save_todos(todos)
            return t
    return {"error": f"Todo not found: {todo_id}"}


async def clear_todos() -> Dict[str, Any]:
    """Remove all todos. Returns count removed."""
    todos = _load_todos()
    count = len(todos)
    _save_todos([])
    return {"removed": count}