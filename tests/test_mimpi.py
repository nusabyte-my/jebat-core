"""Tests for the Mimpi (Dream/Imagination) system."""

import pytest

from jebat.features.mimpi import DreamEngine, DreamType, Dream, DreamPhase

pytestmark = pytest.mark.unit


class FakeMemory:
    """Records encode() calls so we can verify dreams are persisted."""

    def __init__(self):
        self.encoded = []

    async def encode(self, content, memory_type=None, tags=None, importance=0.5, context=None):
        self.encoded.append({"content": content, "tags": tags, "importance": importance})

    async def retrieve(self, query, limit=5):
        return []


@pytest.mark.asyncio
async def test_dream_engine_creates():
    engine = DreamEngine()
    assert engine is not None
    assert engine.concept_graph


@pytest.mark.asyncio
async def test_induce_dream_runs_full_pipeline():
    engine = DreamEngine()
    dream = await engine.induce_dream(
        dream_type=DreamType.CREATIVE, seed_concepts=["database", "caching"]
    )
    assert isinstance(dream, Dream)
    assert DreamPhase.INDUCTION in dream.phases_completed
    assert DreamPhase.AWAKENING in dream.phases_completed
    assert dream.duration_seconds >= 0
    assert isinstance(dream.insights_generated, list)
    assert isinstance(dream.actionable_ideas, list)


@pytest.mark.asyncio
async def test_dream_about_problem():
    dream = await DreamEngine().dream_about_problem("How to optimize a slow database query?")
    assert dream.problem_context
    assert DreamPhase.AWAKENING in dream.phases_completed


@pytest.mark.asyncio
async def test_mimpi_persists_insights_to_memory_manager():
    mem = FakeMemory()
    engine = DreamEngine(memory_manager=mem)
    await engine.dream_about_problem("Design a caching layer for an API")
    # Consolidation phase should have written insights / ideas / dream summaries.
    assert len(mem.encoded) > 0
    assert any("mimpi" in (t.get("tags") or set()) for t in mem.encoded)


@pytest.mark.asyncio
async def test_dream_history():
    engine = DreamEngine()
    await engine.dream_about_problem("Plan a migration strategy")
    summaries = engine.get_dream_history(limit=5)
    assert len(summaries) == 1
    assert "type" in summaries[0]


def test_module_defines_logger():
    import jebat.features.mimpi as m

    assert hasattr(m, "logger")
