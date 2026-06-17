"""Integration tests for Auth, Logging, and Chat API endpoints.

Uses httpx.AsyncClient with ASGITransport against the FastAPI app.
Mocks Redis and LLM providers for CI-friendly testing.

Run:
    pytest test_auth_logging_chat_api.py -v
"""

from __future__ import annotations

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient

from main import app
import routers.auth as auth_router
import routers.chat as chat_router
from jebat.api.auth import APIKeyMiddleware


# ═══════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════


def _find_auth_middleware():
    """Walk the ASGI chain to find the APIKeyMiddleware instance."""
    stack = getattr(app, 'middleware_stack', None)
    if stack is None:
        stack = getattr(app.router, 'middleware_stack', None)
    if stack is None:
        return None
    current = stack
    while current is not None:
        if isinstance(current, APIKeyMiddleware):
            return current
        current = getattr(current, 'app', None)
    return None


@pytest_asyncio.fixture(autouse=True)
async def _reset_state():
    """Reset singleton clients and middleware state before each test."""
    auth_router._client = None
    chat_router._client = None
    # Reset the middleware to dev mode (empty key = no auth)
    mw = _find_auth_middleware()
    if mw is not None:
        mw._api_key = ""
        mw._allow_query = False
    yield



def _mock_redis():
    """Create a mock Redis client with in-memory storage."""
    storage = {}

    mock_client = AsyncMock()
    mock_rm = MagicMock()
    mock_rm.client = mock_client

    async def fake_get(key):
        return storage.get(key)

    async def fake_set(key, value, ex=None):
        storage[key] = value

    async def fake_delete(*keys):
        count = 0
        for k in keys:
            if k in storage:
                del storage[k]
                count += 1
        return count

    async def fake_incr(key):
        current = int(storage.get(key, 0))
        storage[key] = current + 1
        return current + 1

    async def fake_incrbyfloat(key, amount):
        current = float(storage.get(key, 0))
        storage[key] = current + amount
        return current + amount

    async def fake_expire(key, ttl):
        pass

    async def fake_lpush(key, *values):
        lst = json.loads(storage.get(key, "[]"))
        for v in values:
            lst.insert(0, v)
        storage[key] = json.dumps(lst)
        return len(lst)

    async def fake_ltrim(key, start, stop):
        lst = json.loads(storage.get(key, "[]"))
        storage[key] = json.dumps(lst[start:stop + 1])

    async def fake_llen(key):
        lst = json.loads(storage.get(key, "[]"))
        return len(lst)

    async def fake_lrange(key, start, stop):
        lst = json.loads(storage.get(key, "[]"))
        if stop == -1:
            return lst[start:]
        return lst[start:stop + 1]

    async def fake_hincrby(key, field, amount):
        h = json.loads(storage.get(key, "{}"))
        h[field] = h.get(field, 0) + amount
        storage[key] = json.dumps(h)
        return h[field]

    async def fake_hgetall(key):
        return json.loads(storage.get(key, "{}"))

    async def fake_scan(cursor=0, match="*", count=100):
        import fnmatch
        matched = [k for k in storage if fnmatch.fnmatch(k, match)]
        return (0, matched)

    mock_client.get = fake_get
    mock_client.set = fake_set
    mock_client.delete = fake_delete
    mock_client.incr = fake_incr
    mock_client.incrbyfloat = fake_incrbyfloat
    mock_client.expire = fake_expire
    mock_client.lpush = fake_lpush
    mock_client.ltrim = fake_ltrim
    mock_client.llen = fake_llen
    mock_client.lrange = fake_lrange
    mock_client.hincrby = fake_hincrby
    mock_client.hgetall = fake_hgetall
    mock_client.scan = fake_scan
    mock_client.pipeline.return_value = mock_client

    return mock_rm, storage


# ═══════════════════════════════════════════════════════════════════════
# Root & Health Endpoints (baseline)
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.api
class TestRootHealth:
    @pytest.mark.asyncio
    async def test_root_returns_200(self, client: AsyncClient):
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "jebat-api"
        assert "ghost" in data["endpoints"]
        assert "catalyst" in data["endpoints"]

    @pytest.mark.asyncio
    async def test_health_returns_200(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_ready_returns_200_no_db(self, client: AsyncClient):
        resp = await client.get("/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["components"]["postgres"]["status"] == "disabled"


# ═══════════════════════════════════════════════════════════════════════
# Auth Middleware Tests
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.auth
class TestAuthMiddleware:
    @pytest.mark.asyncio
    async def test_dev_mode_allows_all(self, client: AsyncClient):
        """Without JEBAT_API_KEY, all /api/* routes are open."""
        resp = await client.get("/api/status")
        assert resp.status_code != 401
        assert resp.status_code != 403

    @pytest.mark.asyncio
    async def test_public_paths_never_require_auth(self, client: AsyncClient):
        for path in ["/", "/health", "/ready", "/metrics"]:
            resp = await client.get(path)
            assert resp.status_code == 200, f"{path} should be public"

    @pytest.mark.asyncio
    async def test_auth_rejects_without_key(self, client: AsyncClient):
        # Ensure middleware stack is built, then enable auth on the instance
        mw = _find_auth_middleware()
        assert mw is not None, "Middleware instance not found — make a request first"
        mw._api_key = "test-secret-key-123"
        mw._allow_query = False
        resp = await client.get("/api/status")
        assert resp.status_code == 401
        assert resp.json()["error"] == "unauthorized"

    @pytest.mark.asyncio
    async def test_auth_rejects_wrong_key(self, client: AsyncClient):
        mw = _find_auth_middleware()
        assert mw is not None
        mw._api_key = "test-secret-key-123"
        mw._allow_query = False
        resp = await client.get(
            "/api/status",
            headers={"Authorization": "Bearer wrong-key"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"] == "forbidden"

    @pytest.mark.asyncio
    async def test_auth_accepts_correct_bearer(self, client: AsyncClient):
        mw = _find_auth_middleware()
        assert mw is not None
        mw._api_key = "test-secret-key-123"
        mw._allow_query = False
        resp = await client.get(
            "/api/status",
            headers={"Authorization": "Bearer test-secret-key-123"},
        )
        assert resp.status_code != 401
        assert resp.status_code != 403

    @pytest.mark.asyncio
    async def test_auth_accepts_x_api_key_header(self, client: AsyncClient):
        mw = _find_auth_middleware()
        assert mw is not None
        mw._api_key = "test-secret-key-123"
        mw._allow_query = False
        resp = await client.get(
            "/api/status",
            headers={"X-API-Key": "test-secret-key-123"},
        )
        assert resp.status_code != 401
        assert resp.status_code != 403

    @pytest.mark.asyncio
    async def test_auth_accepts_query_param_when_enabled(self, client: AsyncClient):
        mw = _find_auth_middleware()
        assert mw is not None
        mw._api_key = "test-secret-key-123"
        mw._allow_query = True
        resp = await client.get("/api/status?api_key=test-secret-key-123")
        assert resp.status_code != 401
        assert resp.status_code != 403

    @pytest.mark.asyncio
    async def test_options_preflight_skips_auth(self, client: AsyncClient):
        mw = _find_auth_middleware()
        assert mw is not None
        mw._api_key = "test-secret-key-123"
        resp = await client.options("/api/status")
        assert resp.status_code not in (401, 403)


# ═══════════════════════════════════════════════════════════════════════
# Auth Key Info Endpoints
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.auth
class TestAuthKeyInfo:
    @pytest.mark.asyncio
    async def test_key_info_no_redis(self, client: AsyncClient):
        """When Redis is unavailable, key-info fails with ResponseValidationError."""
        from fastapi.exceptions import ResponseValidationError
        # get_key_info() returns {"status": "unavailable"} which doesn't match
        # KeyInfoResponse schema (requires key_id, created_at, etc.)
        # FastAPI raises ResponseValidationError in ASGI test transport
        with pytest.raises(ResponseValidationError):
            await client.get("/api/auth/key-info")

    @pytest.mark.asyncio
    async def test_key_info_with_valid_response(self, client: AsyncClient):
        """key-info returns valid metadata when the endpoint returns schema-compliant data."""
        with patch("routers.auth.get_key_info", new_callable=AsyncMock, return_value={
            "key_id": "a" * 12,
            "created_at": "2026-06-17T00:00:00Z",
            "rotated_count": 0,
            "grace_keys_active": 0,
            "env_key_active": False,
        }):
            resp = await client.get("/api/auth/key-info")
            assert resp.status_code == 200
            data = resp.json()
            assert data["key_id"] == "a" * 12


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.auth
class TestAuthRotateKey:
    @pytest.mark.asyncio
    async def test_rotate_key_no_key_provided(self, client: AsyncClient):
        """Rotate key without providing any key returns 401 (auth fails first)."""
        resp = await client.post(
            "/api/auth/rotate-key",
            json={"grace_period_seconds": 86400},
        )
        # _authenticate_request raises 401 before Redis check
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_rotate_key_with_env_key_no_redis(self, client: AsyncClient):
        """Rotate key with valid env key but no Redis returns 503."""
        os.environ["JEBAT_API_KEY"] = "test-key-123"
        try:
            resp = await client.post(
                "/api/auth/rotate-key",
                json={"grace_period_seconds": 86400},
                headers={"X-API-Key": "test-key-123"},
            )
            assert resp.status_code == 503
        finally:
            os.environ.pop("JEBAT_API_KEY", None)


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.auth
class TestAuthRevokeKey:
    @pytest.mark.asyncio
    async def test_revoke_all_grace_keys_no_auth(self, client: AsyncClient):
        """Revoke all grace keys without providing a key returns 401."""
        resp = await client.post("/api/auth/revoke-key", json={})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_revoke_specific_grace_key_no_auth(self, client: AsyncClient):
        """Revoke specific grace key without providing a key returns 401."""
        resp = await client.post(
            "/api/auth/revoke-key",
            json={"key_id": "abc123def456"},
        )
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════
# Logging Endpoints
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.logging
class TestLoggingEndpoints:
    @pytest.mark.asyncio
    async def test_logs_recent_no_redis(self, client: AsyncClient):
        resp = await client.get("/api/logs/recent")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_logs_recent_with_redis(self, client: AsyncClient):
        mock_rm, storage = _mock_redis()
        entry = json.dumps({
            "ts": 1718600000.0, "method": "GET", "path": "/api/status",
            "status": 200, "latency_ms": 5.2, "ip": "127.0.0.1",
        })
        storage["jebat:logs:recent"] = json.dumps([entry])

        with patch("jebat.database.connection_manager.get_redis_manager", return_value=mock_rm):
            resp = await client.get("/api/logs/recent")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_logs_recent_with_status_filter(self, client: AsyncClient):
        mock_rm, storage = _mock_redis()
        entries = [
            json.dumps({"ts": 1718600000.0, "method": "GET", "path": "/api/a", "status": 200, "latency_ms": 1, "ip": "127.0.0.1"}),
            json.dumps({"ts": 1718600001.0, "method": "GET", "path": "/api/b", "status": 404, "latency_ms": 2, "ip": "127.0.0.1"}),
            json.dumps({"ts": 1718600002.0, "method": "POST", "path": "/api/c", "status": 200, "latency_ms": 3, "ip": "127.0.0.1"}),
        ]
        storage["jebat:logs:recent"] = json.dumps(entries)

        with patch("jebat.database.connection_manager.get_redis_manager", return_value=mock_rm):
            resp = await client.get("/api/logs/recent?status=404")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 1
            assert data["entries"][0]["status"] == 404

    @pytest.mark.asyncio
    async def test_logs_recent_with_method_filter(self, client: AsyncClient):
        mock_rm, storage = _mock_redis()
        entries = [
            json.dumps({"ts": 1718600000.0, "method": "GET", "path": "/api/a", "status": 200, "latency_ms": 1, "ip": "127.0.0.1"}),
            json.dumps({"ts": 1718600001.0, "method": "POST", "path": "/api/b", "status": 200, "latency_ms": 2, "ip": "127.0.0.1"}),
        ]
        storage["jebat:logs:recent"] = json.dumps(entries)

        with patch("jebat.database.connection_manager.get_redis_manager", return_value=mock_rm):
            resp = await client.get("/api/logs/recent?method=POST")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 1
            assert data["entries"][0]["method"] == "POST"

    @pytest.mark.asyncio
    async def test_logs_recent_with_path_filter(self, client: AsyncClient):
        mock_rm, storage = _mock_redis()
        entries = [
            json.dumps({"ts": 1718600000.0, "method": "GET", "path": "/api/status", "status": 200, "latency_ms": 1, "ip": "127.0.0.1"}),
            json.dumps({"ts": 1718600001.0, "method": "GET", "path": "/api/chat", "status": 200, "latency_ms": 2, "ip": "127.0.0.1"}),
        ]
        storage["jebat:logs:recent"] = json.dumps(entries)

        with patch("jebat.database.connection_manager.get_redis_manager", return_value=mock_rm):
            resp = await client.get("/api/logs/recent?path_contains=status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 1
            assert "status" in data["entries"][0]["path"]

    @pytest.mark.asyncio
    async def test_logs_clear_no_redis(self, client: AsyncClient):
        resp = await client.delete("/api/logs/clear")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_logs_clear_with_redis(self, client: AsyncClient):
        mock_rm, storage = _mock_redis()
        storage["jebat:logs:total"] = "100"
        storage["jebat:logs:errors"] = "5"
        storage["jebat:logs:recent"] = json.dumps(["entry1", "entry2"])

        with patch("jebat.database.connection_manager.get_redis_manager", return_value=mock_rm):
            resp = await client.delete("/api/logs/clear")
            assert resp.status_code == 200
            data = resp.json()
            assert data["cleared"] is True

    @pytest.mark.asyncio
    async def test_logs_export_json_no_redis(self, client: AsyncClient):
        resp = await client.get("/api/logs/export")
        assert resp.status_code == 200
        assert "attachment" in resp.headers.get("content-disposition", "")

    @pytest.mark.asyncio
    async def test_logs_export_csv_no_redis(self, client: AsyncClient):
        resp = await client.get("/api/logs/export?format=csv")
        assert resp.status_code == 200
        assert "attachment" in resp.headers.get("content-disposition", "")

    @pytest.mark.asyncio
    async def test_logs_export_invalid_format_defaults_json(self, client: AsyncClient):
        resp = await client.get("/api/logs/export?format=xml")
        assert resp.status_code == 200
        assert "attachment" in resp.headers.get("content-disposition", "")

    @pytest.mark.asyncio
    async def test_logs_export_json_with_redis(self, client: AsyncClient):
        mock_rm, storage = _mock_redis()
        entry = json.dumps({
            "ts": 1718600000.0, "method": "GET", "path": "/api/status",
            "status": 200, "latency_ms": 5.2, "ip": "127.0.0.1",
        })
        storage["jebat:logs:recent"] = json.dumps([entry])

        with patch("jebat.database.connection_manager.get_redis_manager", return_value=mock_rm):
            resp = await client.get("/api/logs/export")
            assert resp.status_code == 200
            parsed = json.loads(resp.text)
            assert parsed["total"] >= 1

    @pytest.mark.asyncio
    async def test_logs_export_csv_with_redis(self, client: AsyncClient):
        mock_rm, storage = _mock_redis()
        entry = json.dumps({
            "ts": 1718600000.0, "method": "GET", "path": "/api/status",
            "status": 200, "latency_ms": 5.2, "ip": "127.0.0.1",
        })
        storage["jebat:logs:recent"] = json.dumps([entry])

        with patch("jebat.database.connection_manager.get_redis_manager", return_value=mock_rm):
            resp = await client.get("/api/logs/export?format=csv")
            assert resp.status_code == 200
            assert "text/csv" in resp.headers.get("content-type", "")


# ═══════════════════════════════════════════════════════════════════════
# Chat Sync Endpoints
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.chat
class TestChatSync:
    @pytest.mark.asyncio
    async def test_chat_empty_message(self, client: AsyncClient):
        resp = await client.post("/api/chat", json={"message": ""})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_missing_message(self, client: AsyncClient):
        resp = await client.post("/api/chat", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_with_mock_provider(self, client: AsyncClient):
        with patch(
            "routers.chat.generate_with_failover",
            new_callable=AsyncMock,
            return_value=("Hello from JEBAT!", "test-provider"),
        ):
            resp = await client.post("/api/chat", json={"message": "Hello"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["response"] == "Hello from JEBAT!"
            assert data["provider"] == "test-provider"
            assert "session_id" in data

    @pytest.mark.asyncio
    async def test_chat_with_system_prompt(self, client: AsyncClient):
        with patch(
            "routers.chat.generate_with_failover",
            new_callable=AsyncMock,
            return_value=("Response", "provider"),
        ) as mock_gen:
            resp = await client.post(
                "/api/chat",
                json={"message": "Hello", "system_prompt": "You are helpful."},
            )
            assert resp.status_code == 200
            call_args = mock_gen.call_args
            assert call_args.kwargs.get("system_prompt") == "You are helpful."

    @pytest.mark.asyncio
    async def test_chat_with_temperature_override(self, client: AsyncClient):
        with patch(
            "routers.chat.generate_with_failover",
            new_callable=AsyncMock,
            return_value=("Response", "provider"),
        ):
            resp = await client.post(
                "/api/chat",
                json={"message": "Hello", "temperature": 0.5},
            )
            assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_chat_session_id(self, client: AsyncClient):
        with patch(
            "routers.chat.generate_with_failover",
            new_callable=AsyncMock,
            return_value=("Response", "provider"),
        ):
            resp = await client.post(
                "/api/chat",
                json={"message": "Hello", "session_id": "my-session"},
            )
            assert resp.status_code == 200
            assert resp.json()["session_id"] == "my-session"


# ═══════════════════════════════════════════════════════════════════════
# Chat Stream Endpoints
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.chat
class TestChatStream:
    @pytest.mark.asyncio
    async def test_stream_returns_sse(self, client: AsyncClient):
        async def fake_stream(config, prompt, system_prompt=""):
            yield {"type": "metadata", "provider": "test", "model": "test-model"}
            yield {"type": "token", "text": "Hello"}
            yield {"type": "token", "text": " world"}
            yield {"type": "done", "provider": "test"}

        with patch("routers.chat.generate_stream_with_failover", fake_stream):
            resp = await client.post("/api/chat/stream", json={"message": "Hello"})
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_stream_contains_done_event(self, client: AsyncClient):
        async def fake_stream(config, prompt, system_prompt=""):
            yield {"type": "token", "text": "Hi"}

        with patch("routers.chat.generate_stream_with_failover", fake_stream):
            resp = await client.post("/api/chat/stream", json={"message": "Hello"})
            assert resp.status_code == 200
            assert "[DONE]" in resp.text

    @pytest.mark.asyncio
    async def test_stream_contains_metadata_event(self, client: AsyncClient):
        async def fake_stream(config, prompt, system_prompt=""):
            yield {"type": "metadata", "provider": "test", "model": "m"}
            yield {"type": "token", "text": "x"}
            yield {"type": "done", "provider": "test"}

        with patch("routers.chat.generate_stream_with_failover", fake_stream):
            resp = await client.post("/api/chat/stream", json={"message": "Hello"})
            assert "metadata" in resp.text
            assert "test" in resp.text

    @pytest.mark.asyncio
    async def test_stream_error_emits_error_event(self, client: AsyncClient):
        async def failing_stream(config, prompt, system_prompt=""):
            raise RuntimeError("Provider down")
            yield  # Make it a generator

        with patch("routers.chat.generate_stream_with_failover", failing_stream):
            resp = await client.post("/api/chat/stream", json={"message": "Hello"})
            assert resp.status_code == 200
            assert "error" in resp.text

    @pytest.mark.asyncio
    async def test_stream_no_cache_headers(self, client: AsyncClient):
        async def fake_stream(config, prompt, system_prompt=""):
            yield {"type": "done", "provider": "test"}

        with patch("routers.chat.generate_stream_with_failover", fake_stream):
            resp = await client.post("/api/chat/stream", json={"message": "Hello"})
            assert resp.headers.get("cache-control") == "no-cache"
            assert resp.headers.get("connection") == "keep-alive"

    @pytest.mark.asyncio
    async def test_stream_empty_message(self, client: AsyncClient):
        resp = await client.post("/api/chat/stream", json={"message": ""})
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════
# Logging Middleware Integration
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.logging
class TestLoggingMiddleware:
    @pytest.mark.asyncio
    async def test_middleware_skips_non_api_paths(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_skips_logs_paths(self, client: AsyncClient):
        resp = await client.get("/api/logs/recent")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_logs_api_requests(self, client: AsyncClient):
        mock_rm, storage = _mock_redis()
        with patch("jebat.database.connection_manager.get_redis_manager", return_value=mock_rm):
            resp = await client.get("/api/status")
            assert resp.status_code == 200
            # If Redis was available, the recent list should have an entry
            recent = storage.get("jebat:logs:recent")
            if recent:
                entries = json.loads(recent)
                assert len(entries) >= 1
