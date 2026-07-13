"""Tests for the Enhanced Memory system and the Core<->Enhanced bridge."""

import numpy as np
import pytest
from types import SimpleNamespace

from jebat.features.memory import EnhancedMemorySystem, MemoryType

pytestmark = pytest.mark.unit


@pytest.fixture
def mem_sys(tmp_path):
    return EnhancedMemorySystem(storage_path=tmp_path)


@pytest.mark.asyncio
async def test_encode_and_retrieve_ngram(mem_sys):
    await mem_sys.encode(
        "Optimizing a slow database query with indexing",
        memory_type=MemoryType.EPISODIC,
        tags={"db"},
    )
    results = await mem_sys.retrieve("database query optimization", limit=5)
    assert results, "should recall the encoded memory via n-gram similarity"
    assert any(
        "database" in (t.content or "").lower() or "query" in (t.content or "").lower()
        for t in results
    )


@pytest.mark.asyncio
async def test_retrieve_respects_type_filter(mem_sys):
    await mem_sys.encode("A fact about caching", memory_type=MemoryType.SEMANTIC, tags={"cache"})
    assert not await mem_sys.retrieve("caching", memory_types=[MemoryType.EPISODIC], limit=5)
    assert await mem_sys.retrieve("caching", memory_types=[MemoryType.SEMANTIC], limit=5)


@pytest.mark.asyncio
async def test_text_similarity_nonzero_regression(mem_sys):
    # Regression: n-gram fallback must never return 0.0 (old bug when embedding_fn set).
    sim = mem_sys._text_similarity("database optimization", "optimize the database")
    assert sim > 0.0


# ── Injected fake Ghost DB client to exercise the vector-search path ──


class FakeGhostClient:
    def __init__(self):
        self.collections = {}

    def list_collections(self):
        return list(self.collections.values())

    def create_collection(self, c):
        self.collections[c.name] = SimpleNamespace(name=c.name, dimension=c.dimension, docs={})

    def upsert(self, collection, documents):
        col = self.collections[collection]
        for d in documents:
            col.docs[d.id] = np.array(d.embedding, dtype=np.float32)

    def search(self, collection, query_vector, k=10):
        col = self.collections[collection]
        q = np.array(query_vector, dtype=np.float32)
        out = []
        for doc_id, vec in col.docs.items():
            denom = np.linalg.norm(q) * np.linalg.norm(vec)
            sim = float(np.dot(q, vec) / denom) if denom > 0 else 0.0
            out.append(SimpleNamespace(id=doc_id, distance=1.0 - sim))
        out.sort(key=lambda r: r.distance)
        return out[:k]


@pytest.mark.asyncio
async def test_vector_search_ranking(tmp_path):
    async def emb(text):
        chars = text[:3]
        v = [float(ord(c) % 7) / 7.0 for c in chars]
        return (v + [0.0, 0.0, 0.0])[:3]

    sys_v = EnhancedMemorySystem(
        storage_path=tmp_path,
        embedding_fn=emb,
        ghost_client=FakeGhostClient(),
    )
    await sys_v.encode(
        "database indexing strategy", memory_type=MemoryType.EPISODIC, tags={"db"}
    )
    await sys_v.encode(
        "unrelated cat video", memory_type=MemoryType.EPISODIC, tags={"fun"}
    )
    results = await sys_v.retrieve("database index", limit=5)
    assert results
    assert "database" in results[0].content


@pytest.mark.asyncio
async def test_manager_two_way_bridge(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    from jebat.core.memory.layers import MemoryLayer
    from jebat.core.memory.manager import MemoryManager

    mm = MemoryManager()
    await mm.store(
        "Learned to optimize database queries with indexes",
        layer=MemoryLayer.M1_EPISODIC,
        user_id="u1",
    )

    # Legacy substring search
    legacy = mm.search("database", "u1")
    # Enhanced (vector/n-gram) search via asearch — the read side of the bridge
    enhanced = await mm.asearch("database query optimization", "u1", limit=5)

    combined = legacy + enhanced
    assert any("database" in m.content.lower() for m in combined)
