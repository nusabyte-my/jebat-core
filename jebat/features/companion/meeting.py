"""
Sahabat Meeting Summarizer — Meeting Transcript Processing

Summarizes meeting transcripts, extracts action items,
generates follow-up emails, and maintains meeting notes.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from jebat.llm.chat_runtime import generate_chat_reply


# ─── Prompts ────────────────────────────────────────────────────

MEETING_SUMMARY_PROMPT = """Summarize this meeting transcript into a structured meeting note.

Meeting Transcript:
---
{transcript}
---

Generate a meeting summary with these sections:

1. **Meeting Overview** — Date, attendees (if mentioned), purpose
2. **Key Discussion Points** — Main topics covered (bullet points)
3. **Decisions Made** — Concrete decisions reached
4. **Action Items** — Tasks assigned with owners and deadlines
5. **Follow-up Items** — Items needing further discussion or research
6. **Key Quotes** — Notable statements (if any)

Be concise but thorough. Extract all action items with their assignees.
If action items are found, format them as:
  - [ ] @owner: task description (due: date)

Keep the summary under 500 words."""

ACTION_ITEMS_PROMPT = """Extract ONLY the action items from this meeting transcript.
Return them as a JSON array with objects containing:
- "task": the action item description
- "assignee": who is responsible (or "unassigned")
- "deadline": any mentioned deadline (or null)
- "priority": "high", "medium", or "low"

Meeting Transcript:
---
{transcript}
---

Return ONLY valid JSON, no other text."""

FOLLOWUP_EMAIL_PROMPT = """Write a follow-up email based on this meeting summary.

Meeting Summary:
---
{summary}
---

Key Action Items:
{action_items}

Write a professional, concise follow-up email that:
1. Thanks attendees
2. Summarizes key decisions
3. Lists action items with owners
4. Sets expectations for next steps

Keep it under 300 words. Use a warm but professional tone."""


@dataclass
class MeetingNote:
    """A processed meeting note."""
    meeting_id: str
    title: str
    transcript: str
    summary: str
    action_items: list[dict[str, str]]
    decisions: list[str]
    participants: list[str]
    created_at: str
    provider: str
    metadata: dict[str, Any] = field(default_factory=dict)


class MeetingSummarizer:
    """
    Processes meeting transcripts into structured summaries
    with action items and follow-up emails.
    """

    def __init__(
        self,
        data_dir: str | Path | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> None:
        self.data_dir = Path(data_dir or "~/.jebat/companion").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.meetings_file = self.data_dir / "meetings.jsonl"
        self.provider = provider
        self.model = model

    async def summarize(
        self,
        transcript: str,
        title: str | None = None,
        generate_followup: bool = False,
    ) -> MeetingNote:
        """
        Process a meeting transcript into a structured summary.

        Args:
            transcript: The meeting transcript text
            title: Optional meeting title
            generate_followup: Whether to generate a follow-up email

        Returns:
            MeetingNote with summary, action items, and decisions
        """
        # Generate summary
        summary_prompt = MEETING_SUMMARY_PROMPT.format(transcript=transcript)
        summary_text, provider = await generate_chat_reply(
            prompt=summary_prompt,
            preset="default",
            provider_override=self.provider,
            model_override=self.model,
            system_prompt_override="You are a meeting summarization expert. Be precise and structured.",
        )

        # Extract action items
        action_prompt = ACTION_ITEMS_PROMPT.format(transcript=transcript)
        action_text, _ = await generate_chat_reply(
            prompt=action_prompt,
            preset="default",
            provider_override=self.provider,
            model_override=self.model,
            system_prompt_override="You extract action items from meeting transcripts. Return only valid JSON.",
        )

        # Parse action items
        action_items = self._parse_action_items(action_text)

        # Extract decisions (from summary)
        decisions = self._extract_decisions(summary_text)

        # Extract participants
        participants = self._extract_participants(transcript)

        meeting_id = f"meeting-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()

        meeting = MeetingNote(
            meeting_id=meeting_id,
            title=title or f"Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            transcript=transcript,
            summary=summary_text,
            action_items=action_items,
            decisions=decisions,
            participants=participants,
            created_at=now,
            provider=provider,
        )

        # Generate follow-up email if requested
        if generate_followup and action_items:
            followup_prompt = FOLLOWUP_EMAIL_PROMPT.format(
                summary=summary_text,
                action_items=json.dumps(action_items, indent=2),
            )
            followup_text, _ = await generate_chat_reply(
                prompt=followup_prompt,
                preset="default",
                provider_override=self.provider,
                model_override=self.model,
                system_prompt_override="You write professional follow-up emails after meetings.",
            )
            meeting.metadata["followup_email"] = followup_text

        # Save meeting
        self._save_meeting(meeting)

        return meeting

    def _parse_action_items(self, action_text: str) -> list[dict[str, str]]:
        """Parse action items from LLM output."""
        try:
            # Try to extract JSON from the response
            text = action_text.strip()
            # Handle markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            items = json.loads(text)
            if isinstance(items, list):
                return [
                    {
                        "task": str(item.get("task", "")),
                        "assignee": str(item.get("assignee", "unassigned")),
                        "deadline": item.get("deadline"),
                        "priority": str(item.get("priority", "medium")),
                    }
                    for item in items
                    if item.get("task")
                ]
        except (json.JSONDecodeError, IndexError):
            pass

        # Fallback: extract from text
        items = []
        for line in action_text.split("\n"):
            line = line.strip()
            if line.startswith("- [ ]") or line.startswith("- @") or line.startswith("•"):
                task = line.lstrip("- •[]@").strip()
                if task:
                    items.append({
                        "task": task,
                        "assignee": "unassigned",
                        "deadline": None,
                        "priority": "medium",
                    })
        return items

    def _extract_decisions(self, summary: str) -> list[str]:
        """Extract decisions from summary text."""
        decisions = []
        in_decisions = False
        for line in summary.split("\n"):
            line = line.strip()
            if "decision" in line.lower() and ("**" in line or "##" in line):
                in_decisions = True
                continue
            if in_decisions:
                if line.startswith("-") or line.startswith("*") or line.startswith("•"):
                    decision = line.lstrip("- *•").strip()
                    if decision:
                        decisions.append(decision)
                elif line and not line.startswith(" ") and not line.startswith("#"):
                    in_decisions = False
        return decisions

    def _extract_participants(self, transcript: str) -> list[str]:
        """Extract participant names from transcript."""
        participants = set()
        for line in transcript.split("\n"):
            line = line.strip()
            # Common patterns: "Name:" or "[Name]" at start of line
            if ":" in line and len(line.split(":")[0]) < 30:
                name = line.split(":")[0].strip().lstrip("[")
                if name and len(name) > 1 and not name.startswith(("http", "www")):
                    participants.add(name)
        return sorted(participants)

    def _save_meeting(self, meeting: MeetingNote) -> None:
        """Save meeting note to storage."""
        record = {
            "meeting_id": meeting.meeting_id,
            "title": meeting.title,
            "transcript": meeting.transcript[:500],  # Truncate for storage
            "summary": meeting.summary,
            "action_items": meeting.action_items,
            "decisions": meeting.decisions,
            "participants": meeting.participants,
            "created_at": meeting.created_at,
            "provider": meeting.provider,
            "metadata": meeting.metadata,
        }
        with self.meetings_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def list_meetings(self, limit: int = 20) -> list[MeetingNote]:
        """List recent meetings."""
        if not self.meetings_file.exists():
            return []
        meetings = []
        for line in self.meetings_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            meetings.append(MeetingNote(
                meeting_id=data["meeting_id"],
                title=data["title"],
                transcript=data.get("transcript", ""),
                summary=data.get("summary", ""),
                action_items=data.get("action_items", []),
                decisions=data.get("decisions", []),
                participants=data.get("participants", []),
                created_at=data.get("created_at", ""),
                provider=data.get("provider", ""),
                metadata=data.get("metadata", {}),
            ))
        return meetings[-limit:]

    def format_meeting(self, meeting: MeetingNote) -> str:
        """Format a meeting note for display."""
        lines = [
            f"📋 {meeting.title}",
            f"   ID: {meeting.meeting_id}",
            f"   Date: {meeting.created_at[:10]}",
            f"   Participants: {', '.join(meeting.participants) if meeting.participants else 'N/A'}",
            "",
            "Summary:",
            meeting.summary,
            "",
        ]

        if meeting.action_items:
            lines.append("Action Items:")
            for item in meeting.action_items:
                assignee = item.get("assignee", "unassigned")
                deadline = item.get("deadline", "no deadline")
                priority = item.get("priority", "medium")
                lines.append(f"  ☐ @{assignee}: {item['task']} ({deadline}) [{priority}]")
            lines.append("")

        if meeting.decisions:
            lines.append("Decisions:")
            for decision in meeting.decisions:
                lines.append(f"  ✓ {decision}")
            lines.append("")

        if "followup_email" in meeting.metadata:
            lines.append("Follow-up Email:")
            lines.append(meeting.metadata["followup_email"])

        return "\n".join(lines)
