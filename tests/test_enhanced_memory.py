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
async def test_manager_two_way_bridge(tmp_path):
    # Explicit storage_path, not a patched HOME: on Windows `Path.home()` reads
    # USERPROFILE, so the old form ran against the real ~/.jebat store.
    from jebat.core.memory.layers import MemoryLayer
    from jebat.core.memory.manager import MemoryManager

    mm = MemoryManager(config={"storage_path": str(tmp_path)})
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


@pytest.mark.asyncio
async def test_asearch_surfaces_enhanced_only_traces(tmp_path):
    """Regression: `asearch`'s enhanced branch raised TypeError.

    It built `HeatScore(visit_count=...)`, a field that does not exist, and a
    bare `except Exception: pass` swallowed it — so similarity/vector recall
    returned nothing and `asearch` was silently legacy-substring-only.
    """
    from jebat.core.memory.manager import MemoryManager

    mm = MemoryManager(config={"storage_path": str(tmp_path)})
    await mm.store("Optimizing slow database queries with indexes", user_id="u1")

    # The legacy substring search cannot see it, because the query is not a
    # substring of the content...
    assert mm.search("database query optimization", "u1") == []

    # ...but the enhanced similarity branch must.
    hits = await mm.asearch("database query optimization", "u1", limit=5)
    assert any("database" in m.content.lower() for m in hits)
    assert hits[0].heat.calculate() > 0


@pytest.mark.asyncio
async def test_encode_is_durable_and_deduplicated(tmp_path):
    system = EnhancedMemorySystem(storage_path=tmp_path)
    first = await system.encode(
        "Remember the durable database migration plan",
        context={"user_id": "u1"},
    )
    duplicate = await system.encode(
        "  remember the durable database migration plan  ",
        context={"user_id": "u1"},
    )
    await system.encode(
        "Remember the durable database migration plan",
        context={"user_id": "u2"},
    )

    assert duplicate.trace_id == first.trace_id
    assert len(system.traces) == 2

    reloaded = EnhancedMemorySystem(storage_path=tmp_path)
    assert len(reloaded.traces) == 2
    assert first.trace_id in reloaded.traces
