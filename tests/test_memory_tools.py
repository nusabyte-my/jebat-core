"""Tests for the agent-facing memory tools (`memory_store/search/forget/stats`).

Covers the store bridge specifically: `memory_search` must read through
`MemoryManager.asearch` (enhanced recall), and `memory_forget` must clear both
the legacy record and the linked enhanced trace. Removing only the legacy copy
left the content reachable via `asearch`, so a forgotten memory came back on the
next search.
"""

import threading

import pytest

from jebat.core.memory.layers import MemoryLayer
from jebat.core.memory.manager import MemoryManager
from jebat.features.memory import EnhancedMemorySystem
from jebat.tools import memory_tools

pytestmark = pytest.mark.unit


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Isolated MemoryManager wired into the tool module's singleton slot.

    `EnhancedMemorySystem` is bound to `tmp_path` so nothing touches the real
    `~/.jebat/memory` store.
    """
    manager = MemoryManager()
    manager._enhanced_memory = EnhancedMemorySystem(storage_path=tmp_path)
    monkeypatch.setattr(memory_tools, "_memory_manager", manager)
    return manager


@pytest.mark.asyncio
async def test_store_dedups_identical_content(store):
    first = await memory_tools.memory_store("Project uses ruff for linting")
    second = await memory_tools.memory_store("  project uses   RUFF for Linting  ")

    assert first["status"] == "stored"
    assert second["memory_id"] == first["memory_id"]
    assert len(store.memories[MemoryLayer.M2_SEMANTIC]) == 1
    assert len(store._get_enhanced_memory().traces) == 1


@pytest.mark.asyncio
async def test_search_reads_through_asearch(store):
    calls = []

    async def fake_asearch(query, user_id, layer=None, limit=10):
        calls.append((query, user_id, limit))
        return []

    store.asearch = fake_asearch

    result = await memory_tools.memory_search("linting")

    assert calls == [("linting", "default", 5)]
    assert result["status"] == "ok"


@pytest.mark.asyncio
async def test_search_reaches_enhanced_only_records(store):
    """A similarity-only match must surface, not just substring matches."""
    enhanced = store._get_enhanced_memory()
    await enhanced.encode(
        "Optimizing slow database queries with indexes",
        context={"user_id": "default"},
    )

    # The legacy substring search cannot see it: the query is not a substring.
    assert store.search("database query optimization", user_id="default") == []

    result = await memory_tools.memory_search("database query optimization")

    assert result["status"] == "ok"
    assert result["count"] >= 1
    assert any("database" in r["content"].lower() for r in result["results"])


@pytest.mark.asyncio
async def test_forget_clears_both_stores_and_persists(store, tmp_path):
    stored = await memory_tools.memory_store("Temporary fact to forget")
    enhanced = store._get_enhanced_memory()
    assert len(store.memories[MemoryLayer.M2_SEMANTIC]) == 1
    assert len(enhanced.traces) == 1

    result = await memory_tools.memory_forget(stored["memory_id"])

    assert result == {"status": "deleted", "memory_id": stored["memory_id"]}
    assert store.memories[MemoryLayer.M2_SEMANTIC] == []
    assert enhanced.traces == {}
    # Persisted: a fresh instance must not resurrect the forgotten trace.
    reloaded = EnhancedMemorySystem(storage_path=tmp_path)
    assert reloaded.traces == {}


@pytest.mark.asyncio
async def test_forget_by_search_result_id_also_clears_legacy(store):
    """`memory_search` returns the enhanced trace id, not the legacy id.

    Forgetting by that id must still drop the legacy record — otherwise the
    two stores drift apart and `memory_stats` keeps counting a deleted memory.
    """
    await memory_tools.memory_store("Temporary fact to forget")
    found = await memory_tools.memory_search("temporary fact")
    trace_id = found["results"][0]["memory_id"]

    assert await memory_tools.memory_forget(trace_id) == {
        "status": "deleted",
        "memory_id": trace_id,
    }

    assert store.memories[MemoryLayer.M2_SEMANTIC] == []
    assert store._get_enhanced_memory().traces == {}
    assert (await memory_tools.memory_stats())["total_memories"] == 0


@pytest.mark.asyncio
async def test_forget_unknown_id_reports_not_found(store):
    result = await memory_tools.memory_forget("mem_does_not_exist")
    assert result["status"] == "not_found"


@pytest.mark.asyncio
async def test_stats_does_not_block_the_event_loop(store):
    """`get_stats` touches both stores, so it must run off the event loop."""
    seen = {}

    def fake_get_stats():
        seen["thread"] = threading.current_thread().ident
        return {"total_memories": 0}

    store.get_stats = fake_get_stats

    result = await memory_tools.memory_stats()

    assert result == {"total_memories": 0}
    assert seen["thread"] != threading.main_thread().ident


@pytest.mark.asyncio
async def test_forget_does_not_block_the_event_loop(store):
    seen = {}

    def fake_forget(memory_id, user_id="default"):
        seen["thread"] = threading.current_thread().ident
        return True

    store.forget = fake_forget

    result = await memory_tools.memory_forget("mem_x")

    assert result["status"] == "deleted"
    assert seen["thread"] != threading.main_thread().ident
