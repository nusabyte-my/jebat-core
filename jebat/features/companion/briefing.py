"""
Sahabat Daily Briefing — Morning Briefing Generator

Generates daily briefings with task summaries, schedule awareness,
weather context, and recent conversation highlights.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from jebat.llm.chat_runtime import generate_chat_reply


# ─── Briefing Template ──────────────────────────────────────────

BRIEFING_SYSTEM_PROMPT = (
    "You are Sahabat, the JEBAT Companion generating a daily briefing. "
    "Be concise, warm, and actionable. Format the briefing in clear sections. "
    "Use emoji sparingly for section headers. "
    "Prioritize what the user needs to know and do today."
)

BRIEFING_TEMPLATE = """Generate a daily briefing for today ({date}).

Context:
- Timezone: {timezone}
- Active tasks: {task_count} items
- Recent conversations: {recent_topics}
- Day of week: {day_of_week}

Task Summary:
{tasks_section}

Recent Highlights:
{highlights_section}

Generate a concise, actionable daily briefing with these sections:
1. 🌅 Good Morning greeting (personalized, brief)
2. 📋 Today's Focus (top 3-5 tasks to tackle)
3. 📝 Recent Context (what was discussed recently)
4. 💡 Suggested Actions (proactive suggestions based on context)
5. 🎯 Daily Goal (one key outcome to aim for)

Keep it under 400 words. Be specific, not generic."""


@dataclass
class BriefingResult:
    """A generated daily briefing."""
    date: str
    content: str
    task_count: int
    recent_topics: list[str]
    generated_at: str
    provider: str


class DailyBriefing:
    """
    Generates daily briefings by combining task data,
    conversation history, and LLM generation.
    """

    def __init__(
        self,
        data_dir: str | Path | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> None:
        self.data_dir = Path(data_dir or "~/.jebat/companion").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.briefings_file = self.data_dir / "briefings.jsonl"
        self.provider = provider
        self.model = model

    def _load_recent_tasks(self) -> list[dict[str, Any]]:
        """Load recent tasks from the task manager."""
        from .tasks import TaskManager
        tm = TaskManager(data_dir=self.data_dir)
        tasks = tm.list_tasks(status="pending")
        return [{"title": t.title, "priority": t.priority, "due": t.due_date} for t in tasks[:10]]

    def _load_recent_topics(self, limit: int = 5) -> list[str]:
        """Load recent conversation topics from companion store."""
        from .companion import CompanionStore
        store = CompanionStore(data_dir=self.data_dir)
        return store.get_recent_topics(limit)

    def _format_tasks_section(self, tasks: list[dict]) -> str:
        """Format tasks for the briefing prompt."""
        if not tasks:
            return "No pending tasks."
        lines = []
        for i, task in enumerate(tasks, 1):
            priority = task.get("priority", "medium")
            due = task.get("due", "no due date")
            lines.append(f"  {i}. [{priority.upper()}] {task['title']} (due: {due})")
        return "\n".join(lines)

    def _format_highlights_section(self, topics: list[str]) -> str:
        """Format recent topics for the briefing prompt."""
        if not topics:
            return "No recent conversations."
        return "\n".join(f"  - {topic}" for topic in topics)

    async def generate(
        self,
        timezone_str: str = "Asia/Kuala_Lumpur",
        extra_context: str | None = None,
    ) -> BriefingResult:
        """
        Generate today's daily briefing.

        Returns:
            BriefingResult with the generated briefing content.
        """
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        day_of_week = now.strftime("%A")

        tasks = self._load_recent_tasks()
        topics = self._load_recent_topics()

        prompt = BRIEFING_TEMPLATE.format(
            date=date_str,
            timezone=timezone_str,
            task_count=len(tasks),
            recent_topics=", ".join(topics[:3]) if topics else "none",
            day_of_week=day_of_week,
            tasks_section=self._format_tasks_section(tasks),
            highlights_section=self._format_highlights_section(topics),
        )

        if extra_context:
            prompt += f"\n\nAdditional context: {extra_context}"

        response_text, used_provider, _ = await generate_chat_reply(
            prompt=prompt,
            preset="default",
            provider_override=self.provider,
            model_override=self.model,
            system_prompt_override=BRIEFING_SYSTEM_PROMPT,
        )

        result = BriefingResult(
            date=date_str,
            content=response_text,
            task_count=len(tasks),
            recent_topics=topics,
            generated_at=now.isoformat(),
            provider=used_provider,
        )

        # Save briefing
        self._save_briefing(result)

        return result

    def _save_briefing(self, briefing: BriefingResult) -> None:
        """Save briefing to history."""
        record = {
            "date": briefing.date,
            "content": briefing.content,
            "task_count": briefing.task_count,
            "recent_topics": briefing.recent_topics,
            "generated_at": briefing.generated_at,
            "provider": briefing.provider,
        }
        with self.briefings_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def get_briefing_history(self, limit: int = 7) -> list[BriefingResult]:
        """Load recent briefing history."""
        if not self.briefings_file.exists():
            return []
        briefings = []
        for line in self.briefings_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            briefings.append(BriefingResult(
                date=data["date"],
                content=data["content"],
                task_count=data.get("task_count", 0),
                recent_topics=data.get("recent_topics", []),
                generated_at=data.get("generated_at", ""),
                provider=data.get("provider", ""),
            ))
        return briefings[-limit:]
