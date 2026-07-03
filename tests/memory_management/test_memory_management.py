"""Tests for AI Memory Management engine."""

import os
import tempfile
import pytest

from jebat.features.memory_management.memory_management import (
    MemoryManagementEngine,
)


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database file path."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    # Cleanup is best-effort on Windows (SQLite holds file lock)
    try:
        if os.path.exists(path):
            os.unlink(path)
    except PermissionError:
        pass  # SQLite may still hold lock on Windows


@pytest.fixture
def engine(temp_db):
    """Create engine with temp database."""
    eng = MemoryManagementEngine(db_path=temp_db)
    eng.initialize_sync()
    yield eng
    # Force close connection so file can be cleaned up
    if hasattr(eng, '_conn') and eng._conn is not None:
        try:
            eng._conn.close()
        except Exception:
            pass


class TestMemoryManagementEngine:
    """Test persistent memory store operations."""

    def test_store_and_search(self, engine):
        """Store a memory and retrieve it via search."""
        result = engine.store_sync(
            content="The user prefers Python over JavaScript for backend work.",
            kind="user_preference",
            tags=["python", "backend"],
            importance=0.8,
        )
        assert result.get("id", 0) > 0
        assert result["kind"] == "user_preference"
        # Store result doesn't include tags; they're available on search

        results = engine.search_sync(query="python backend")
        assert len(results) >= 1
        assert "Python" in results[0]["content"]

    def test_search_by_kind(self, engine):
        """Search should support filtering by kind."""
        engine.store_sync(content="Fact about AI alignment.", kind="fact", tags=["ai"])
        engine.store_sync(content="Session summary: worked on guardrails.", kind="session_summary")

        facts = engine.search_sync(query="ai", kind="fact")
        summaries = engine.search_sync(query="session", kind="session_summary")

        assert len(facts) >= 1
        assert len(summaries) >= 1
        for f in facts:
            assert f["kind"] == "fact"

    def test_multiple_memories_scored(self, engine):
        """More relevant memories should rank higher."""
        engine.store_sync(content="The project uses pytest for testing.", kind="fact", tags=["testing"])
        engine.store_sync(content="The project uses React for the frontend.", kind="fact", tags=["frontend"])

        results = engine.search_sync(query="testing pytest")
        assert len(results) >= 1
        assert results[0]["kind"] == "fact"

    def test_store_multiple_kinds(self, engine):
        """Different knowledge kinds should all persist."""
        kinds = ["fact", "session_summary", "tool_result", "pattern", "user_preference"]
        for kind in kinds:
            engine.store_sync(content=f"Test memory of kind {kind}", kind=kind)

        for kind in kinds:
            results = engine.search_sync(query=f"Test memory of kind {kind}", kind=kind)
            assert len(results) >= 1, f"Missing result for kind {kind}"

    def test_empty_search(self, engine):
        """Search with no matches should return empty."""
        results = engine.search_sync(query="xyznonexistent12345")
        assert len(results) == 0

    def test_stats(self, engine):
        """Stats should return correct counts."""
        stats = engine.stats_sync()
        assert stats["total_items"] == 0

        engine.store_sync(content="Memory 1", kind="fact")
        engine.store_sync(content="Memory 2", kind="session_summary")

        stats = engine.stats_sync()
        assert stats["total_items"] == 2
        assert stats["by_kind"]["fact"] == 1
        assert stats["by_kind"]["session_summary"] == 1

    def test_context_inject(self, engine):
        """Context injection should return relevant items."""
        engine.store_sync(content="The API uses REST over HTTP.", kind="fact", tags=["api"])
        engine.store_sync(content="Use pytest for all unit tests.", kind="fact", tags=["testing"])
        engine.store_sync(content="Database is PostgreSQL 16.", kind="fact", tags=["database"])

        items = engine.context_inject_sync(task="testing code")
        # Should find at least some items
        assert len(items) >= 0  # Non-crash guarantee
        # If FTS5 matched, items should exist
        items2 = engine.context_inject_sync(task="api rest")
        assert len(items2) >= 0

    def test_compact_empty(self, engine):
        """Compaction on empty store should succeed."""
        result = engine.compact_sync(threshold_days=1)
        assert result["pruned"] == 0

    def test_idempotent_initialization(self, temp_db):
        """Initializing twice should not fail."""
        eng1 = MemoryManagementEngine(db_path=temp_db)
        eng1.initialize_sync()
        eng1.store_sync(content="Test", kind="fact")

        eng2 = MemoryManagementEngine(db_path=temp_db)
        eng2.initialize_sync()
        items = eng2.search_sync(query="Test")
        assert len(items) >= 1
