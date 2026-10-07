"""Run: python scripts/check_learning.py. Disposable memory/KB, real CLI/MCP, no model calls."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def cli(*args: str, cwd: Path | None = None, stdin: str = "", code: int = 0):
    run = subprocess.run([sys.executable, "-m", "jebat_cli_new", *args], cwd=cwd,
                         input=stdin, capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert run.returncode == code, (args, run.returncode, run.stdout, run.stderr)
    return run


def parsed(*args: str, **kwargs):
    return json.loads(cli("learning", *args, **kwargs).stdout)


async def check_analysis_and_consolidation():
    from jebat.features.memory import EnhancedMemorySystem, MemoryTrace
    from jebat.features.memory.automimpi import AutoMimpi, SelfLearn

    memory = EnhancedMemorySystem(storage_path=Path.home() / "analysis")
    root = str(Path.cwd())
    for index in range(3):
        memory.store(f"database retry timeout evidence {index}", tags={"project:sample", "database", "session", "summary"},
                     context={"project_root": root})
    future = memory.store("clock skew", tags={"project:sample"}, context={"project_root": root})
    future.created_at = datetime.now(timezone.utc) + timedelta(days=2)
    naive = memory.store("legacy UTC timestamp", tags={"project:sample"}, context={"project_root": root})
    naive.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
    naive.last_accessed = datetime.now(timezone.utc).replace(tzinfo=None)
    foreign = memory.store("private foreign evidence", tags={"project:other"}, confidence=0.1)
    foreign.strength = 0.001
    foreign_before = foreign.to_dict()
    original = MemoryTrace.calculate_current_strength
    counted = []
    def count_strength(trace):
        counted.append(trace.trace_id)
        return original(trace)
    with patch.object(MemoryTrace, "calculate_current_strength", count_strength):
        analysis = SelfLearn(memory).analyze("sample", root)
        AutoMimpi(memory)._build_learning_profile(analysis)
    assert len(counted) == 5 and len(set(counted)) == 5
    assert "session" not in analysis["domains"] and "summary" not in analysis["domains"]
    assert analysis["learning_velocity"]["per_hour_24h"] * 24 == 4
    assert analysis["evidence"]["future_timestamp"]["ids"] == [future.trace_id]
    engine = AutoMimpi(memory)
    first = await engine.dream(force=True, project="sample", project_root=root)
    assert first.patterns_extracted == 1 and first.generalizations_created == 1
    second = await engine.dream(force=True, project="sample", project_root=root)
    assert second.patterns_extracted == 0 and second.generalizations_created == 0
    assert len(memory.generalizations) == 1
    assert foreign.to_dict() == foreign_before
    assert (await engine.dream(project="sample", project_root=root)).status == "skipped"
    reloaded = EnhancedMemorySystem(storage_path=memory.storage_path)
    assert len(reloaded.generalizations) == 1 and foreign.trace_id in reloaded.traces

    # Same wording in distinct roots cannot combine into a three-record pattern.
    isolated = EnhancedMemorySystem(storage_path=Path.home() / "cluster-scope", embedding_fn=lambda _: [0.0])
    for index in range(4):
        isolated.store("same database retry timeout " + str(index), tags={"project:same", "database"},
                       context={"project_root": "root-a" if index < 2 else "root-b"})
    result = await isolated.consolidate(force=True)
    assert result.patterns_extracted == 0 and result.generalized_concepts == []
    assert isolated._text_similarity("database retry", "database retry") == 1.0

    # Failed state persistence cannot advance in-process success counters/history.
    prior_count, prior_time = engine.dream_count, engine.last_dream_at
    with patch.object(engine, "_save_state", side_effect=OSError("state unavailable")):
        try:
            await engine.dream(force=True, project="sample", project_root=root)
        except OSError:
            pass
        else:
            raise AssertionError("Failed persistence reported success")
    assert (engine.dream_count, engine.last_dream_at) == (prior_count, prior_time)
    print("PASS one strength calculation per trace, timestamps, scope, repeat dreams, persistence failure")


async def check_tools():
    from jebat.tools import automimpi_tools as tools
    from jebat.features.memory import EnhancedMemorySystem
    from jebat.features.memory.learning_advisor import LearningAdvisor

    first = await tools.session_learning_commit("verified local change", ["Retain scoped lesson"], "session-proof")
    second = await tools.session_learning_commit("verified local change", ["Retain scoped lesson"], "session-proof")
    assert first["memory_ids"] == second["memory_ids"]
    for _ in range(3):
        failure = await tools.mimpi_record_failure("terminal", "password=DO_NOT_STORE_TOKEN refused", "same action")
    assert failure["similar_failures"] == 3
    memory = tools._get_memory()
    assert all("DO_NOT_STORE_TOKEN" not in trace.content for trace in memory.traces.values())
    persisted = EnhancedMemorySystem(storage_path=memory.storage_path)
    assert sum("failure" in trace.tags for trace in persisted.traces.values()) == 3
    advice = await tools.learning_advisor()
    recurring = next(item for item in advice["recommendations"] if item["type"] == "recurring_failure")
    assert len(recurring["evidence_ids"]) == 3
    assert all(citation["root_bound"] for citation in recurring["citations"])
    before = (await tools.learning_kb_status())["records_by_kind"]["advice"]
    again = await tools.learning_advisor()
    assert recurring["record_id"] in {item["record_id"] for item in again["recommendations"]}
    assert (await tools.learning_kb_status())["records_by_kind"]["advice"] == before
    await tools.learning_feedback(recurring["record_id"], "dismissed", "Confirmed dependency outage; password=DO_NOT_STORE_TOKEN")
    assert (await tools.learning_advisor())["suppressed_by_feedback"] == 1
    stored = await tools.learning_kb_search("terminal", "advice")
    assert "DO_NOT_STORE_TOKEN" not in json.dumps(stored)
    report = await tools.mimpi_dream(force=True)
    assert report["status"] == "ok" and report["kb_record_id"]
    assert (await tools.learning_kb_search("AutoMimpi", "dream"))["count"] == 1
    assert (await tools.mimpi_dream())["status"] == "skipped"
    with patch.object(LearningAdvisor, "record_dream", side_effect=OSError("KB write unavailable")):
        result = await tools.mimpi_dream(force=True)
    assert result["status"] == "partial" and "KB write unavailable" in result["persistence_error"]
    assert result["memories_processed"] >= 0
    print("PASS batch idempotency, repeated failures after reload, redaction, evidence, feedback, partial KB failure")
    return recurring["record_id"]


def check_database():
    from jebat.features.wiki.wiki_core import WikiStore

    kb = WikiStore(Path.home() / "db-boundaries")
    current, foreign = str(Path.cwd()), str(Path.cwd().parent / "other")
    record = kb.record_learning(current, "advice", "stable", "database review", "original indexword", {"value": 1}, ["trace-a"])
    assert record == kb.record_learning(current, "advice", "stable", "database review", "updated searchword", {"value": 2}, ["trace-b"])
    assert kb.search_learning(current, "indexword")["count"] == 0
    assert kb.search_learning(current, "searchword")["records"][0]["evidence_ids"] == ["trace-b"]
    assert kb.search_learning(foreign, "searchword")["count"] == 0
    try:
        kb.learning_feedback(foreign, record, "helpful", "Wrong project")
    except ValueError:
        pass
    else:
        raise AssertionError("Cross-project feedback accepted")
    kb.learning_feedback(current, record, "helpful", "Verified reviewed source")
    with sqlite3.connect(kb._db_path) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        connection.execute("INSERT INTO learning_fts(learning_fts, rank) VALUES('integrity-check', 1)")
    assert WikiStore(Path.home() / "db-boundaries").learning_status(current)["feedback_counts"] == {"helpful": 1}
    print("PASS SQLite/FTS upsert, literal search, project boundary, feedback, restart, integrity")


def check_entrypoints(record_id: str):
    # Fresh processes prove persistence rather than in-memory caches.
    result = parsed("advise")
    assert result["suppressed_by_feedback"] == 1
    assert parsed("dream")["status"] == "skipped"
    assert parsed("search", "AutoMimpi", "--kind", "dream")["count"] == 1
    assert parsed("status")["kb"]["feedback_counts"] == {"dismissed": 1}
    foreign = Path.cwd().parent / "other" / Path.cwd().name
    foreign.mkdir(parents=True)
    assert parsed("analyze", cwd=foreign)["analysis"]["knowledge_map"]["total_memories"] == 0
    assert parsed("search", cwd=foreign)["count"] == 0
    cli("learning", "feedback", record_id, "helpful", "--evidence", "Wrong root", cwd=foreign, code=2)
    cli("learning", "advise", "--limit", "0", code=2)
    parsed("feedback", record_id, "helpful", "--evidence", "Source rechecked; recommendation useful")
    assert parsed("status")["kb"]["feedback_counts"] == {"helpful": 1}
    requests = [
        {"id": 1, "method": "initialize", "params": {"protocolVersion": "2026-07-28"}},
        {"id": 2, "method": "tools/call", "params": {"name": "learning_advisor", "arguments": {}}},
        {"id": 3, "method": "resources/read", "params": {"uri": "jebat://kb/learning"}},
        {"id": 4, "method": "resources/read", "params": {"uri": "jebat://learning/profile"}},
        {"id": 5, "method": "tools/call", "params": {"name": "learning_feedback", "arguments": {"record_id": record_id, "outcome": "dismissed", "evidence": "requires permission"}}},
    ]
    wire = "".join(json.dumps({"jsonrpc": "2.0", **request}) + "\n" for request in requests)
    response = cli("mcp", "serve", "--transport", "stdio", stdin=wire)
    frames = [json.loads(line) for line in response.stdout.splitlines() if line.strip()]
    replies = {frame["id"]: frame for frame in frames if "id" in frame}
    advice_payload = json.loads(replies[2]["result"]["content"][0]["text"])
    assert advice_payload["project_root"] == str(Path.cwd())
    assert any(item["record_id"] == record_id for item in advice_payload["recommendations"])
    assert json.loads(replies[3]["result"]["contents"][0]["text"])["count"] >= 1
    assert json.loads(replies[4]["result"]["contents"][0]["text"])["scope"]["project_root"] == str(Path.cwd())
    assert replies[5]["result"]["structuredContent"]["status"] == "approval_required"
    assert parsed("status")["kb"]["feedback_counts"] == {"helpful": 1}
    print("PASS real CLI and MCP, persistent dismissal/restoration, same-name root isolation, feedback approval gate")


def worker():
    assert Path.home().resolve() == Path(os.environ["JEBAT_CHECK_HOME"]).resolve()
    asyncio.run(check_analysis_and_consolidation())
    record_id = asyncio.run(check_tools())
    check_database()
    check_entrypoints(record_id)
    print("PASS complete learning cycle; no live model, production data, or external actions")


if __name__ == "__main__":
    if sys.argv[1:] == ["--worker"]:
        worker()
    else:
        with tempfile.TemporaryDirectory(prefix="jebat-learning-check-") as directory:
            home = Path(directory)
            workspace = home / "sample"
            workspace.mkdir()
            environment = os.environ.copy()
            environment.update(HOME=str(home), USERPROFILE=str(home), JEBAT_CHECK_HOME=str(home),
                               JEBAT_WIKI_DIR=str(home / "wiki"), PYTHONUTF8="1", PYTHONPATH=str(ROOT))
            result = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"],
                                    cwd=workspace, env=environment, timeout=240)
            raise SystemExit(result.returncode)
