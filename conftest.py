"""Shared pytest fixtures and configuration for JEBAT test suite.

Provides reusable fixtures for:
- Async HTTP client (httpx AsyncClient against FastAPI)
- Mock Redis with in-memory storage
- Environment variable management
- Middleware state reset

Markers are defined in pyproject.toml [tool.pytest.ini_options].
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Ensure the project root is first on sys.path so the root jebat/ package
# is found before the stale duplicate inside jebat-core/jebat/.
_project_root = str(Path(__file__).resolve().parent)
if _project_root in sys.path:
    sys.path.remove(_project_root)
sys.path.insert(0, _project_root)

try:
    from main import app
except (ImportError, ModuleNotFoundError):
    app = None  # API tests will be skipped if main isn't importable


# ═══════════════════════════════════════════════════════════════════════
# Environment Fixtures
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def _clean_env():
    """Ensure JEBAT env vars are clean for every test."""
    _saved = {}
    for key in ("JEBAT_API_KEY", "JEBAT_API_KEY_ALLOW_QUERY"):
        _saved[key] = os.environ.pop(key, None)
    yield
    for key, val in _saved.items():
        if val is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = val


# ═══════════════════════════════════════════════════════════════════════
# Async HTTP Client
# ═══════════════════════════════════════════════════════════════════════


@pytest_asyncio.fixture
async def client():
    """Async HTTP client wired to the FastAPI app via ASGITransport."""
    if app is None:
        pytest.skip("FastAPI app not importable")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# ═══════════════════════════════════════════════════════════════════════
# Mock Redis
# ═══════════════════════════════════════════════════════════════════════


def make_mock_redis():
    """Create a mock Redis client with in-memory storage.

    Returns (mock_redis_manager, storage_dict) where storage_dict
    is the raw key-value store backing the mock.
    """
    storage: dict = {}

    mock_client = AsyncMock()
    mock_rm = MagicMock()
    mock_rm.client = mock_client

    # --- String operations ---
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

    async def fake_exists(key):
        return key in storage

    # --- Counter operations ---
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

    # --- List operations ---
    async def fake_lpush(key, *values):
        lst = json.loads(storage.get(key, "[]"))
        for v in values:
            lst.insert(0, v)
        storage[key] = json.dumps(lst)
        return len(lst)

    async def fake_ltrim(key, start, stop):
        lst = json.loads(storage.get(key, "[]"))
        storage[key] = json.dumps(lst[start : stop + 1])

    async def fake_llen(key):
        lst = json.loads(storage.get(key, "[]"))
        return len(lst)

    async def fake_lrange(key, start, stop):
        lst = json.loads(storage.get(key, "[]"))
        if stop == -1:
            return lst[start:]
        return lst[start : stop + 1]

    # --- Hash operations ---
    async def fake_hincrby(key, field, amount):
        h = json.loads(storage.get(key, "{}"))
        h[field] = h.get(field, 0) + amount
        storage[key] = json.dumps(h)
        return h[field]

    async def fake_hgetall(key):
        return json.loads(storage.get(key, "{}"))

    # --- Scan ---
    async def fake_scan(cursor=0, match="*", count=100):
        import fnmatch

        matched = [k for k in storage if fnmatch.fnmatch(k, match)]
        return (0, matched)

    # --- Pipeline (returns self for chaining) ---
    mock_client.pipeline.return_value = mock_client

    # Wire up all operations
    mock_client.get = fake_get
    mock_client.set = fake_set
    mock_client.delete = fake_delete
    mock_client.exists = fake_exists
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

    return mock_rm, storage


@pytest.fixture
def mock_redis():
    """Provide a fresh mock Redis instance per test."""
    return make_mock_redis()
