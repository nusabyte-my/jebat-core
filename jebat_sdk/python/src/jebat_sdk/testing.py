"""JEBAT SDK — Testing Utilities (Mocks)."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from .client import JebatClient, AsyncJebatClient
from .models import *  # noqa: F403,F401


@dataclass
class MockResponse:
    """Pre-configured mock response."""

    method: str
    path: str
    status_code: int = 200
    json_data: Any = None
    text_data: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    delay: float = 0.0


class MockJebatClient:
    """Mock JebatClient for unit testing without network calls."""

    def __init__(self):
        self._responses: dict[str, list[MockResponse]] = {}
        self._call_log: list[dict[str, Any]] = []
        self._default_responses: dict[str, Any] = {}

    def mock_response(
        self,
        method: str,
        path: str,
        *,
        status_code: int = 200,
        json_data: Any = None,
        text_data: str | None = None,
        headers: dict[str, str] | None = None,
        delay: float = 0.0,
    ) -> "MockJebatClient":
        """Register a mock response for a specific endpoint."""
        key = f"{method}:{path}"
        if key not in self._responses:
            self._responses[key] = []
        self._responses[key].append(MockResponse(
            method=method,
            path=path,
            status_code=status_code,
            json_data=json_data,
            text_data=text_data,
            headers=headers or {},
            delay=delay,
        ))
        return self

    def mock_chat_complete(
        self,
        content: str = "Hello!",
        usage: dict[str, int] | None = None,
    ) -> "MockJebatClient":
        """Mock chat completion endpoint."""
        return self.mock_response(
            "POST",
            "/api/v1/chat",
            json_data={
                "id": "chat_123",
                "object": "chat.completion",
                "created": 1234567890,
                "model": "jebat-core-v8.2",
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }],
                "usage": usage or {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            }
        )

    def mock_chat_stream(
        self,
        chunks: list[str] | None = None,
    ) -> "MockJebatClient":
        """Mock streaming chat endpoint."""
        chunks = chunks or ["Hello", " ", "world", "!"]
        stream_data = []
        for i, chunk in enumerate(chunks):
            stream_data.append({
                "id": f"chat_123_{i}",
                "object": "chat.completion.chunk",
                "created": 1234567890,
                "model": "jebat-core-v8.2",
                "choices": [{
                    "index": 0,
                    "delta": {"content": chunk},
                    "finish_reason": None if i < len(chunks) - 1 else "stop",
                }],
            })
        return self.mock_response(
            "POST",
            "/api/v1/chat",
            status_code=200,
            text_data="\n".join(json.dumps(d) for d in stream_data),
            headers={"Content-Type": "application/x-ndjson"},
        )

    def mock_memory_query(
        self,
        results: list[dict] | None = None,
    ) -> "MockJebatClient":
        results = results or [{
            "id": "doc_1",
            "text": "Test document",
            "score": 0.95,
            "layer": "M2",
            "metadata": {"source": "test"},
        }]
        return self.mock_response(
            "POST",
            "/api/v1/memory/query",
            json_data={
                "results": results,
                "total": len(results),
                "query_time_ms": 1.5,
            }
        )

    def mock_memory_add(self, doc_id: str = "doc_123") -> "MockJebatClient":
        return self.mock_response(
            "POST",
            "/api/v1/memory",
            json_data={"id": doc_id, "layer": "M2", "created_at": "2026-07-11T10:00:00Z"},
        )

    def mock_agent_create(self, agent_id: str = "agent_123") -> "MockJebatClient":
        return self.mock_response(
            "POST",
            "/api/v1/agents",
            json_data={"id": agent_id, "name": "test-agent", "status": "pending", "created_at": "2026-07-11T10:00:00Z"},
        )

    def mock_agent_run(
        self,
        output: str = "Task completed",
        status: str = "completed",
    ) -> "MockJebatClient":
        return self.mock_response(
            "POST",
            "/api/v1/agents/agent_123/run",
            json_data={
                "run_id": "run_123",
                "agent_id": "agent_123",
                "status": status,
                "output": output,
                "steps": [{"step": 1, "action": "think", "result": output}],
                "started_at": "2026-07-11T10:00:00Z",
                "completed_at": "2026-07-11T10:01:00Z",
                "usage": {"prompt_tokens": 100, "completion_tokens": 50},
            }
        )

    def mock_tool_call(self, result: Any = "OK") -> "MockJebatClient":
        return self.mock_response(
            "POST",
            "/api/v1/tools/call",
            json_data={"result": result, "error": None, "is_error": False},
        )

    def mock_sentinel_scan(self, scan_id: str = "scan_123") -> "MockJebatClient":
        return self.mock_response(
            "POST",
            "/api/v1/sentinel/scan",
            json_data={"scan_id": "scan_123", "status": "queued", "target": "test.com", "profile": "standard"},
        )

    def mock_sentinel_status(
        self,
        scan_id: str,
        status: str = "completed",
    ) -> "MockJebatClient":
        return self.mock_response(
            "GET",
            f"/api/v1/sentinel/scan/{scan_id}",
            json_data={"scan_id": scan_id, "status": status, "target": "test.com"},
        )

    def mock_health(self, status: str = "healthy") -> "MockJebatClient":
        return self.mock_response(
            "GET",
            "/api/v1/admin/health",
            json_data={"status": status, "version": "1.0.0", "uptime_seconds": 3600},
        )

    def get_call_log(self) -> list[dict[str, Any]]:
        """Get log of all API calls made."""
        return self._call_log

    def reset(self) -> None:
        """Reset mock state."""
        self._responses.clear()
        self._call_log.clear()

    # ─── Sync Interface ────────────────────────────────────────────

    def _request_sync(
        self, method: str, path: str, **kwargs
    ) -> Any:
        self._call_log.append({"method": method, "path": path, "kwargs": kwargs, "async": False})

        key = f"{method}:{path}"
        if key in self._responses and self._responses[key]:
            response = self._responses[key].pop(0)
            if response.delay:
                import time
                time.sleep(response.delay)

            if response.status_code >= 400:
                from .errors import create_error_from_response
                raise create_error_from_response(
                    status_code=response.status_code,
                    response_body=response.text_data or "",
                )

            if response.json_data is not None:
                return response.json_data
            return response.text_data

        # Return default for unmocked endpoints
        return {"mock": True, "path": path}

    def _stream_sync(self, path: str, **kwargs) -> Generator[Any, None, None]:
        yield {"mock": "stream", "path": path}

    def _get_sync(self, path: str, params: dict | None = None) -> Any:
        return self._request_sync("GET", path, params=params)

    def _post_sync(self, path: str, json_data: dict | None = None, **kwargs) -> Any:
        return self._request_sync("POST", path, json_data=json_data, **kwargs)

    def _put_sync(self, path: str, json_data: dict | None = None, **kwargs) -> Any:
        return self._request_sync("PUT", path, json_data=json_data, **kwargs)

    def _delete_sync(self, path: str, params: dict | None = None) -> Any:
        return self._request_sync("DELETE", path, params=params)

    def _stream_sync(self, path: str, **kwargs) -> Generator[Any, None, None]:
        yield {"mock": "stream", "path": path}

    # ─── Async Interface ──────────────────────────────────────────

    async def _request_async(self, method: str, path: str, **kwargs) -> Any:
        return self._request_sync(method, path, **kwargs)

    async def _stream_async(self, path: str, **kwargs) -> AsyncGenerator[Any, None]:
        yield {"mock": "async_stream", "path": path}

    async def _get_async(self, path: str, params: dict | None = None) -> Any:
        return self._request_sync("GET", path, params=params)

    async def _post_async(self, path: str, json_data: dict | None = None, **kwargs) -> Any:
        return self._request_sync("POST", path, json_data=json_data)

    async def _put_async(self, path: str, json_data: dict | None = None, **kwargs) -> Any:
        return self._request_sync("PUT", path, json_data=json_data)

    async def _delete_async(self, path: str, params: dict | None = None) -> Any:
        return self._request_sync("DELETE", path, params=params)

    # ─── Sync/Async Client Compatibility ──────────────────────────

    def close(self) -> None:
        pass

    async def close(self) -> None:
        pass

    def __enter__(self) -> "MockJebatClient":
        return self

    def __exit__(self, *args) -> None:
        pass

    async def __aenter__(self) -> "MockJebatClient":
        return self

    async def __aexit__(self, *args) -> None:
        pass

    # ─── Delegate to real client methods ──────────────────────────

    def __getattr__(self, name: str) -> Any:
        # Delegate to real client for actual implementation
        # In tests, you typically only mock the HTTP layer
        real_client = JebatClient()
        return getattr(real_client, name)


# ─── Convenience Functions ────────────────────────────────────────

def mock_chat_response(content: str = "Hello!") -> MockJebatClient:
    """Quick mock for chat completion."""
    client = MockJebatClient()
    return client.mock_chat_complete(content)


def mock_stream_response(chunks: list[str]) -> MockJebatClient:
    """Quick mock for streaming chat."""
    client = MockJebatClient()
    return client.mock_chat_stream(chunks)


def mock_memory(results: list[dict]) -> MockJebatClient:
    """Quick mock for memory query."""
    client = MockJebatClient()
    return client.mock_memory_query(results)


def mock_sentinel_scan(scan_id: str = "scan_123") -> MockJebatClient:
    """Quick mock for sentinel scan."""
    client = MockJebatClient()
    return client.mock_sentinel_scan(scan_id)


# ─── Context Managers for Test Fixtures ──────────────────────────

@contextmanager
def mock_client(**mock_configs) -> Generator[MockJebatClient, None, None]:
    """Context manager for mocked client."""
    client = MockJebatClient()
    for method, path, response in mock_configs.get("responses", []):
        client.mock_response(method, path, **response)
    yield client


@asynccontextmanager
async def async_mock_client(**mock_configs) -> AsyncGenerator[MockJebatClient, None]:
    """Async context manager for mocked client."""
    client = MockJebatClient()
    for method, path, response in mock_configs.get("responses", []):
        client.mock_response(method, path, **response)
    yield client


# ─── Pytest Fixtures ─────────────────────────────────────────────

import pytest


@pytest.fixture
def mock_jebat_client() -> MockJebatClient:
    """Pytest fixture for mocked client."""
    return MockJebatClient()


@pytest.fixture
def mock_chat(mock_jebat_client: MockJebatClient) -> MockJebatClient:
    """Fixture with chat mocked."""
    return mock_jebat_client.mock_chat_complete("Test response")


@pytest.fixture
def mock_stream(mock_jebat_client: MockJebatClient) -> MockJebatClient:
    """Fixture with streaming mocked."""
    return mock_jebat_client.mock_chat_stream(["Hello", " ", "World", "!"])


@pytest.fixture
def mock_memory(mock_jebat_client: MockJebatClient) -> MockJebatClient:
    """Fixture with memory mocked."""
    return mock_jebat_client.mock_memory_query([
        {"id": "doc_1", "text": "Test doc", "score": 0.9, "layer": "M2", "metadata": {}}
    ])


# ─── Async Mock Client ──────────────────────────────────────────

class AsyncMockJebatClient(MockJebatClient):
    """Async mock client with async-compatible methods."""

    async def _request_async(self, method: str, path: str, **kwargs) -> Any:
        return self._request_sync(method, path, **kwargs)

    async def _stream_async(self, path: str, **kwargs) -> AsyncGenerator[Any, None]:
        for item in self._stream_sync(path):
            yield item


def create_mock_client() -> MockJebatClient:
    """Factory for creating a pre-configured mock client."""
    client = MockJebatClient()
    client.mock_health()
    client.mock_chat_complete()
    client.mock_memory_query()
    return client


def create_async_mock_client() -> AsyncMockJebatClient:
    """Factory for async mock client."""
    client = AsyncMockJebatClient()
    client.mock_health()
    client.mock_chat_complete()
    client.mock_memory_query()
    return client