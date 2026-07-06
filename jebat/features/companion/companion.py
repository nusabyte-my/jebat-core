"""
Sahabat Companion — Core Conversational Engine

Persistent chat with memory integration, context awareness,
and multi-session conversation management.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from jebat.llm.chat_runtime import generate_chat_reply, normalize_chat_preset, build_chat_system_prompt
from jebat.llm.history import ChatHistoryStore, ChatTurn
from jebat.llm.providers import generate_with_failover


# ─── Sahabat System Prompt ──────────────────────────────────────

SAHABAT_IDENTITY = (
    "You are Sahabat — the JEBAT Companion. "
    "You are a friendly, reliable AI assistant for daily operations. "
    "You help with conversations, task management, meeting summaries, "
    "daily briefings, and schedule awareness. "
    "Be warm but efficient. Remember context from prior conversations. "
    "When the user mentions tasks, meetings, or schedules, handle them proactively. "
    "You can access the user's task list, recent conversation history, "
    "and daily briefing data to provide contextual assistance."
)

SAHABAT_PERSONA = (
    "You speak like a knowledgeable friend who happens to be an AI. "
    "Be concise by default, expand when asked. "
    "Use emoji sparingly — only when it adds clarity or warmth. "
    "Never be overly formal or robotic. "
    "When you don't know something, say so directly and offer to help find it."
)


# ─── Conversation Session ───────────────────────────────────────

@dataclass
class ConversationSession:
    """A single conversation session with metadata."""
    session_id: str
    created_at: str
    title: str = "New Conversation"
    messages: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })


# ─── Companion Store ────────────────────────────────────────────

class CompanionStore:
    """Persistent storage for Sahabat companion sessions."""

    def __init__(self, data_dir: str | Path | None = None) -> None:
        self.data_dir = Path(data_dir or "~/.jebat/companion").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_file = self.data_dir / "sessions.jsonl"
        self.context_file = self.data_dir / "context.json"

    def save_session(self, session: ConversationSession) -> None:
        """Append session to storage."""
        record = {
            "session_id": session.session_id,
            "created_at": session.created_at,
            "title": session.title,
            "messages": session.messages,
            "metadata": session.metadata,
        }
        with self.sessions_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def load_sessions(self, limit: int = 50) -> list[ConversationSession]:
        """Load recent sessions."""
        if not self.sessions_file.exists():
            return []
        sessions = []
        for line in self.sessions_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            sessions.append(ConversationSession(
                session_id=data["session_id"],
                created_at=data["created_at"],
                title=data.get("title", "Untitled"),
                messages=data.get("messages", []),
                metadata=data.get("metadata", {}),
            ))
        return sessions[-limit:]

    def get_session(self, session_id: str) -> ConversationSession | None:
        """Get a specific session by ID."""
        for session in self.load_sessions():
            if session.session_id == session_id:
                return session
        return None

    def load_context(self) -> dict[str, Any]:
        """Load persistent context (user preferences, recent topics, etc.)."""
        if not self.context_file.exists():
            return {}
        return json.loads(self.context_file.read_text(encoding="utf-8"))

    def save_context(self, context: dict[str, Any]) -> None:
        """Save persistent context."""
        self.context_file.write_text(
            json.dumps(context, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_recent_topics(self, limit: int = 10) -> list[str]:
        """Extract recent conversation topics from history."""
        sessions = self.load_sessions(limit=5)
        topics = []
        for session in reversed(sessions):
            for msg in session.messages[-3:]:
                if msg.get("role") == "user":
                    content = msg.get("content", "")[:80]
                    if content and content not in topics:
                        topics.append(content)
                        if len(topics) >= limit:
                            return topics
        return topics


# ─── Sahabat Companion ──────────────────────────────────────────

class SahabatCompanion:
    """
    Sahabat — The JEBAT Companion.

    A conversational AI for daily operations, meeting summaries,
    task management, and persistent memory across sessions.
    """

    def __init__(
        self,
        data_dir: str | Path | None = None,
        provider: str | None = None,
        model: str | None = None,
        preset: str | None = None,
    ) -> None:
        self.store = CompanionStore(data_dir=data_dir)
        self.provider = provider
        self.model = model
        self.preset = preset or "default"
        self.current_session: ConversationSession | None = None

    def start_session(self, title: str | None = None) -> ConversationSession:
        """Start a new conversation session."""
        session_id = f"sahabat-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        self.current_session = ConversationSession(
            session_id=session_id,
            created_at=now,
            title=title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        )
        return self.current_session

    def _build_system_prompt(self, context: dict[str, Any] | None = None) -> str:
        """Build the Sahabat system prompt with context."""
        parts = [SAHABAT_IDENTITY, SAHABAT_PERSONA]

        if context:
            if context.get("user_name"):
                parts.append(f"The user's name is {context['user_name']}.")
            if context.get("timezone"):
                parts.append(f"The user is in timezone {context['timezone']}.")
            if context.get("recent_topics"):
                topics_str = ", ".join(context["recent_topics"][:5])
                parts.append(f"Recent conversation topics: {topics_str}.")
            if context.get("active_tasks"):
                task_count = len(context["active_tasks"])
                parts.append(f"The user has {task_count} active tasks in their task list.")

        return " ".join(parts)

    async def chat(
        self,
        message: str,
        session: ConversationSession | None = None,
        provider_override: str | None = None,
        model_override: str | None = None,
    ) -> tuple[str, str]:
        """
        Send a message and get a response.

        Returns:
            Tuple of (response_text, used_provider)
        """
        if session is None:
            if self.current_session is None:
                self.start_session()
            session = self.current_session

        # Add user message
        session.add_message("user", message)

        # Build context
        context = self.store.load_context()
        context["recent_topics"] = self.store.get_recent_topics()

        # Build system prompt
        system_prompt = self._build_system_prompt(context)

        # Prepare conversation history for LLM
        conversation_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in session.messages[-20:]  # Keep last 20 messages for context
        ]

        # Generate response
        response_text, used_provider, _ = await generate_chat_reply(
            prompt=message,
            preset=self.preset,
            provider_override=provider_override or self.provider,
            model_override=model_override or self.model,
            conversation_messages=conversation_messages,
            system_prompt_override=system_prompt,
        )

        # Add assistant response
        session.add_message("assistant", response_text)

        # Auto-save session
        self.store.save_session(session)

        return response_text, used_provider

    async def chat_one_shot(
        self,
        message: str,
        provider_override: str | None = None,
        model_override: str | None = None,
    ) -> tuple[str, str]:
        """
        One-shot chat without session persistence.
        Good for quick questions.
        """
        context = self.store.load_context()
        context["recent_topics"] = self.store.get_recent_topics()

        system_prompt = self._build_system_prompt(context)

        response_text, used_provider, _ = await generate_chat_reply(
            prompt=message,
            preset=self.preset,
            provider_override=provider_override or self.provider,
            model_override=model_override or self.model,
            system_prompt_override=system_prompt,
        )

        return response_text, used_provider

    def list_sessions(self, limit: int = 20) -> list[ConversationSession]:
        """List recent conversation sessions."""
        return self.store.load_sessions(limit=limit)

    def get_session_history(self, session_id: str) -> list[dict[str, str]]:
        """Get message history for a session."""
        session = self.store.get_session(session_id)
        if session is None:
            return []
        return session.messages

    def get_stats(self) -> dict[str, Any]:
        """Get companion statistics."""
        sessions = self.store.load_sessions()
        total_messages = sum(len(s.messages) for s in sessions)
        context = self.store.load_context()

        return {
            "total_sessions": len(sessions),
            "total_messages": total_messages,
            "context_keys": list(context.keys()),
            "recent_topics": self.store.get_recent_topics(5),
        }


# ─── CLI Entry Point ────────────────────────────────────────────

def main():
    """CLI entry point for Sahabat Companion."""
    import asyncio
    import sys

    print("\n🤖 Sahabat — JEBAT Companion")
    print("   Conversational AI for daily operations")
    print("   Type 'quit' to exit, 'stats' for info\n")

    companion = SahabatCompanion()

    async def run():
        session = companion.start_session()

        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n👋 Goodbye!")
                break

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                print("\n👋 Goodbye!")
                break

            if user_input.lower() == "stats":
                stats = companion.get_stats()
                print(f"\n📊 Session Stats:")
                print(f"   Sessions: {stats['total_sessions']}")
                print(f"   Messages: {stats['total_messages']}")
                print(f"   Recent topics: {', '.join(stats['recent_topics'][:3])}\n")
                continue

            if user_input.lower() == "history":
                sessions = companion.list_sessions(5)
                print(f"\n📜 Recent Sessions:")
                for s in sessions:
                    print(f"   [{s.session_id[:16]}] {s.title} ({len(s.messages)} msgs)")
                print()
                continue

            response, provider = await companion.chat(user_input, session=session)
            print(f"\nSahabat [{provider}]: {response}\n")

    asyncio.run(run())


if __name__ == "__main__":
    main()
