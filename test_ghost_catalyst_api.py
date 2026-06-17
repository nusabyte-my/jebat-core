"""Integration tests for Ghost Database and Catalyst Observability API endpoints.

Uses httpx.AsyncClient with ASGITransport against the FastAPI app.
Both GhostClient and CatalystClient are in-memory, so no external services needed.

Run:
    pytest test_ghost_catalyst_api.py -v
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from main import app
import routers.ghost as ghost_router
import routers.catalyst as catalyst_router


@pytest_asyncio.fixture(autouse=True)
async def _reset_clients():
    """Reset singleton clients before each test for isolation."""
    ghost_router._client = None
    catalyst_router._client = None
    yield
    ghost_router._client = None
    catalyst_router._client = None


@pytest_asyncio.fixture
async def client():
    """Async HTTP client wired to the FastAPI app via ASGITransport."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# ═══════════════════════════════════════════════════════════════════════
# Ghost Database API Tests
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.ghost
class TestGhostStatus:
    @pytest.mark.asyncio
    async def test_status_returns_200(self, client: AsyncClient):
        resp = await client.get("/api/ghost/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "databases" in data
        assert "workspaces" in data
        assert "checkpoints" in data


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.ghost
class TestGhostDatabases:
    @pytest.mark.asyncio
    async def test_list_databases_empty(self, client: AsyncClient):
        resp = await client.get("/api/ghost/databases")
        assert resp.status_code == 200
        data = resp.json()
        assert data["databases"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_create_database(self, client: AsyncClient):
        resp = await client.post("/api/ghost/databases", json={"name": "test-db"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "test-db"
        assert data["status"] == "active"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_database_with_parent(self, client: AsyncClient):
        # Create parent
        parent = await client.post("/api/ghost/databases", json={"name": "parent"})
        parent_id = parent.json()["id"]

        # Create child
        resp = await client.post(
            "/api/ghost/databases",
            json={"name": "child", "parent_id": parent_id},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["parent_id"] == parent_id

    @pytest.mark.asyncio
    async def test_get_database(self, client: AsyncClient):
        create_resp = await client.post("/api/ghost/databases", json={"name": "my-db"})
        db_id = create_resp.json()["id"]

        resp = await client.get(f"/api/ghost/databases/{db_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == db_id

    @pytest.mark.asyncio
    async def test_get_database_not_found(self, client: AsyncClient):
        resp = await client.get("/api/ghost/databases/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_database(self, client: AsyncClient):
        create_resp = await client.post("/api/ghost/databases", json={"name": "del-me"})
        db_id = create_resp.json()["id"]

        resp = await client.delete(f"/api/ghost/databases/{db_id}")
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

        # Verify gone
        get_resp = await client.get(f"/api/ghost/databases/{db_id}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_database_not_found(self, client: AsyncClient):
        resp = await client.delete("/api/ghost/databases/nonexistent")
        assert resp.status_code == 404


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.ghost
class TestGhostFork:
    @pytest.mark.asyncio
    async def test_fork_database(self, client: AsyncClient):
        db_resp = await client.post("/api/ghost/databases", json={"name": "source"})
        db_id = db_resp.json()["id"]

        resp = await client.post(
            "/api/ghost/fork",
            json={"source_db_id": db_id, "agent_id": "agent-1"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["database_id"] == db_id
        assert data["agent_id"] == "agent-1"
        assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_fork_database_not_found(self, client: AsyncClient):
        resp = await client.post(
            "/api/ghost/fork",
            json={"source_db_id": "nonexistent", "agent_id": "agent-1"},
        )
        assert resp.status_code == 404


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.ghost
class TestGhostWorkspaces:
    @pytest.mark.asyncio
    async def test_list_workspaces_empty(self, client: AsyncClient):
        resp = await client.get("/api/ghost/workspaces")
        assert resp.status_code == 200
        data = resp.json()
        assert data["workspaces"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_workspaces_after_fork(self, client: AsyncClient):
        db_resp = await client.post("/api/ghost/databases", json={"name": "ws-test"})
        db_id = db_resp.json()["id"]

        await client.post(
            "/api/ghost/fork",
            json={"source_db_id": db_id, "agent_id": "agent-1"},
        )

        resp = await client.get(f"/api/ghost/workspaces?database_id={db_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_get_workspace(self, client: AsyncClient):
        db_resp = await client.post("/api/ghost/databases", json={"name": "ws-get"})
        db_id = db_resp.json()["id"]

        fork_resp = await client.post(
            "/api/ghost/fork",
            json={"source_db_id": db_id, "agent_id": "agent-2"},
        )
        ws_id = fork_resp.json()["id"]

        resp = await client.get(f"/api/ghost/workspaces/{ws_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == ws_id

    @pytest.mark.asyncio
    async def test_get_workspace_not_found(self, client: AsyncClient):
        resp = await client.get("/api/ghost/workspaces/nonexistent")
        assert resp.status_code == 404


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.ghost
class TestGhostSQL:
    @pytest.mark.asyncio
    async def test_execute_sql(self, client: AsyncClient):
        db_resp = await client.post("/api/ghost/databases", json={"name": "sql-db"})
        db_id = db_resp.json()["id"]

        resp = await client.post(
            "/api/ghost/sql",
            json={"db_id": db_id, "query": "SELECT 1"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "SELECT 1"
        assert data["db_id"] == db_id

    @pytest.mark.asyncio
    async def test_execute_sql_database_not_found(self, client: AsyncClient):
        resp = await client.post(
            "/api/ghost/sql",
            json={"db_id": "nonexistent", "query": "SELECT 1"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_sql_history(self, client: AsyncClient):
        db_resp = await client.post("/api/ghost/databases", json={"name": "hist-db"})
        db_id = db_resp.json()["id"]

        await client.post(
            "/api/ghost/sql",
            json={"db_id": db_id, "query": "SELECT 1"},
        )
        await client.post(
            "/api/ghost/sql",
            json={"db_id": db_id, "query": "SELECT 2"},
        )

        resp = await client.get(f"/api/ghost/sql/history?db_id={db_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.ghost
class TestGhostCheckpoints:
    @pytest.mark.asyncio
    async def test_create_checkpoint(self, client: AsyncClient):
        db_resp = await client.post("/api/ghost/databases", json={"name": "cp-db"})
        db_id = db_resp.json()["id"]

        resp = await client.post(
            "/api/ghost/checkpoint",
            json={"db_id": db_id, "label": "snapshot-v1"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["label"] == "snapshot-v1"
        assert data["database_id"] == db_id

    @pytest.mark.asyncio
    async def test_list_checkpoints(self, client: AsyncClient):
        db_resp = await client.post("/api/ghost/databases", json={"name": "cp-list"})
        db_id = db_resp.json()["id"]

        await client.post(
            "/api/ghost/checkpoint",
            json={"db_id": db_id, "label": "snap-1"},
        )
        await client.post(
            "/api/ghost/checkpoint",
            json={"db_id": db_id, "label": "snap-2"},
        )

        resp = await client.get(f"/api/ghost/checkpoints?db_id={db_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_restore_checkpoint(self, client: AsyncClient):
        db_resp = await client.post("/api/ghost/databases", json={"name": "cp-restore"})
        db_id = db_resp.json()["id"]

        cp_resp = await client.post(
            "/api/ghost/checkpoint",
            json={"db_id": db_id, "label": "restore-me"},
        )
        cp_id = cp_resp.json()["id"]

        resp = await client.post(f"/api/ghost/checkpoints/{cp_id}/restore")
        assert resp.status_code == 200
        assert resp.json()["restored"] is True

    @pytest.mark.asyncio
    async def test_restore_checkpoint_not_found(self, client: AsyncClient):
        resp = await client.post("/api/ghost/checkpoints/nonexistent/restore")
        assert resp.status_code == 404


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.ghost
class TestGhostCleanup:
    @pytest.mark.asyncio
    async def test_cleanup_idle_workspaces(self, client: AsyncClient):
        resp = await client.post(
            "/api/ghost/cleanup",
            json={"idle_hours": 24.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "cleaned" in data
        assert data["idle_hours"] == 24.0


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.ghost
class TestGhostFullLifecycle:
    @pytest.mark.asyncio
    async def test_full_database_lifecycle(self, client: AsyncClient):
        """Test create → fork → SQL → checkpoint → restore → delete."""
        # Create
        db_resp = await client.post("/api/ghost/databases", json={"name": "lifecycle"})
        db_id = db_resp.json()["id"]

        # Fork
        fork_resp = await client.post(
            "/api/ghost/fork",
            json={"source_db_id": db_id, "agent_id": "agent-lifecycle"},
        )
        assert fork_resp.status_code == 200

        # SQL
        sql_resp = await client.post(
            "/api/ghost/sql",
            json={"db_id": db_id, "query": "CREATE TABLE test (id INT)"},
        )
        assert sql_resp.status_code == 200

        # Checkpoint
        cp_resp = await client.post(
            "/api/ghost/checkpoint",
            json={"db_id": db_id, "label": "before-restore"},
        )
        cp_id = cp_resp.json()["id"]

        # Restore
        restore_resp = await client.post(f"/api/ghost/checkpoints/{cp_id}/restore")
        assert restore_resp.status_code == 200

        # Status shows everything
        status_resp = await client.get("/api/ghost/status")
        status = status_resp.json()
        assert status["databases"] >= 1
        assert status["workspaces"] >= 1
        assert status["checkpoints"] >= 1

        # Delete
        del_resp = await client.delete(f"/api/ghost/databases/{db_id}")
        assert del_resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════
# Catalyst Observability API Tests
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.catalyst
class TestCatalystStatus:
    @pytest.mark.asyncio
    async def test_status_returns_200(self, client: AsyncClient):
        resp = await client.get("/api/catalyst/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "instrumented" in data
        assert "total_traces" in data
        assert "total_spans" in data
        assert "active_spans" in data


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.catalyst
class TestCatalystInstrument:
    @pytest.mark.asyncio
    async def test_instrument(self, client: AsyncClient):
        resp = await client.post("/api/catalyst/instrument")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "instrumented"
        assert "agents" in data["components"]


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.catalyst
class TestCatalystSpans:
    @pytest.mark.asyncio
    async def test_start_span(self, client: AsyncClient):
        resp = await client.post(
            "/api/catalyst/spans",
            json={"name": "llm-call", "kind": "llm"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "llm-call"
        assert data["kind"] == "llm"
        assert data["status"] == "ok"
        assert "trace_id" in data

    @pytest.mark.asyncio
    async def test_start_span_in_existing_trace(self, client: AsyncClient):
        # Start first span (creates trace)
        first = await client.post(
            "/api/catalyst/spans",
            json={"name": "parent-span"},
        )
        trace_id = first.json()["trace_id"]

        # Start second span in same trace
        resp = await client.post(
            "/api/catalyst/spans",
            json={"name": "child-span", "trace_id": trace_id},
        )
        assert resp.status_code == 200
        assert resp.json()["trace_id"] == trace_id

    @pytest.mark.asyncio
    async def test_end_span(self, client: AsyncClient):
        start_resp = await client.post(
            "/api/catalyst/spans",
            json={"name": "short-span"},
        )
        span_id = start_resp.json()["id"]

        resp = await client.post(
            f"/api/catalyst/spans/{span_id}/end",
            json={"status": "ok"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == span_id
        assert data["end_time"] > 0
        assert data["duration_ms"] >= 0

    @pytest.mark.asyncio
    async def test_end_span_not_found(self, client: AsyncClient):
        resp = await client.post(
            "/api/catalyst/spans/nonexistent/end",
            json={"status": "ok"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_record_event(self, client: AsyncClient):
        start_resp = await client.post(
            "/api/catalyst/spans",
            json={"name": "event-span"},
        )
        span_id = start_resp.json()["id"]

        resp = await client.post(
            f"/api/catalyst/spans/{span_id}/event",
            json={"name": "retry", "attributes": {"attempt": 1}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["recorded"] is True
        assert data["event_name"] == "retry"

    @pytest.mark.asyncio
    async def test_record_event_not_found(self, client: AsyncClient):
        resp = await client.post(
            "/api/catalyst/spans/nonexistent/event",
            json={"name": "test-event"},
        )
        assert resp.status_code == 404


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.catalyst
class TestCatalystTraces:
    @pytest.mark.asyncio
    async def test_list_traces_empty(self, client: AsyncClient):
        resp = await client.get("/api/catalyst/traces")
        assert resp.status_code == 200
        data = resp.json()
        assert data["traces"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_traces_after_span(self, client: AsyncClient):
        await client.post(
            "/api/catalyst/spans",
            json={"name": "trace-span"},
        )

        resp = await client.get("/api/catalyst/traces")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_get_trace(self, client: AsyncClient):
        start_resp = await client.post(
            "/api/catalyst/spans",
            json={"name": "get-trace-span"},
        )
        trace_id = start_resp.json()["trace_id"]

        resp = await client.get(f"/api/catalyst/traces/{trace_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["trace"]["id"] == trace_id
        assert isinstance(data["spans"], list)

    @pytest.mark.asyncio
    async def test_get_trace_not_found(self, client: AsyncClient):
        resp = await client.get("/api/catalyst/traces/nonexistent")
        assert resp.status_code == 404


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.catalyst
class TestCatalystHalo:
    @pytest.mark.asyncio
    async def test_halo_analysis(self, client: AsyncClient):
        # Create two traces with spans
        s1 = await client.post(
            "/api/catalyst/spans",
            json={"name": "trace-a-span", "kind": "llm"},
        )
        trace_a = s1.json()["trace_id"]
        await client.post(
            f"/api/catalyst/spans/{s1.json()['id']}/end",
            json={"status": "ok"},
        )

        s2 = await client.post(
            "/api/catalyst/spans",
            json={"name": "trace-b-span", "kind": "llm"},
        )
        trace_b = s2.json()["trace_id"]
        await client.post(
            f"/api/catalyst/spans/{s2.json()['id']}/end",
            json={"status": "ok"},
        )

        resp = await client.post(
            "/api/catalyst/halo",
            json={
                "trace_id_start": trace_a,
                "trace_id_end": trace_b,
                "analysis_type": "full",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "trace_a" in data
        assert "trace_b" in data
        assert "comparison" in data
        assert "recommendations" in data

    @pytest.mark.asyncio
    async def test_halo_analysis_trace_not_found(self, client: AsyncClient):
        resp = await client.post(
            "/api/catalyst/halo",
            json={
                "trace_id_start": "nonexistent-a",
                "trace_id_end": "nonexistent-b",
            },
        )
        assert resp.status_code == 404


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.catalyst
class TestCatalystFullLifecycle:
    @pytest.mark.asyncio
    async def test_full_tracing_lifecycle(self, client: AsyncClient):
        """Test instrument → span → event → end → trace → HALO."""
        # Instrument
        inst_resp = await client.post("/api/catalyst/instrument")
        assert inst_resp.status_code == 200

        # Start span
        s1_resp = await client.post(
            "/api/catalyst/spans",
            json={"name": "request-handler", "kind": "agent"},
        )
        span_id = s1_resp.json()["id"]
        trace_id = s1_resp.json()["trace_id"]

        # Record event
        await client.post(
            f"/api/catalyst/spans/{span_id}/event",
            json={"name": "processing", "attributes": {"step": 1}},
        )

        # End span
        end_resp = await client.post(
            f"/api/catalyst/spans/{span_id}/end",
            json={"status": "ok"},
        )
        assert end_resp.json()["duration_ms"] >= 0

        # Get trace
        trace_resp = await client.get(f"/api/catalyst/traces/{trace_id}")
        assert trace_resp.status_code == 200
        assert len(trace_resp.json()["spans"]) == 1

        # Start second trace for HALO
        s2_resp = await client.post(
            "/api/catalyst/spans",
            json={"name": "optimized-handler", "kind": "agent"},
        )
        trace_b = s2_resp.json()["trace_id"]
        await client.post(
            f"/api/catalyst/spans/{s2_resp.json()['id']}/end",
            json={"status": "ok"},
        )

        # HALO
        halo_resp = await client.post(
            "/api/catalyst/halo",
            json={
                "trace_id_start": trace_id,
                "trace_id_end": trace_b,
                "analysis_type": "full",
            },
        )
        assert halo_resp.status_code == 200
        assert "recommendations" in halo_resp.json()

        # Status shows stats
        status_resp = await client.get("/api/catalyst/status")
        status = status_resp.json()
        assert status["instrumented"] is True
        assert status["total_traces"] >= 2
        assert status["total_spans"] >= 2


# ═══════════════════════════════════════════════════════════════════════
# Root Endpoint Verification
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.api
class TestRootEndpoints:
    @pytest.mark.asyncio
    async def test_root_lists_ghost_and_catalyst(self, client: AsyncClient):
        resp = await client.get("/")
        assert resp.status_code == 200
        endpoints = resp.json()["endpoints"]
        assert "ghost" in endpoints
        assert "catalyst" in endpoints
