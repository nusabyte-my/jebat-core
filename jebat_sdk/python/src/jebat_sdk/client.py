"""JEBAT SDK — Core Client (Sync + Async)."""

from __future__ import annotations

import asyncio
import contextlib
import json
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Generator, Literal

import httpx
from httpx import AsyncClient, Client as SyncClient

from .config import ClientConfig, RetryConfig, CircuitBreakerConfig, WebSocketConfig, MCPConfig
from .errors import (
    JebatError,
    create_error,
    is_jebat_error,
    is_retryable_error,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError,
    ServerError,
    ForbiddenError,
    TimeoutError,
    ConnectionError,
)
from .models import *  # noqa: F403,F401


class CircuitBreaker:
    """Simple circuit breaker implementation."""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = "closed"  # closed, open, half-open
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self._lock = asyncio.Lock()

    def can_execute(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open":
            if time.time() - self.last_failure_time >= self.config.timeout:
                self.state = "half-open"
                self.success_count = 0
                return True
            return False
        # half-open
        return True

    def record_success(self) -> None:
        if self.state == "half-open":
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = "closed"
                self.failure_count = 0
        elif self.state == "closed":
            self.failure_count = 0

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.state == "half-open":
            self.state = "open"
        elif self.failure_count >= self.config.failure_threshold:
            self.state = "open"


class RequestMiddleware:
    """Request/response middleware chain."""

    def __init__(self):
        self.request_hooks: list[callable] = []
        self.response_hooks: list[callable] = []
        self.error_hooks: list[callable] = []

    def add_request_hook(self, hook: callable) -> None:
        self.request_hooks.append(hook)

    def add_response_hook(self, hook: callable) -> None:
        self.response_hooks.append(hook)

    def add_error_hook(self, hook: callable) -> None:
        self.error_hooks.append(hook)

    async def process_request(self, request: httpx.Request) -> httpx.Request:
        for hook in self.request_hooks:
            if asyncio.iscoroutinefunction(hook):
                request = await hook(request) or request
            else:
                request = hook(request) or request
        return request

    async def process_response(self, response: httpx.Response) -> httpx.Response:
        for hook in self.response_hooks:
            if asyncio.iscoroutinefunction(hook):
                response = await hook(response) or response
            else:
                response = hook(response) or response
        return response

    async def process_error(self, error: Exception) -> Exception:
        for hook in self.error_hooks:
            if asyncio.iscoroutinefunction(hook):
                error = await hook(error) or error
            else:
                error = hook(error) or error
        return error


class _BaseClient:
    """Base class with shared logic for sync/async clients."""

    def __init__(self, config: ClientConfig):
        self.config = config
        self._circuit_breaker = CircuitBreaker(config.circuit_breaker)
        self._middleware = RequestMiddleware()
        self._transport: Literal["http", "websocket", "mcp"] = config.transport

        # HTTP client
        self._sync_client: SyncClient | None = None
        self._async_client: AsyncClient | None = None

        # Request ID generator
        self._request_counter = 0

    def _get_headers(self) -> dict[str, str]:
        headers = {
            "User-Agent": self.config.user_agent,
            "Content-Type": "application/json",
            **self.config.default_headers,
        }
        if self.config.api_key:
            headers[self.config.auth_header] = f"{self.config.auth_scheme} {self.config.api_key}"
        return headers

    def _generate_request_id(self) -> str:
        self._request_counter += 1
        return f"req_{int(time.time() * 1000)}_{self._request_counter}"

    def _build_url(self, path: str) -> str:
        base = self.config.base_url.rstrip("/")
        path = path.lstrip("/")
        return f"{base}/{path}"

    def _handle_response(self, response: httpx.Response) -> Any:
        """Parse and validate response."""
        request_id = response.headers.get("X-Request-ID")

        if response.is_success:
            if response.headers.get("Content-Type", "").startswith("application/json"):
                return response.json()
            return response.text

        # Error handling
        try:
            error_data = response.json()
            message = error_data.get("message", f"HTTP {response.status_code}")
            details = error_data.get("details", {})
        except Exception:
            message = f"HTTP {response.status_code}: {response.text[:200]}"
            details = {}

        raise create_error(
            status_code=response.status_code,
            message=message,
            response_body=response.text,
            request_id=request_id,
            retry_after=error_data.get("retry_after") if "error_data" in locals() else None,
        )

    def _check_circuit_breaker(self) -> None:
        if not self._circuit_breaker.can_execute():
            from .errors import CircuitBreakerOpenError
            raise CircuitBreakerOpenError("Circuit breaker is open")

    def _record_result(self, success: bool) -> None:
        if success:
            self._circuit_breaker.record_success()
        else:
            self._circuit_breaker.record_failure()

    # ─── Sync HTTP Client ────────────────────────────────────────────

    def _get_sync_client(self) -> SyncClient:
        if self._sync_client is None:
            self._sync_client = SyncClient(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(
                    connect=self.config.connect_timeout,
                    read=self.config.timeout,
                    write=self.config.timeout,
                    pool=self.config.timeout,
                ),
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20,
                    keepalive_expiry=15.0,
                ),
                http2=self.config.http2,
                headers=self._get_headers(),
                follow_redirects=True,
            )
        return self._sync_client

    def _get_async_client(self) -> AsyncClient:
        if self._async_client is None:
            self._async_client = AsyncClient(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(
                    connect=self.config.connect_timeout,
                    read=self.config.timeout,
                    write=self.config.timeout,
                    pool=self.config.timeout,
                ),
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20,
                    keepalive_expiry=15.0,
                ),
                http2=self.config.http2,
                headers=self._get_headers(),
                follow_redirects=True,
            )
        return self._async_client

    def _request_sync(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        data: Any = None,
        files: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        stream: bool = False,
    ) -> Any:
        self._check_circuit_breaker()
        client = self._get_sync_client()
        url = self._build_url(path)

        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)

        request_id = self._generate_request_id()
        request_headers["X-Request-ID"] = request_id

        attempt = 0
        last_error = None

        while attempt <= self.config.retry.max_attempts:
            attempt += 1
            try:
                response = client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    data=data,
                    files=files,
                    headers=request_headers,
                    stream=stream,
                )

                if stream:
                    self._record_result(True)
                    return response

                result = self._handle_response(response)
                self._record_result(True)
                return result

            except RateLimitError as e:
                last_error = e
                self._record_result(False)
                if attempt <= self.config.retry.max_attempts:
                    delay = e.retry_after or self.config.retry.get_delay(attempt, 429)
                    time.sleep(delay)
                    continue
                raise

            except (ServerError, TimeoutError, ConnectionError) as e:
                last_error = e
                self._record_result(False)
                if attempt < self.config.retry.max_attempts and is_retryable_error(e):
                    delay = self.config.retry.get_delay(attempt, getattr(e, "status_code", None))
                    time.sleep(delay)
                    continue
                raise

            except JebatError:
                self._record_result(False)
                raise

        raise last_error or JebatError("Max retries exceeded")

    async def _request_async(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        data: Any = None,
        files: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        stream: bool = False,
    ) -> Any:
        self._check_circuit_breaker()
        client = self._get_async_client()
        url = self._build_url(path)

        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)

        request_id = self._generate_request_id()
        request_headers["X-Request-ID"] = request_id

        attempt = 0
        last_error = None

        while attempt <= self.config.retry.max_attempts:
            attempt += 1
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    data=data,
                    files=files,
                    headers=request_headers,
                    stream=stream,
                )

                if stream:
                    self._record_result(True)
                    return response

                result = self._handle_response(response)
                self._record_result(True)
                return result

            except RateLimitError as e:
                last_error = e
                self._record_result(False)
                if attempt <= self.config.retry.max_attempts:
                    delay = e.retry_after or self.config.retry.get_delay(attempt, 429)
                    await asyncio.sleep(delay)
                    continue
                raise

            except (ServerError, TimeoutError, ConnectionError) as e:
                last_error = e
                self._record_result(False)
                if attempt < self.config.retry.max_attempts and is_retryable_error(e):
                    delay = self.config.retry.get_delay(attempt, getattr(e, "status_code", None))
                    await asyncio.sleep(delay)
                    continue
                raise

            except JebatError:
                self._record_result(False)
                raise

        raise last_error or JebatError("Max retries exceeded")

    # ─── Resource Methods ────────────────────────────────────────────

    def _get_sync(self, path: str, params: dict | None = None) -> Any:
        return self._request_sync("GET", path, params=params)

    def _post_sync(self, path: str, json_data: dict | None = None, **kwargs) -> Any:
        return self._request_sync("POST", path, json_data=json_data, **kwargs)

    def _put_sync(self, path: str, json_data: dict | None = None, **kwargs) -> Any:
        return self._request_sync("PUT", path, json_data=json_data, **kwargs)

    def _patch_sync(self, path: str, json_data: dict | None = None, **kwargs) -> Any:
        return self._request_sync("PATCH", path, json_data=json_data, **kwargs)

    def _delete_sync(self, path: str, params: dict | None = None) -> Any:
        return self._request_sync("DELETE", path, params=params)

    async def _get_async(self, path: str, params: dict | None = None) -> Any:
        return await self._request_async("GET", path, params=params)

    async def _post_async(self, path: str, json_data: dict | None = None, **kwargs) -> Any:
        return await self._request_async("POST", path, json_data=json_data, **kwargs)

    async def _put_async(self, path: str, json_data: dict | None = None, **kwargs) -> Any:
        return await self._request_async("PUT", path, json_data=json_data, **kwargs)

    async def _patch_async(self, path: str, json_data: dict | None = None, **kwargs) -> Any:
        return await self._request_async("PATCH", path, json_data=json_data, **kwargs)

    async def _delete_async(self, path: str, params: dict | None = None) -> Any:
        return await self._request_async("DELETE", path, params=params)

    # ─── Streaming ───────────────────────────────────────────────────

    def _stream_sync(self, path: str, json_data: dict | None = None) -> Generator[Any, None, None]:
        self._check_circuit_breaker()
        client = self._get_sync_client()
        url = self._build_url(path)
        headers = self._get_headers()
        headers["X-Request-ID"] = self._generate_request_id()

        with client.stream("POST", url, json=json_data, headers=headers) as response:
            if not response.is_success:
                self._handle_response(response)
            for line in response.iter_lines():
                if line:
                    yield json.loads(line)

    async def _stream_async(self, path: str, json_data: dict | None = None) -> AsyncGenerator[Any, None]:
        self._check_circuit_breaker()
        client = self._get_async_client()
        url = self._build_url(path)
        headers = self._get_headers()
        headers["X-Request-ID"] = self._generate_request_id()

        async with client.stream("POST", url, json=json_data, headers=headers) as response:
            if not response.is_success:
                await self._handle_response(response)
            async for line in response.aiter_lines():
                if line:
                    yield json.loads(line)

    # ─── Cleanup ────────────────────────────────────────────────────

    def close_sync(self) -> None:
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None

    async def close_async(self) -> None:
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None


class JebatClient(_BaseClient):
    """Synchronous JEBAT client."""

    def __init__(self, config: ClientConfig | None = None):
        super().__init__(config or ClientConfig())

    # ─── Context Manager ────────────────────────────────────────────

    def __enter__(self) -> "JebatClient":
        return self

    def __exit__(self, *args) -> None:
        self.close_sync()

    # ─── Core API ───────────────────────────────────────────────────

    def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str = "jebat-core-v8.2",
        mode: str = "deliberate",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        **kwargs,
    ) -> ChatCompleteResponse:
        request = ChatCompleteRequest(
            messages=messages,
            model=model,
            mode=mode,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            **kwargs,
        )
        return self._post_sync("/api/v1/chat", request.model_dump(exclude_none=True))

    def chat_stream(
        self,
        messages: list[ChatMessage],
        *,
        model: str = "jebat-core-v8.2",
        mode: str = "deliberate",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        **kwargs,
    ) -> Generator[ChatStreamChunk, None, None]:
        request = ChatCompleteRequest(
            messages=messages,
            model=model,
            mode=mode,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            stream=True,
            **kwargs,
        )
        for chunk in self._stream_sync("/api/v1/chat", request.model_dump(exclude_none=True)):
            yield ChatStreamChunk(**chunk)

    # ─── Thinking Modes ──────────────────────────────────────────────

    def list_thinking_modes(self) -> list[ThinkingMode]:
        return [m.value for m in ThinkingMode]

    # ─── Memory ──────────────────────────────────────────────────────

    def memory_query(
        self,
        query: str,
        layer: str = "all",
        limit: int = 10,
        min_score: float = 0.7,
        filters: dict | None = None,
    ) -> MemoryQueryResponse:
        request = MemoryQueryRequest(
            query=query,
            layer=layer,
            limit=limit,
            min_score=min_score,
            filters=filters,
        )
        return self._post_sync("/api/v1/memory/query", request.model_dump(exclude_none=True))

    def memory_add(
        self,
        content: str,
        layer: str,
        metadata: dict | None = None,
        ttl_seconds: int | None = None,
    ) -> MemoryAddResponse:
        request = MemoryAddRequest(
            content=content,
            layer=layer,
            metadata=metadata,
            ttl_seconds=ttl_seconds,
        )
        return self._post_sync("/api/v1/memory", request.model_dump(exclude_none=True))

    # ─── Agents ──────────────────────────────────────────────────────

    def agent_create(self, request: AgentCreateRequest) -> AgentCreateResponse:
        return self._post_sync("/api/v1/agents", request.model_dump(exclude_none=True))

    def agent_run(self, agent_id: str, request: AgentRunRequest) -> AgentRunResponse:
        return self._post_sync(f"/api/v1/agents/{agent_id}/run", request.model_dump(exclude_none=True))

    def agent_run_stream(
        self, agent_id: str, request: AgentRunRequest
    ) -> Generator[AgentRunResponse, None, None]:
        for chunk in self._stream_sync(f"/api/v1/agents/{agent_id}/run/stream", request.model_dump()):
            yield AgentRunResponse(**chunk)

    # ─── Tools ───────────────────────────────────────────────────────

    def tool_call(self, name: str, arguments: dict) -> ToolCallResponse:
        return self._post_sync("/api/v1/tools/call", {"name": name, "arguments": arguments})

    def tool_list(self) -> list[ToolDefinition]:
        return self._get_sync("/api/v1/tools")

    # ─── Sentinel ────────────────────────────────────────────────────

    def sentinel_scan(self, request: ScanRequest) -> ScanResponse:
        return self._post_sync("/api/v1/sentinel/scan", request.model_dump(exclude_none=True))

    def sentinel_get_scan(self, scan_id: str) -> ScanResponse:
        return self._get_sync(f"/api/v1/sentinel/scan/{scan_id}")

    def sentinel_wait(
        self, scan_id: str, timeout: int = 300, poll_interval: int = 5
    ) -> ScanReport:
        start = time.time()
        while time.time() - start < timeout:
            scan = self.sentinel_get_scan(scan_id)
            if scan.status in ("completed", "failed", "cancelled"):
                return self.sentinel_get_report(scan_id)
            time.sleep(poll_interval)
        raise TimeoutError(f"Scan {scan_id} timed out after {timeout}s")

    def sentinel_get_report(self, scan_id: str) -> ScanReport:
        return self._get_sync(f"/api/v1/sentinel/scan/{scan_id}/report")

    def sentinel_list_cves(
        self, severity: str | None = None, limit: int = 20
    ) -> list[CVEResult]:
        params = {"limit": limit}
        if severity:
            params["severity"] = severity
        return self._get_sync("/api/v1/sentinel/cves", params)

    # ─── DevSuite ────────────────────────────────────────────────────

    def generate_code(self, request: GenerateRequest) -> GenerateResponse:
        return self._post_sync("/api/v1/dev/generate", request.model_dump(exclude_none=True))

    def review_code(self, request: ReviewRequest) -> ReviewResponse:
        return self._post_sync("/api/v1/dev/review", request.model_dump(exclude_none=True))

    def sandbox_run(self, request: SandboxRunRequest) -> SandboxRunResponse:
        return self._post_sync("/api/v1/dev/sandbox", request.model_dump(exclude_none=True))

    def get_ide_config(self, editor: str, workspace_path: str) -> IDEConfigResponse:
        request = IDEConfigRequest(editor=editor, workspace_path=workspace_path)
        return self._post_sync("/api/v1/dev/ide-config", request.model_dump(exclude_none=True))

    # ─── Companion ───────────────────────────────────────────────────

    def companion_chat(self, request: CompanionChatRequest) -> CompanionChatResponse:
        return self._post_sync("/api/v1/companion/chat", request.model_dump(exclude_none=True))

    def companion_briefing(self, request: BriefingRequest) -> BriefingResponse:
        return self._post_sync("/api/v1/companion/briefing", request.model_dump(exclude_none=True))

    def companion_meeting_summarize(self, request: MeetingSummarizeRequest) -> MeetingSummarizeResponse:
        return self._post_sync("/api/v1/companion/meeting", request.model_dump(exclude_none=True))

    def companion_tasks(self, request: TaskListRequest) -> TaskListResponse:
        return self._get_sync("/api/v1/companion/tasks", request.model_dump(exclude_none=True))

    # ─── Nexus ───────────────────────────────────────────────────────

    def bot_create(self, request: BotCreateRequest) -> BotCreateResponse:
        return self._post_sync("/api/v1/nexus/bots", request.model_dump(exclude_none=True))

    def bot_broadcast(self, request: BroadcastRequest) -> BroadcastResponse:
        return self._post_sync("/api/v1/nexus/broadcast", request.model_dump(exclude_none=True))

    def channel_list(self) -> ChannelListResponse:
        return self._get_sync("/api/v1/nexus/channels")

    # ─── MCP ─────────────────────────────────────────────────────────

    def mcp_tools_call(self, name: str, arguments: dict) -> MCPToolCallResponse:
        return self._post_sync("/api/v1/mcp/tools/call", {"name": name, "arguments": arguments})

    def mcp_tools_list(self) -> MCPToolListResponse:
        return self._get_sync("/api/v1/mcp/tools")

    # ─── Admin ───────────────────────────────────────────────────────

    def health_check(self) -> HealthResponse:
        return self._get_sync("/api/v1/admin/health")

    def api_key_create(self, request: APIKeyCreateRequest) -> APIKeyCreateResponse:
        return self._post_sync("/api/v1/admin/keys", request.model_dump(exclude_none=True))

    def api_key_list(self) -> APIKeyListResponse:
        return self._get_sync("/api/v1/admin/keys")

    # ─── RBAC ────────────────────────────────────────────────────────

    def org_create(self, request: OrgCreateRequest) -> OrgCreateResponse:
        return self._post_sync("/api/v1/admin/orgs", request.model_dump(exclude_none=True))

    def team_create(self, org_id: str, request: TeamCreateRequest) -> TeamCreateResponse:
        return self._post_sync(f"/api/v1/admin/orgs/{org_id}/teams", request.model_dump(exclude_none=True))

    def project_create(
        self, org_id: str, request: ProjectCreateRequest
    ) -> ProjectCreateResponse:
        return self._post_sync(f"/api/v1/admin/orgs/{org_id}/projects", request.model_dump(exclude_none=True))

    def role_assign(self, request: RoleAssignRequest) -> None:
        self._post_sync("/api/v1/admin/roles/assign", request.model_dump(exclude_none=True))

    def audit_list(
        self, org_id: str, limit: int = 100, **filters
    ) -> list[AuditLogEntry]:
        params = {"limit": limit, **filters}
        return self._get_sync(f"/api/v1/admin/orgs/{org_id}/audit", params)

    def service_account_create(self, org_id: str, request: ServiceAccountCreateRequest) -> ServiceAccountCreateResponse:
        return self._post_sync(f"/api/v1/admin/orgs/{org_id}/service-accounts", request.model_dump(exclude_none=True))

    def service_account_key_create(
        self, sa_id: str, request: ServiceAccountKeyCreateRequest
    ) -> ServiceAccountKeyCreateResponse:
        return self._post_sync(f"/api/v1/admin/service-accounts/{sa_id}/keys", request.model_dump(exclude_none=True))

    # ─── MCP Server Management ──────────────────────────────────────

    def mcp_serve(self, config: MCPServerConfig) -> None:
        """Start JEBAT as MCP server (blocks)."""
        import subprocess
        cmd = [config.command] + config.args
        env = {**os.environ, **config.env}
        subprocess.run(cmd, env=env, cwd=config.cwd, check=True)

    # ─── Cleanup ────────────────────────────────────────────────────

    def close(self) -> None:
        self.close_sync()


class AsyncJebatClient(_BaseClient):
    """Asynchronous JEBAT client."""

    def __init__(self, config: ClientConfig | None = None):
        super().__init__(config or ClientConfig())

    async def __aenter__(self) -> "AsyncJebatClient":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close_async()

    # ─── Core API ───────────────────────────────────────────────────

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str = "jebat-core-v8.2",
        mode: str = "deliberate",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        **kwargs,
    ) -> ChatCompleteResponse:
        request = ChatCompleteRequest(
            messages=messages,
            model=model,
            mode=mode,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            **kwargs,
        )
        return await self._post_async("/api/v1/chat", request.model_dump(exclude_none=True))

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        *,
        model: str = "jebat-core-v8.2",
        mode: str = "deliberate",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        **kwargs,
    ) -> AsyncGenerator[ChatStreamChunk, None]:
        request = ChatCompleteRequest(
            messages=messages,
            model=model,
            mode=mode,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            stream=True,
            **kwargs,
        )
        async for chunk in self._stream_async("/api/v1/chat", request.model_dump(exclude_none=True)):
            yield ChatStreamChunk(**chunk)

    # ─── Memory ──────────────────────────────────────────────────────

    async def memory_query(
        self,
        query: str,
        layer: str = "all",
        limit: int = 10,
        min_score: float = 0.7,
        filters: dict | None = None,
    ) -> MemoryQueryResponse:
        request = MemoryQueryRequest(
            query=query,
            layer=layer,
            limit=limit,
            min_score=min_score,
            filters=filters,
        )
        return await self._post_async("/api/v1/memory/query", request.model_dump(exclude_none=True))

    async def memory_add(
        self,
        content: str,
        layer: str,
        metadata: dict | None = None,
        ttl_seconds: int | None = None,
    ) -> MemoryAddResponse:
        request = MemoryAddRequest(
            content=content,
            layer=layer,
            metadata=metadata,
            ttl_seconds=ttl_seconds,
        )
        return await self._post_async("/api/v1/memory", request.model_dump(exclude_none=True))

    # ─── Agents ──────────────────────────────────────────────────────

    async def agent_create(self, request: AgentCreateRequest) -> AgentCreateResponse:
        return await self._post_async("/api/v1/agents", request.model_dump(exclude_none=True))

    async def agent_run(self, agent_id: str, request: AgentRunRequest) -> AgentRunResponse:
        return await self._post_async(f"/api/v1/agents/{agent_id}/run", request.model_dump(exclude_none=True))

    async def agent_run_stream(
        self, agent_id: str, request: AgentRunRequest
    ) -> AsyncGenerator[AgentRunResponse, None]:
        async for chunk in self._stream_async(f"/api/v1/agents/{agent_id}/run/stream", request.model_dump()):
            yield AgentRunResponse(**chunk)

    # ─── Tools ───────────────────────────────────────────────────────

    async def tool_call(self, name: str, arguments: dict) -> ToolCallResponse:
        return await self._post_async("/api/v1/tools/call", {"name": name, "arguments": arguments})

    async def tool_list(self) -> list[ToolDefinition]:
        return await self._get_async("/api/v1/tools")

    # ─── Sentinel ────────────────────────────────────────────────────

    async def sentinel_scan(self, request: ScanRequest) -> ScanResponse:
        return await self._post_async("/api/v1/sentinel/scan", request.model_dump(exclude_none=True))

    async def sentinel_get_scan(self, scan_id: str) -> ScanResponse:
        return await self._get_async(f"/api/v1/sentinel/scan/{scan_id}")

    async def sentinel_wait(
        self, scan_id: str, timeout: int = 300, poll_interval: int = 5
    ) -> ScanReport:
        start = time.time()
        while time.time() - start < timeout:
            scan = await self.sentinel_get_scan(scan_id)
            if scan.status in ("completed", "failed", "cancelled"):
                return await self.sentinel_get_report(scan_id)
            await asyncio.sleep(poll_interval)
        raise TimeoutError(f"Scan {scan_id} timed out after {timeout}s")

    async def sentinel_get_report(self, scan_id: str) -> ScanReport:
        return await self._get_async(f"/api/v1/sentinel/scan/{scan_id}/report")

    async def sentinel_list_cves(
        self, severity: str | None = None, limit: int = 20
    ) -> list[CVEResult]:
        params = {"limit": limit}
        if severity:
            params["severity"] = severity
        return await self._get_async("/api/v1/sentinel/cves", params)

    # ─── DevSuite ────────────────────────────────────────────────────

    async def generate_code(self, request: GenerateRequest) -> GenerateResponse:
        return await self._post_async("/api/v1/dev/generate", request.model_dump(exclude_none=True))

    async def review_code(self, request: ReviewRequest) -> ReviewResponse:
        return await self._post_async("/api/v1/dev/review", request.model_dump(exclude_none=True))

    async def sandbox_run(self, request: SandboxRunRequest) -> SandboxRunResponse:
        return await self._post_async("/api/v1/dev/sandbox", request.model_dump(exclude_none=True))

    async def get_ide_config(self, editor: str, workspace_path: str) -> IDEConfigResponse:
        request = IDEConfigRequest(editor=editor, workspace_path=workspace_path)
        return await self._post_async("/api/v1/dev/ide-config", request.model_dump(exclude_none=True))

    # ─── Companion ───────────────────────────────────────────────────

    async def companion_chat(self, request: CompanionChatRequest) -> CompanionChatResponse:
        return await self._post_async("/api/v1/companion/chat", request.model_dump(exclude_none=True))

    async def companion_briefing(self, request: BriefingRequest) -> BriefingResponse:
        return await self._post_async("/api/v1/companion/briefing", request.model_dump(exclude_none=True))

    async def companion_meeting_summarize(self, request: MeetingSummarizeRequest) -> MeetingSummarizeResponse:
        return await self._post_async("/api/v1/companion/meeting", request.model_dump(exclude_none=True))

    async def companion_tasks(self, request: TaskListRequest) -> TaskListResponse:
        return await self._get_async("/api/v1/companion/tasks", request.model_dump(exclude_none=True))

    # ─── Nexus ───────────────────────────────────────────────────────

    async def bot_create(self, request: BotCreateRequest) -> BotCreateResponse:
        return await self._post_async("/api/v1/nexus/bots", request.model_dump(exclude_none=True))

    async def bot_broadcast(self, request: BroadcastRequest) -> BroadcastResponse:
        return await self._post_async("/api/v1/nexus/broadcast", request.model_dump(exclude_none=True))

    async def channel_list(self) -> ChannelListResponse:
        return await self._get_async("/api/v1/nexus/channels")

    # ─── MCP ─────────────────────────────────────────────────────────

    async def mcp_tools_call(self, name: str, arguments: dict) -> MCPToolCallResponse:
        return await self._post_async("/api/v1/mcp/tools/call", {"name": name, "arguments": arguments})

    async def mcp_tools_list(self) -> MCPToolListResponse:
        return await self._get_async("/api/v1/mcp/tools")

    # ─── Admin ───────────────────────────────────────────────────────

    async def health_check(self) -> HealthResponse:
        return await self._get_async("/api/v1/admin/health")

    async def api_key_create(self, request: APIKeyCreateRequest) -> APIKeyCreateResponse:
        return await self._post_async("/api/v1/admin/keys", request.model_dump(exclude_none=True))

    async def api_key_list(self) -> APIKeyListResponse:
        return await self._get_async("/api/v1/admin/keys")

    # ─── RBAC ────────────────────────────────────────────────────────

    async def org_create(self, request: OrgCreateRequest) -> OrgCreateResponse:
        return await self._post_async("/api/v1/admin/orgs", request.model_dump(exclude_none=True))

    async def team_create(self, org_id: str, request: TeamCreateRequest) -> TeamCreateResponse:
        return await self._post_async(f"/api/v1/admin/orgs/{org_id}/teams", request.model_dump(exclude_none=True))

    async def project_create(
        self, org_id: str, request: ProjectCreateRequest
    ) -> ProjectCreateResponse:
        return await self._post_async(f"/api/v1/admin/orgs/{org_id}/projects", request.model_dump(exclude_none=True))

    async def role_assign(self, request: RoleAssignRequest) -> None:
        await self._post_async("/api/v1/admin/roles/assign", request.model_dump(exclude_none=True))

    async def audit_list(
        self, org_id: str, limit: int = 100, **filters
    ) -> list[AuditLogEntry]:
        params = {"limit": limit, **filters}
        return await self._get_async(f"/api/v1/admin/orgs/{org_id}/audit", params)

    async def service_account_create(
        self, org_id: str, request: ServiceAccountCreateRequest
    ) -> ServiceAccountCreateResponse:
        return await self._post_async(f"/api/v1/admin/orgs/{org_id}/service-accounts", request.model_dump(exclude_none=True))

    async def service_account_key_create(
        self, sa_id: str, request: ServiceAccountKeyCreateRequest
    ) -> ServiceAccountKeyCreateResponse:
        return await self._post_async(f"/api/v1/admin/service-accounts/{sa_id}/keys", request.model_dump(exclude_none=True))

    # ─── Cleanup ────────────────────────────────────────────────────

    async def close(self) -> None:
        await self.close_async()


# ─── Factory Functions ──────────────────────────────────────────────

def create_client(config: ClientConfig | None = None) -> JebatClient:
    """Create synchronous client."""
    return JebatClient(config)


def create_async_client(config: ClientConfig | None = None) -> AsyncJebatClient:
    """Create asynchronous client."""
    return AsyncJebatClient(config)