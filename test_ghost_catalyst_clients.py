"""Unit tests for GhostClient and CatalystClient classes directly.

Tests the in-memory client implementations without HTTP routing.
All state is isolated per test via fresh client instances.

Run:
    pytest test_ghost_catalyst_clients.py -v
"""

from __future__ import annotations

import time

import pytest

from jebat.features.ghost.ghost_integration import (
    DatabaseStatus,
    GhostClient,
    GhostCheckpoint,
    GhostDatabase,
    GhostWorkspace,
    WorkspaceStatus,
    create_ghost_client,
)
from jebat.features.catalyst.catalyst_integration import (
    CatalystClient,
    CatalystSpan,
    CatalystTrace,
    SpanKind,
    SpanStatus,
    create_catalyst_client,
)


# ═══════════════════════════════════════════════════════════════════════
# Ghost Client — Database Operations
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.unit
@pytest.mark.ghost
class TestGhostDatabaseCRUD:
    """Create / Read / Update / Delete for Ghost databases."""

    @pytest.mark.asyncio
    async def test_create_database(self):
        client = GhostClient()
        db = await client.create_database("test-db")
        assert db.id.startswith("ghost_")
        assert db.name == "test-db"
        assert db.status == DatabaseStatus.ACTIVE
        assert db.created_at > 0

    @pytest.mark.asyncio
    async def test_create_database_with_parent(self):
        client = GhostClient()
        parent = await client.create_database("parent")
        child = await client.create_database("child", parent_id=parent.id)
        assert child.parent_id == parent.id

    @pytest.mark.asyncio
    async def test_create_database_with_metadata(self):
        client = GhostClient()
        db = await client.create_database("meta-db", metadata={"env": "test"})
        assert db.metadata == {"env": "test"}

    @pytest.mark.asyncio
    async def test_list_databases_empty(self):
        client = GhostClient()
        assert await client.list_databases() == []

    @pytest.mark.asyncio
    async def test_list_databases(self):
        client = GhostClient()
        await client.create_database("db1")
        await client.create_database("db2")
        dbs = await client.list_databases()
        assert len(dbs) == 2
        names = {db.name for db in dbs}
        assert names == {"db1", "db2"}

    @pytest.mark.asyncio
    async def test_get_database(self):
        client = GhostClient()
        db = await client.create_database("lookup")
        fetched = await client.get_database(db.id)
        assert fetched is not None
        assert fetched.name == "lookup"

    @pytest.mark.asyncio
    async def test_get_database_not_found(self):
        client = GhostClient()
        assert await client.get_database("nonexistent") is None

    @pytest.mark.asyncio
    async def test_delete_database(self):
        client = GhostClient()
        db = await client.create_database("to-delete")
        assert await client.delete_database(db.id) is True
        assert await client.get_database(db.id) is None

    @pytest.mark.asyncio
    async def test_delete_database_cascades_workspaces(self):
        client = GhostClient()
        db = await client.create_database("parent")
        ws = await client.fork_database(db.id, "agent-1")
        assert await client.delete_database(db.id) is True
        assert await client.get_workspace(ws.id) is None

    @pytest.mark.asyncio
    async def test_delete_database_not_found(self):
        client = GhostClient()
        assert await client.delete_database("nonexistent") is False


# ═══════════════════════════════════════════════════════════════════════
# Ghost Client — Fork & Workspace Operations
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.unit
@pytest.mark.ghost
class TestGhostForkWorkspace:
    """Fork databases into workspaces and manage them."""

    @pytest.mark.asyncio
    async def test_fork_database(self):
        client = GhostClient()
        db = await client.create_database("source")
        ws = await client.fork_database(db.id, "agent-1")
        assert ws.id.startswith("ws_")
        assert ws.database_id == db.id
        assert ws.agent_id == "agent-1"
        assert ws.status == WorkspaceStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_fork_database_with_metadata(self):
        client = GhostClient()
        db = await client.create_database("source")
        ws = await client.fork_database(db.id, "agent-1", metadata={"task": "audit"})
        assert ws.metadata == {"task": "audit"}

    @pytest.mark.asyncio
    async def test_fork_database_not_found(self):
        client = GhostClient()
        with pytest.raises(ValueError, match="not found"):
            await client.fork_database("nonexistent", "agent-1")

    @pytest.mark.asyncio
    async def test_list_workspaces(self):
        client = GhostClient()
        db = await client.create_database("src")
        await client.fork_database(db.id, "agent-1")
        await client.fork_database(db.id, "agent-2")
        wss = await client.list_workspaces()
        assert len(wss) == 2

    @pytest.mark.asyncio
    async def test_list_workspaces_filtered_by_database(self):
        client = GhostClient()
        db1 = await client.create_database("db1")
        db2 = await client.create_database("db2")
        await client.fork_database(db1.id, "agent-1")
        await client.fork_database(db2.id, "agent-2")

        ws_db1 = await client.list_workspaces(database_id=db1.id)
        assert len(ws_db1) == 1
        assert ws_db1[0].database_id == db1.id

    @pytest.mark.asyncio
    async def test_get_workspace(self):
        client = GhostClient()
        db = await client.create_database("src")
        ws = await client.fork_database(db.id, "agent-1")
        fetched = await client.get_workspace(ws.id)
        assert fetched is not None
        assert fetched.agent_id == "agent-1"

    @pytest.mark.asyncio
    async def test_get_workspace_not_found(self):
        client = GhostClient()
        assert await client.get_workspace("nonexistent") is None


# ═══════════════════════════════════════════════════════════════════════
# Ghost Client — SQL Execution
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.unit
@pytest.mark.ghost
class TestGhostSQL:
    """SQL execution and history tracking."""

    @pytest.mark.asyncio
    async def test_execute_sql(self):
        client = GhostClient()
        db = await client.create_database("db")
        result = await client.execute_sql(db.id, "SELECT 1")
        assert result["db_id"] == db.id
        assert result["query"] == "SELECT 1"
        assert result["rows_affected"] == 0
        assert result["result"] == []

    @pytest.mark.asyncio
    async def test_execute_sql_with_params(self):
        client = GhostClient()
        db = await client.create_database("db")
        result = await client.execute_sql(db.id, "SELECT * WHERE id=$1", params={"$1": 42})
        assert result["params"] == {"$1": 42}

    @pytest.mark.asyncio
    async def test_sql_history(self):
        client = GhostClient()
        db = await client.create_database("db")
        await client.execute_sql(db.id, "SELECT 1")
        await client.execute_sql(db.id, "SELECT 2")
        history = await client.get_sql_history()
        assert len(history) == 2
        assert history[0]["query"] == "SELECT 1"
        assert history[1]["query"] == "SELECT 2"

    @pytest.mark.asyncio
    async def test_sql_history_filtered_by_db(self):
        client = GhostClient()
        db1 = await client.create_database("db1")
        db2 = await client.create_database("db2")
        await client.execute_sql(db1.id, "SELECT 1")
        await client.execute_sql(db2.id, "SELECT 2")

        history = await client.get_sql_history(db_id=db1.id)
        assert len(history) == 1
        assert history[0]["db_id"] == db1.id

    @pytest.mark.asyncio
    async def test_sql_history_limit(self):
        client = GhostClient()
        db = await client.create_database("db")
        for i in range(10):
            await client.execute_sql(db.id, f"SELECT {i}")
        history = await client.get_sql_history(limit=3)
        assert len(history) == 3
        assert history[0]["query"] == "SELECT 7"


# ═══════════════════════════════════════════════════════════════════════
# Ghost Client — Checkpoints
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.unit
@pytest.mark.ghost
class TestGhostCheckpoints:
    """Checkpoint creation, listing, and restoration."""

    @pytest.mark.asyncio
    async def test_create_checkpoint(self):
        client = GhostClient()
        db = await client.create_database("db")
        cp = await client.create_checkpoint(db.id, "before-migration")
        assert cp.id.startswith("cp_")
        assert cp.database_id == db.id
        assert cp.label == "before-migration"
        assert cp.created_at > 0

    @pytest.mark.asyncio
    async def test_list_checkpoints(self):
        client = GhostClient()
        db = await client.create_database("db")
        await client.create_checkpoint(db.id, "cp1")
        await client.create_checkpoint(db.id, "cp2")
        cps = await client.list_checkpoints()
        assert len(cps) == 2

    @pytest.mark.asyncio
    async def test_list_checkpoints_filtered_by_db(self):
        client = GhostClient()
        db1 = await client.create_database("db1")
        db2 = await client.create_database("db2")
        await client.create_checkpoint(db1.id, "cp1")
        await client.create_checkpoint(db2.id, "cp2")
        cps = await client.list_checkpoints(db_id=db1.id)
        assert len(cps) == 1
        assert cps[0].database_id == db1.id

    @pytest.mark.asyncio
    async def test_restore_checkpoint(self):
        client = GhostClient()
        db = await client.create_database("db")
        cp = await client.create_checkpoint(db.id, "snapshot")
        assert await client.restore_checkpoint(cp.id) is True

    @pytest.mark.asyncio
    async def test_restore_checkpoint_not_found(self):
        client = GhostClient()
        assert await client.restore_checkpoint("nonexistent") is False


# ═══════════════════════════════════════════════════════════════════════
# Ghost Client — Cleanup & Status
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.unit
@pytest.mark.ghost
class TestGhostCleanupStatus:
    """Idle workspace cleanup and status reporting."""

    @pytest.mark.asyncio
    async def test_cleanup_idle_workspaces(self):
        client = GhostClient()
        db = await client.create_database("db")
        ws = await client.fork_database(db.id, "agent-1")
        # Manually age the workspace
        ws.last_accessed = time.time() - (25 * 3600)  # 25 hours ago
        cleaned = await client.cleanup_idle_workspaces(idle_hours=24)
        assert cleaned == 1
        updated = await client.get_workspace(ws.id)
        assert updated.status == WorkspaceStatus.CLEANED

    @pytest.mark.asyncio
    async def test_cleanup_preserves_recent_workspaces(self):
        client = GhostClient()
        db = await client.create_database("db")
        ws = await client.fork_database(db.id, "agent-1")
        # Workspace is brand new — should not be cleaned
        cleaned = await client.cleanup_idle_workspaces(idle_hours=24)
        assert cleaned == 0
        updated = await client.get_workspace(ws.id)
        assert updated.status == WorkspaceStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_get_status(self):
        client = GhostClient()
        db = await client.create_database("db")
        await client.fork_database(db.id, "agent-1")
        await client.create_checkpoint(db.id, "cp1")
        await client.execute_sql(db.id, "SELECT 1")
        status = client.get_status()
        assert status["databases"] == 1
        assert status["workspaces"] == 1
        assert status["active_workspaces"] == 1
        assert status["checkpoints"] == 1
        assert status["sql_queries_executed"] == 1

    @pytest.mark.asyncio
    async def test_get_status_empty(self):
        client = GhostClient()
        status = client.get_status()
        assert status["databases"] == 0
        assert status["workspaces"] == 0
        assert status["checkpoints"] == 0
        assert status["sql_queries_executed"] == 0


# ═══════════════════════════════════════════════════════════════════════
# Ghost Client — Factory
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.unit
@pytest.mark.ghost
class TestGhostFactory:
    @pytest.mark.asyncio
    async def test_create_ghost_client(self):
        client = await create_ghost_client()
        assert isinstance(client, GhostClient)
        assert client.config == {}

    @pytest.mark.asyncio
    async def test_create_ghost_client_with_config(self):
        client = await create_ghost_client(config={"max_dbs": 10})
        assert client.config == {"max_dbs": 10}


# ═══════════════════════════════════════════════════════════════════════
# Catalyst Client — Instrumentation
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.unit
@pytest.mark.catalyst
class TestCatalystInstrumentation:
    @pytest.mark.asyncio
    async def test_instrument(self):
        client = CatalystClient()
        assert client.is_instrumented() is False
        result = await client.instrument()
        assert result["status"] == "instrumented"
        assert "agents" in result["components"]
        assert client.is_instrumented() is True


# ═══════════════════════════════════════════════════════════════════════
# Catalyst Client — Span Operations
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.unit
@pytest.mark.catalyst
class TestCatalystSpans:
    @pytest.mark.asyncio
    async def test_start_span_creates_trace(self):
        client = CatalystClient()
        span = await client.start_span("llm-call")
        assert span.id.startswith("span_")
        assert span.trace_id.startswith("trace_")
        assert span.name == "llm-call"
        assert span.kind == SpanKind.INTERNAL
        assert client.get_stats()["active_spans"] == 1
        assert client.get_stats()["total_traces"] == 1

    @pytest.mark.asyncio
    async def test_start_span_in_existing_trace(self):
        client = CatalystClient()
        s1 = await client.start_span("step-1")
        s2 = await client.start_span("step-2", trace_id=s1.trace_id)
        assert s2.trace_id == s1.trace_id
        assert client.get_stats()["total_traces"] == 1
        assert client.get_stats()["total_spans"] == 2

    @pytest.mark.asyncio
    async def test_start_span_with_kind(self):
        client = CatalystClient()
        span = await client.start_span("llm-call", kind=SpanKind.LLM)
        assert span.kind == SpanKind.LLM

    @pytest.mark.asyncio
    async def test_start_span_with_parent(self):
        client = CatalystClient()
        parent = await client.start_span("parent")
        child = await client.start_span("child", parent_id=parent.id)
        assert child.parent_id == parent.id

    @pytest.mark.asyncio
    async def test_start_span_with_attributes(self):
        client = CatalystClient()
        span = await client.start_span("op", attributes={"model": "qwen"})
        assert span.attributes == {"model": "qwen"}

    @pytest.mark.asyncio
    async def test_end_span(self):
        client = CatalystClient()
        span = await client.start_span("llm-call")
        ended = await client.end_span(span.id)
        assert ended is not None
        assert ended.status == SpanStatus.OK
        assert ended.end_time > 0
        assert ended.duration_ms >= 0
        assert client.get_stats()["active_spans"] == 0

    @pytest.mark.asyncio
    async def test_end_span_with_error_status(self):
        client = CatalystClient()
        span = await client.start_span("failing-op")
        ended = await client.end_span(span.id, status=SpanStatus.ERROR)
        assert ended.status == SpanStatus.ERROR

    @pytest.mark.asyncio
    async def test_end_span_with_attributes(self):
        client = CatalystClient()
        span = await client.start_span("op")
        ended = await client.end_span(span.id, attributes={"result": "success"})
        assert ended.attributes["result"] == "success"

    @pytest.mark.asyncio
    async def test_end_span_not_found(self):
        client = CatalystClient()
        assert await client.end_span("nonexistent") is None

    @pytest.mark.asyncio
    async def test_end_span_attaches_to_trace(self):
        client = CatalystClient()
        span = await client.start_span("op")
        await client.end_span(span.id)
        trace = await client.get_trace(span.trace_id)
        assert trace is not None
        assert len(trace.spans) == 1
        assert trace.spans[0].id == span.id


# ═══════════════════════════════════════════════════════════════════════
# Catalyst Client — Event Recording
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.unit
@pytest.mark.catalyst
class TestCatalystEvents:
    @pytest.mark.asyncio
    async def test_record_event(self):
        client = CatalystClient()
        span = await client.start_span("op")
        result = await client.record_event(span.id, "retry", attributes={"attempt": 2})
        assert result is True
        ended = await client.end_span(span.id)
        assert len(ended.events) == 1
        assert ended.events[0]["name"] == "retry"
        assert ended.events[0]["attributes"]["attempt"] == 2

    @pytest.mark.asyncio
    async def test_record_event_on_missing_span(self):
        client = CatalystClient()
        assert await client.record_event("nonexistent", "event") is False


# ═══════════════════════════════════════════════════════════════════════
# Catalyst Client — Trace Operations
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.unit
@pytest.mark.catalyst
class TestCatalystTraces:
    @pytest.mark.asyncio
    async def test_get_trace(self):
        client = CatalystClient()
        span = await client.start_span("op")
        trace = await client.get_trace(span.trace_id)
        assert trace is not None
        assert trace.id == span.trace_id

    @pytest.mark.asyncio
    async def test_get_trace_not_found(self):
        client = CatalystClient()
        assert await client.get_trace("nonexistent") is None

    @pytest.mark.asyncio
    async def test_list_traces_empty(self):
        client = CatalystClient()
        assert await client.list_traces() == []

    @pytest.mark.asyncio
    async def test_list_traces_sorted_newest_first(self):
        client = CatalystClient()
        s1 = await client.start_span("first")
        await client.end_span(s1.id)
        s2 = await client.start_span("second")
        await client.end_span(s2.id)
        traces = await client.list_traces()
        assert len(traces) == 2
        assert traces[0].start_time >= traces[1].start_time

    @pytest.mark.asyncio
    async def test_list_traces_limit(self):
        client = CatalystClient()
        for i in range(5):
            s = await client.start_span(f"op-{i}")
            await client.end_span(s.id)
        traces = await client.list_traces(limit=2)
        assert len(traces) == 2

    @pytest.mark.asyncio
    async def test_get_trace_spans(self):
        client = CatalystClient()
        s1 = await client.start_span("step-1")
        s2 = await client.start_span("step-2", trace_id=s1.trace_id)
        await client.end_span(s1.id)
        await client.end_span(s2.id)
        spans = await client.get_trace_spans(s1.trace_id)
        assert len(spans) == 2

    @pytest.mark.asyncio
    async def test_get_trace_spans_not_found(self):
        client = CatalystClient()
        assert await client.get_trace_spans("nonexistent") == []


# ═══════════════════════════════════════════════════════════════════════
# Catalyst Client — HALO Analysis
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.unit
@pytest.mark.catalyst
class TestCatalystHALO:
    @pytest.mark.asyncio
    async def test_halo_analysis(self):
        client = CatalystClient()
        s1 = await client.start_span("trace-a-step")
        await client.end_span(s1.id, status=SpanStatus.OK)
        s2 = await client.start_span("trace-b-step")
        await client.end_span(s2.id, status=SpanStatus.OK)

        result = await client.halo_analysis(s1.trace_id, s2.trace_id)
        assert "trace_a" in result
        assert "trace_b" in result
        assert "comparison" in result
        assert "recommendations" in result
        assert result["comparison"]["span_diff"] == 0

    @pytest.mark.asyncio
    async def test_halo_analysis_trace_not_found(self):
        client = CatalystClient()
        result = await client.halo_analysis("missing-a", "missing-b")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_halo_analysis_performance_regression(self):
        """Trace B significantly slower than Trace A triggers regression recommendation."""
        client = CatalystClient()
        # Fast trace
        s1 = await client.start_span("fast")
        await client.end_span(s1.id)
        # Slow trace (simulate by manually adjusting span duration)
        s2 = await client.start_span("slow")
        ended = await client.end_span(s2.id)
        ended.duration_ms = 10000  # 10 seconds
        trace_a = await client.get_trace(s1.trace_id)
        trace_b = await client.get_trace(s2.trace_id)
        trace_b.duration_ms = 10000

        result = await client.halo_analysis(trace_a.id, trace_b.id)
        recs = result["recommendations"]
        assert any("regression" in r.lower() for r in recs)

    @pytest.mark.asyncio
    async def test_halo_analysis_high_llm_latency(self):
        """LLM spans averaging >5000ms triggers latency recommendation."""
        client = CatalystClient()
        # Trace A with no spans
        s_a = await client.start_span("trace-a")
        await client.end_span(s_a.id)
        # Trace B with slow LLM spans
        s_b = await client.start_span("trace-b")
        await client.end_span(s_b.id)
        trace_a = await client.get_trace(s_a.trace_id)
        trace_b = await client.get_trace(s_b.trace_id)
        # Add slow LLM spans manually
        slow_llm = CatalystSpan(
            id="llm-1", trace_id=trace_b.id, name="llm-call",
            kind=SpanKind.LLM, duration_ms=8000,
        )
        trace_b.spans.append(slow_llm)

        result = await client.halo_analysis(trace_a.id, trace_b.id)
        recs = result["recommendations"]
        assert any("llm latency" in r.lower() for r in recs)

    @pytest.mark.asyncio
    async def test_halo_analysis_no_issues(self):
        """Similar traces produce a 'no issues' recommendation."""
        client = CatalystClient()
        s1 = await client.start_span("a")
        await client.end_span(s1.id)
        s2 = await client.start_span("b")
        await client.end_span(s2.id)

        result = await client.halo_analysis(s1.trace_id, s2.trace_id)
        recs = result["recommendations"]
        assert any("no significant issues" in r.lower() for r in recs)


# ═══════════════════════════════════════════════════════════════════════
# Catalyst Client — Status & Factory
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.unit
@pytest.mark.catalyst
class TestCatalystStatus:
    @pytest.mark.asyncio
    async def test_get_stats_empty(self):
        client = CatalystClient()
        stats = client.get_stats()
        assert stats["instrumented"] is False
        assert stats["total_traces"] == 0
        assert stats["total_spans"] == 0
        assert stats["active_spans"] == 0
        assert stats["completed_traces"] == 0

    @pytest.mark.asyncio
    async def test_get_stats_after_operations(self):
        client = CatalystClient()
        await client.instrument()
        s1 = await client.start_span("op-1")
        s2 = await client.start_span("op-2")
        await client.end_span(s1.id)
        # s2 is still active
        stats = client.get_stats()
        assert stats["instrumented"] is True
        assert stats["total_traces"] == 2
        assert stats["total_spans"] == 2
        assert stats["active_spans"] == 1
        assert stats["completed_traces"] == 2

    @pytest.mark.asyncio
    async def test_create_catalyst_client(self):
        client = await create_catalyst_client()
        assert isinstance(client, CatalystClient)
        assert client.config == {}

    @pytest.mark.asyncio
    async def test_create_catalyst_client_with_config(self):
        client = await create_catalyst_client(config={"sample_rate": 0.5})
        assert client.config == {"sample_rate": 0.5}
