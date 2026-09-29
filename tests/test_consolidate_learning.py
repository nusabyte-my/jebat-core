"""Tests for AGICognitiveEngine.consolidate_learning.

The stored fact used to be content-free — "Goal 'x': Completed via N tool
steps." — so every run persisted a near-identical no-op memory that passed
dedup while saying nothing. The fact must carry the actual lesson material:
the goal, the tools used, and what the run concluded.
"""

from __future__ import annotations

import pytest

from jebat.core.agi_core import AGICognitiveEngine
from jebat.tools import automimpi_tools

pytestmark = pytest.mark.unit


@pytest.fixture
def captured(monkeypatch):
    """Record what consolidate_learning stores, without touching real memory."""
    calls: list[dict] = []

    async def fake_project_remember(fact: str, category: str = "other",
                                    importance: float = 0.5) -> dict:
        calls.append({"fact": fact, "category": category, "importance": importance})
        return {"status": "stored", "memory_id": f"mem_{len(calls)}"}

    monkeypatch.setattr(automimpi_tools, "project_remember", fake_project_remember)
    return calls


@pytest.mark.asyncio
async def test_fact_carries_goal_tools_and_outcome(captured):
    engine = AGICognitiveEngine()
    result = await engine.consolidate_learning(
        "Fix the login redirect loop",
        "The auth guard was missing in middleware.py; added it and verified "
        "the redirect with a regression test.",
        ["read_file(middleware.py)", "edit_file(middleware.py)"],
    )

    assert result["status"] == "consolidated"
    fact = captured[0]["fact"]
    assert "Fix the login redirect loop" in fact
    assert "read_file(middleware.py)" in fact
    assert "auth guard" in fact
    assert result["fact"] == fact


@pytest.mark.asyncio
async def test_fact_is_not_the_content_free_placeholder(captured):
    """The old fact passed dedup while carrying nothing; it must not return."""
    engine = AGICognitiveEngine()
    await engine.consolidate_learning(
        "Deploy the service", "Shipped via docker compose, healthcheck green.",
        ["run_cmd(docker compose up -d)"],
    )

    fact = captured[0]["fact"]
    assert "Completed via" not in fact
    assert "tool steps" not in fact


@pytest.mark.asyncio
async def test_different_runs_produce_different_facts(captured):
    engine = AGICognitiveEngine()
    await engine.consolidate_learning("Fix CORS headers", "Added allowlist in nginx.",
                                      ["edit_file(nginx.conf)"])
    await engine.consolidate_learning("Fix CORS preflight", "Added OPTIONS route.",
                                      ["edit_file(routes.py)"])

    assert captured[0]["fact"] != captured[1]["fact"]


@pytest.mark.asyncio
async def test_long_answer_is_truncated_and_whitespace_collapsed(captured):
    engine = AGICognitiveEngine()
    await engine.consolidate_learning(
        "Summarize the incident",
        "line one\n\nline two\n" + "detail " * 200,
        [],
    )

    fact = captured[0]["fact"]
    assert "\n\n" not in fact
    outcome = fact.split("Outcome: ", 1)[1]
    assert len(outcome) <= 300


@pytest.mark.asyncio
async def test_more_than_eight_actions_are_summarized(captured):
    engine = AGICognitiveEngine()
    actions = [f"tool_{i}()" for i in range(10)]
    await engine.consolidate_learning("Wide task", "Finished after ten calls.", actions)

    fact = captured[0]["fact"]
    assert "tool_0()" in fact and "tool_7()" in fact
    assert "tool_8()" not in fact
    assert "(+2 more)" in fact


@pytest.mark.asyncio
async def test_no_actions_says_none(captured):
    engine = AGICognitiveEngine()
    await engine.consolidate_learning("Pure reasoning task", "Answered from context.", [])

    assert "Tools: none" in captured[0]["fact"]


@pytest.mark.asyncio
async def test_short_answer_is_skipped(captured):
    engine = AGICognitiveEngine()
    result = await engine.consolidate_learning("Tiny", "ok", [])

    assert result == {"status": "skipped"}
    assert captured == []


@pytest.mark.asyncio
async def test_category_follows_domain_classification(captured):
    engine = AGICognitiveEngine()
    await engine.consolidate_learning(
        "Audit security headers and run CVE port scan",
        "Two missing headers found and documented.",
        ["run_cmd(nmap)"],
    )

    assert captured[0]["category"] == "security"


@pytest.mark.asyncio
async def test_storage_errors_are_surfaced(monkeypatch):
    async def boom(fact, category="other", importance=0.5):
        raise RuntimeError("memory offline")

    monkeypatch.setattr(automimpi_tools, "project_remember", boom)
    result = await AGICognitiveEngine().consolidate_learning(
        "Some goal", "Some sufficiently long outcome.", []
    )

    assert result["status"] == "error"
    assert "memory offline" in result["error"]
