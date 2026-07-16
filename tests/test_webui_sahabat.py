"""Focused tests for Sahabat WebUI companion route adapters."""

from types import SimpleNamespace

import pytest

from jebat.features.companion.briefing import DailyBriefing
from jebat.features.companion.meeting import MeetingSummarizer
from jebat.features.companion.tasks import TaskManager
from jebat.services.webui import webui_server as webui


@pytest.mark.asyncio
async def test_sahabat_briefing_uses_daily_briefing(monkeypatch):
    async def generate(self, timezone_str, extra_context):
        assert timezone_str == "UTC"
        assert extra_context == "Release day"
        return SimpleNamespace(
            content="Today's focus",
            date="2026-07-16",
            task_count=2,
            recent_topics=["release"],
            generated_at="2026-07-16T00:00:00+00:00",
            provider="local",
        )

    monkeypatch.setattr(DailyBriefing, "generate", generate)

    result = await webui.sahabat_briefing(
        webui.SahabatBriefingRequest(timezone="UTC", extra_context="Release day")
    )

    assert result["briefing"] == "Today's focus"
    assert result["task_count"] == 2


@pytest.mark.asyncio
async def test_sahabat_tasks_create_list_and_complete(monkeypatch):
    task = SimpleNamespace(
        task_id="task-123",
        title="Ship Sahabat",
        description="",
        status="pending",
        priority="high",
        category="general",
        due_date=None,
        created_at="2026-07-16T00:00:00+00:00",
        completed_at=None,
        tags=[],
    )
    monkeypatch.setattr(TaskManager, "add_task", lambda self, **kwargs: task)
    monkeypatch.setattr(TaskManager, "list_tasks", lambda self, **kwargs: [task])

    created = await webui.create_sahabat_task(
        webui.SahabatTaskCreateRequest(title="Ship Sahabat", priority="high")
    )
    listed = await webui.sahabat_tasks(status="pending")

    assert created["task"]["task_id"] == "task-123"
    assert listed["tasks"][0]["title"] == "Ship Sahabat"

    task.status = "completed"
    task.completed_at = "2026-07-16T01:00:00+00:00"
    monkeypatch.setattr(TaskManager, "update_task", lambda self, task_id, **kwargs: task)
    completed = await webui.update_sahabat_task(
        "task-123", webui.SahabatTaskUpdateRequest(status="completed")
    )
    assert completed["task"]["status"] == "completed"


@pytest.mark.asyncio
async def test_sahabat_meeting_uses_meeting_summarizer(monkeypatch):
    async def summarize(self, transcript, title, generate_followup):
        assert transcript == "Ava: Ship it."
        assert title == "Release"
        assert generate_followup is True
        return SimpleNamespace(
            meeting_id="meeting-123",
            title="Release",
            summary="Ship this week.",
            action_items=[{"task": "Ship", "assignee": "Ava"}],
            decisions=["Ship this week"],
            participants=["Ava"],
            created_at="2026-07-16T00:00:00+00:00",
            provider="local",
            metadata={"followup_email": "Thanks everyone."},
        )

    monkeypatch.setattr(MeetingSummarizer, "summarize", summarize)

    result = await webui.sahabat_meeting(
        webui.SahabatMeetingRequest(
            transcript="Ava: Ship it.", title="Release", generate_followup=True
        )
    )

    assert result["action_items"] == [{"task": "Ship", "assignee": "Ava"}]
    assert result["followup_email"] == "Thanks everyone."
