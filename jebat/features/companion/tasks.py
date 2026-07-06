"""
Sahabat Task Manager — Integrated Task Management

Persistent task storage with priorities, due dates, categories,
and natural language task creation via chat.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass
class Task:
    """A single task."""
    task_id: str
    title: str
    description: str = ""
    status: str = "pending"  # pending, in_progress, completed, cancelled
    priority: str = "medium"  # low, medium, high, urgent
    category: str = "general"
    due_date: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    completed_at: str | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class TaskManager:
    """
    Persistent task manager with JSONL storage.
    Integrates with Sahabat Companion for natural language task operations.
    """

    def __init__(self, data_dir: str | Path | None = None) -> None:
        self.data_dir = Path(data_dir or "~/.jebat/companion").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_file = self.data_dir / "tasks.jsonl"

    def _load_all_tasks(self) -> list[Task]:
        """Load all tasks from storage."""
        if not self.tasks_file.exists():
            return []
        tasks = []
        for line in self.tasks_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            tasks.append(Task(
                task_id=data["task_id"],
                title=data["title"],
                description=data.get("description", ""),
                status=data.get("status", "pending"),
                priority=data.get("priority", "medium"),
                category=data.get("category", "general"),
                due_date=data.get("due_date"),
                created_at=data.get("created_at", ""),
                completed_at=data.get("completed_at"),
                tags=data.get("tags", []),
                metadata=data.get("metadata", {}),
            ))
        return tasks

    def _save_all_tasks(self, tasks: list[Task]) -> None:
        """Save all tasks to storage."""
        with self.tasks_file.open("w", encoding="utf-8") as f:
            for task in tasks:
                record = {
                    "task_id": task.task_id,
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "priority": task.priority,
                    "category": task.category,
                    "due_date": task.due_date,
                    "created_at": task.created_at,
                    "completed_at": task.completed_at,
                    "tags": task.tags,
                    "metadata": task.metadata,
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def add_task(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        category: str = "general",
        due_date: str | None = None,
        tags: list[str] | None = None,
    ) -> Task:
        """Add a new task."""
        tasks = self._load_all_tasks()
        task = Task(
            task_id=f"task-{uuid.uuid4().hex[:8]}",
            title=title,
            description=description,
            priority=priority,
            category=category,
            due_date=due_date,
            tags=tags or [],
        )
        tasks.append(task)
        self._save_all_tasks(tasks)
        return task

    def list_tasks(
        self,
        status: str | None = None,
        priority: str | None = None,
        category: str | None = None,
        limit: int = 50,
    ) -> list[Task]:
        """List tasks with optional filters."""
        tasks = self._load_all_tasks()

        if status:
            tasks = [t for t in tasks if t.status == status]
        if priority:
            tasks = [t for t in tasks if t.priority == priority]
        if category:
            tasks = [t for t in tasks if t.category == category]

        # Sort: urgent first, then by created_at
        priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        tasks.sort(key=lambda t: (priority_order.get(t.priority, 9), t.created_at))

        return tasks[-limit:]

    def complete_task(self, task_id: str) -> Task | None:
        """Mark a task as completed."""
        tasks = self._load_all_tasks()
        for task in tasks:
            if task.task_id == task_id:
                task.status = "completed"
                task.completed_at = datetime.now(timezone.utc).isoformat()
                self._save_all_tasks(tasks)
                return task
        return None

    def update_task(
        self,
        task_id: str,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        category: str | None = None,
        due_date: str | None = None,
    ) -> Task | None:
        """Update a task's fields."""
        tasks = self._load_all_tasks()
        for task in tasks:
            if task.task_id == task_id:
                if title is not None:
                    task.title = title
                if description is not None:
                    task.description = description
                if status is not None:
                    task.status = status
                    if status == "completed":
                        task.completed_at = datetime.now(timezone.utc).isoformat()
                if priority is not None:
                    task.priority = priority
                if category is not None:
                    task.category = category
                if due_date is not None:
                    task.due_date = due_date
                self._save_all_tasks(tasks)
                return task
        return None

    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        tasks = self._load_all_tasks()
        original_count = len(tasks)
        tasks = [t for t in tasks if t.task_id != task_id]
        if len(tasks) < original_count:
            self._save_all_tasks(tasks)
            return True
        return False

    def get_task(self, task_id: str) -> Task | None:
        """Get a specific task by ID."""
        tasks = self._load_all_tasks()
        for task in tasks:
            if task.task_id == task_id:
                return task
        return None

    def search_tasks(self, query: str) -> list[Task]:
        """Search tasks by title or description."""
        tasks = self._load_all_tasks()
        query_lower = query.lower()
        return [
            t for t in tasks
            if query_lower in t.title.lower()
            or query_lower in t.description.lower()
            or query_lower in " ".join(t.tags).lower()
        ]

    def get_stats(self) -> dict[str, Any]:
        """Get task statistics."""
        tasks = self._load_all_tasks()
        pending = [t for t in tasks if t.status == "pending"]
        completed = [t for t in tasks if t.status == "completed"]
        in_progress = [t for t in tasks if t.status == "in_progress"]
        urgent = [t for t in tasks if t.priority == "urgent" and t.status != "completed"]

        return {
            "total": len(tasks),
            "pending": len(pending),
            "completed": len(completed),
            "in_progress": len(in_progress),
            "urgent": len(urgent),
            "completion_rate": (
                f"{len(completed) / len(tasks) * 100:.0f}%" if tasks else "0%"
            ),
        }

    def format_tasks(self, tasks: list[Task]) -> str:
        """Format tasks for display."""
        if not tasks:
            return "  No tasks found."

        priority_icons = {
            "urgent": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
        }

        status_icons = {
            "pending": "○",
            "in_progress": "◐",
            "completed": "●",
            "cancelled": "✕",
        }

        lines = []
        for task in tasks:
            p_icon = priority_icons.get(task.priority, "⚪")
            s_icon = status_icons.get(task.status, "?")
            due = f" (due: {task.due_date})" if task.due_date else ""
            tags = f" [{', '.join(task.tags)}]" if task.tags else ""
            lines.append(
                f"  {s_icon} {p_icon} {task.title}{due}{tags}\n"
                f"     {task.task_id} | {task.category} | {task.status}"
            )

        return "\n".join(lines)
