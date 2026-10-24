"""Regression tests for `project_recall` query matching.

The tool advertises keyword recall, but it compared the whole query as one
substring and sorted only by strength. A two-word query ("canonical receipt")
missed a fact containing both words, and same-strength facts written in the
current session were pushed past the limit by older rows.
"""

import os
from pathlib import Path

import pytest

from jebat.features.memory import EnhancedMemorySystem, MemoryType
from jebat.tools import automimpi_tools

pytestmark = pytest.mark.unit


@pytest.fixture
def project_store(tmp_path, monkeypatch):
    enhanced = EnhancedMemorySystem(storage_path=tmp_path)
    monkeypatch.setattr(automimpi_tools, "_memory", enhanced)
    monkeypatch.chdir(tmp_path)
    return enhanced


async def _seed_fact(enhanced: EnhancedMemorySystem, fact: str, category: str = "convention"):
    project = Path(os.getcwd()).name
    await enhanced.encode(
        content=f"[{project}][{category}] {fact}",
        memory_type=MemoryType.SEMANTIC,
        context={"project_root": str(Path.cwd().resolve())},
        tags={"project", f"project:{project}", f"category:{category}"},
        importance=0.9,
    )


@pytest.mark.asyncio
async def test_recall_matches_all_query_tokens(project_store):
    await _seed_fact(project_store, "Receipts render from one canonical document and one receipt model")

    result = await automimpi_tools.project_recall(query="canonical receipt")

    assert result["status"] == "ok"
    assert result["count"] == 1
    assert "canonical document" in result["facts"][0]["content"]


@pytest.mark.asyncio
async def test_recall_rejects_when_a_token_is_missing(project_store):
    await _seed_fact(project_store, "Receipts render from one canonical document")

    result = await automimpi_tools.project_recall(query="canonical invoice")

    assert result["count"] == 0


@pytest.mark.asyncio
async def test_recall_returns_newest_fact_first(project_store):
    await _seed_fact(project_store, "Older receipt convention")
    await _seed_fact(project_store, "Newer receipt convention")

    result = await automimpi_tools.project_recall(query="receipt", limit=1)

    assert result["count"] == 1
    assert result["facts"][0]["content"] == "Newer receipt convention"
