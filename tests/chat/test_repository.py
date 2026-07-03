"""Tests for Chat Module — repository, engine, context management."""

import json
import os
import tempfile
import pytest
from pathlib import Path

from jebat.features.chat.repository import ChatRepository, Conversation, Message


@pytest.fixture
def db_path():
    """Temp SQLite DB for test isolation."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def repo(db_path):
    r = ChatRepository(db_path)
    r.initialize()
    return r


class TestConversationRepository:
    """Conversation CRUD."""

    def test_create(self, repo):
        conv = repo.create_conversation(title="Test Chat", model_preference="gemma3:12b")
        assert conv.id > 0
        assert conv.title == "Test Chat"
        assert conv.model_preference == "gemma3:12b"

    def test_get_exists(self, repo):
        conv = repo.create_conversation(title="Hello")
        fetched = repo.get_conversation(conv.id)
        assert fetched is not None
        assert fetched.id == conv.id
        assert fetched.title == "Hello"

    def test_get_missing(self, repo):
        assert repo.get_conversation(99999) is None

    def test_list_empty(self, repo):
        assert repo.list_conversations() == []

    def test_list_ordering(self, repo):
        c1 = repo.create_conversation(title="A")
        c2 = repo.create_conversation(title="B")
        # B should be first (latest updated_at)
        lst = repo.list_conversations()
        assert lst[0].id == c2.id
        assert lst[1].id == c1.id

    def test_list_limit(self, repo):
        for i in range(5):
            repo.create_conversation(title=f"Chat {i}")
        assert len(repo.list_conversations(limit=3)) == 3

    def test_update(self, repo):
        conv = repo.create_conversation(title="Old")
        conv.title = "New"
        conv.model_preference = "qwen2.5:7b"
        ok = repo.update_conversation(conv)
        assert ok
        fetched = repo.get_conversation(conv.id)
        assert fetched is not None
        assert fetched.title == "New"
        assert fetched.model_preference == "qwen2.5:7b"

    def test_delete(self, repo):
        conv = repo.create_conversation(title="Temp")
        assert repo.get_conversation(conv.id) is not None
        ok = repo.delete_conversation(conv.id)
        assert ok
        assert repo.get_conversation(conv.id) is None

    def test_search(self, repo):
        c1 = repo.create_conversation(title="Python async patterns")
        c2 = repo.create_conversation(title="Rust ownership")
        results = repo.search_conversations("python")
        ids = [r.id for r in results]
        assert c1.id in ids
        assert c2.id not in ids

    def test_count(self, repo):
        assert repo.conversation_count() == 0
        repo.create_conversation(title="A")
        repo.create_conversation(title="B")
        assert repo.conversation_count() == 2


class TestMessageRepository:
    """Message CRUD and context window."""

    def test_add_and_get(self, repo):
        conv = repo.create_conversation()
        msg = Message(conversation_id=conv.id, role="user", content="Hello, world!")
        saved = repo.add_message(msg)
        assert saved.id > 0
        msgs = repo.get_messages(conv.id)
        assert len(msgs) == 1
        assert msgs[0].role == "user"
        assert msgs[0].content == "Hello, world!"

    def test_message_ordering(self, repo):
        conv = repo.create_conversation()
        msg1 = repo.add_message(Message(conversation_id=conv.id, role="user", content="First"))
        msg2 = repo.add_message(Message(conversation_id=conv.id, role="assistant", content="Second"))
        msg3 = repo.add_message(Message(conversation_id=conv.id, role="user", content="Third"))
        msgs = repo.get_messages(conv.id)
        assert [m.content for m in msgs] == ["First", "Second", "Third"]

    def test_context_window_budget(self, repo):
        """Context window should respect token budget."""
        conv = repo.create_conversation()
        for i in range(10):
            repo.add_message(Message(
                conversation_id=conv.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message number {i} with enough text to take up tokens "
                        f"so the context window will truncate at some point.",
                tokens_used=20,
            ))
        # Budget of 60 tokens = ~3 messages
        window = repo.get_context_window(conv.id, token_budget=60, min_messages=2)
        assert len(window) >= 2
        assert len(window) <= 4  # 60/20 = 3, with min_messages=2

    def test_context_window_min_messages(self, repo):
        """Should always include at least min_messages even if budget is tight."""
        conv = repo.create_conversation()
        repo.add_message(Message(conversation_id=conv.id, role="user", content="A", tokens_used=5000))
        repo.add_message(Message(conversation_id=conv.id, role="assistant", content="B", tokens_used=5000))
        window = repo.get_context_window(conv.id, token_budget=100, min_messages=2)
        assert len(window) == 2  # both included despite exceeding budget

    def test_delete_messages(self, repo):
        conv = repo.create_conversation()
        repo.add_message(Message(conversation_id=conv.id, role="user", content="M1"))
        repo.add_message(Message(conversation_id=conv.id, role="user", content="M2"))
        deleted = repo.delete_messages(conv.id)
        assert deleted == 2
        assert repo.get_messages(conv.id) == []

    def test_message_count(self, repo):
        conv = repo.create_conversation()
        assert repo.message_count(conv.id) == 0
        repo.add_message(Message(conversation_id=conv.id, role="user", content="Hi"))
        assert repo.message_count(conv.id) == 1


class TestChatEngine:
    """Integration-level chat engine tests."""

    @pytest.mark.asyncio
    async def test_send_message(self, repo, monkeypatch):
        from jebat.features.chat.engine import ChatEngine

        async def fake_llm(**kwargs):
            return ("Hello! I'm an AI assistant.", {})

        monkeypatch.setattr("jebat.features.chat.engine.generate_chat_reply", fake_llm)

        engine = ChatEngine(repo=repo)
        conv = engine.create_conversation(title="Test")

        # Send a message (non-streaming)
        msg = await engine.send(conv.id, "Say hello")
        # Verify assistant message was stored
        msgs = repo.get_messages(conv.id)
        assert len(msgs) == 2
        assert msgs[0].role == "user"
        assert msgs[0].content == "Say hello"
        assert msgs[1].role == "assistant"
        assert "Hello" in msgs[1].content

    @pytest.mark.asyncio
    async def test_create_conversation(self, repo):
        from jebat.features.chat.engine import ChatEngine
        engine = ChatEngine(repo=repo)
        conv = engine.create_conversation(title="New Chat", model_preference="gemma3:12b")
        assert conv.id > 0
        assert conv.title == "New Chat"

    @pytest.mark.asyncio
    async def test_list_conversations(self, repo):
        from jebat.features.chat.engine import ChatEngine
        engine = ChatEngine(repo=repo)
        engine.create_conversation(title="A")
        engine.create_conversation(title="B")
        lst = engine.list_conversations()
        assert len(lst) == 2
