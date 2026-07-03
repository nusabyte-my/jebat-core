"""
Asynchronous JEBAT API Client.

Provides async interface to the JEBAT REST API with full streaming support.
"""

import asyncio
import json
from typing import Optional, Dict, Any, List, Union, AsyncIterator
from contextlib import asynccontextmanager

import httpx
from pydantic import BaseModel

from .models import *
from .exceptions import (
    JebatError,
    map_http_error,
    AuthenticationError,
    RateLimitError,
    ServerError,
)
from .retry import standard_retry, is_retryable_exception


class AsyncJebatClient:
    """
    Asynchronous JEBAT API client with full streaming support.

    Usage:
        async with AsyncJebatClient(base_url="http://localhost:8000") as client:
            await client.login("username", "password")
            async for chunk in client.chat_stream("Hello!"):
                print(chunk.content, end="", flush=True)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
        max_retries: int = 3,
        limits: Optional[httpx.Limits] = None,
    ):
        """
        Initialize async client.

        Args:
            base_url: API base URL
            timeout: Request timeout in seconds
            headers: Default headers
            max_retries: Maximum retry attempts
            limits: HTTPX limits for connection pooling
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if headers:
            default_headers.update(headers)

        if limits is None:
            limits = httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
                keepalive_expiry=30.0,
            )

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers=default_headers,
            limits=limits,
        )

        self._token: Optional[str] = None
        self._refresh_token: Optional[str] = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    @property
    def token(self) -> Optional[str]:
        return self._token

    @property
    def refresh_token(self) -> Optional[str]:
        return self._refresh_token

    def set_token(self, access_token: str, refresh_token: Optional[str] = None) -> None:
        """Set authentication tokens."""
        self._token = access_token
        if refresh_token:
            self._refresh_token = refresh_token
        self._client.headers["Authorization"] = f"Bearer {access_token}"

    def clear_tokens(self) -> None:
        """Clear authentication tokens."""
        self._token = None
        self._refresh_token = None
        self._client.headers.pop("Authorization", None)

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retries: Optional[int] = None,
        stream: bool = False,
    ) -> Union[httpx.Response, httpx.Response]:
        """Make HTTP request with retry logic."""
        url = f"/api/v1{path}" if not path.startswith("/api/v1") else path
        retries = retries if retries is not None else self.max_retries

        @standard_retry
        async def _do_request():
            response = await self._client.request(
                method=method,
                url=url,
                json=json,
                params=params,
                headers=headers,
                stream=stream,
            )

            # Handle rate limit
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "60")
                raise RateLimitError(
                    "Rate limit exceeded",
                    status_code=429,
                    retry_after=int(retry_after),
                )

            # Handle other errors
            if response.status_code >= 400:
                error_data = None
                try:
                    error_data = response.json()
                except Exception:
                    error_data = {"detail": response.text or f"HTTP {response.status_code}"}

                error = map_http_error(
                    response.status_code,
                    error_data.get("detail", f"HTTP {response.status_code}"),
                    error_data,
                )
                raise error

            return response

        return await _do_request()

    async def _get(self, path: str, **kwargs) -> Dict[str, Any]:
        response = await self._request("GET", path, **kwargs)
        return response.json()

    async def _post(self, path: str, **kwargs) -> Dict[str, Any]:
        response = await self._request("POST", path, **kwargs)
        return response.json()

    async def _put(self, path: str, **kwargs) -> Dict[str, Any]:
        response = await self._request("PUT", path, **kwargs)
        return response.json()

    async def _delete(self, path: str, **kwargs) -> Dict[str, Any]:
        response = await self._request("DELETE", path, **kwargs)
        if response.status_code == 204:
            return {}
        return response.json()

    # ==================== Authentication ====================

    async def login(self, username: str, password: str) -> TokenResponse:
        """
        Authenticate user and get tokens.

        Args:
            username: Username
            password: Password

        Returns:
            TokenResponse with access_token and refresh_token
        """
        data = await self._post("/auth/login", json={"username": username, "password": password})
        token_response = TokenResponse(**data)
        self.set_token(token_response.access_token, token_response.refresh_token)
        return token_response

    async def refresh_token(self, refresh_token: Optional[str] = None) -> TokenResponse:
        """
        Refresh access token.

        Args:
            refresh_token: Refresh token (uses stored if not provided)

        Returns:
            New TokenResponse
        """
        token = refresh_token or self._refresh_token
        if not token:
            raise AuthenticationError("No refresh token available")

        data = await self._post("/auth/refresh", json={"refresh_token": token})
        token_response = TokenResponse(**data)
        self.set_token(token_response.access_token, token_response.refresh_token)
        return token_response

    async def logout(self, refresh_token: Optional[str] = None) -> Dict[str, str]:
        """
        Logout by revoking refresh token.

        Args:
            refresh_token: Refresh token to revoke (uses stored if not provided)

        Returns:
            Success message
        """
        token = refresh_token or self._refresh_token
        if token:
            await self._post("/auth/logout", json={"refresh_token": token})
        self.clear_tokens()
        return {"message": "Logged out"}

    # ==================== API Keys ====================

    async def create_api_key(self, name: str, expires_in_days: Optional[int] = None) -> APIKeyResponse:
        """
        Create a new API key.

        Args:
            name: Key name
            expires_in_days: Optional expiry in days

        Returns:
            APIKeyResponse with full key (only returned once)
        """
        data = await self._post("/auth/api-keys", json={
            "name": name,
            "expires_in_days": expires_in_days,
        })
        return APIKeyResponse(**data)

    async def list_api_keys(self) -> List[APIKeyResponse]:
        """List all API keys for current user."""
        data = await self._get("/auth/api-keys")
        return [APIKeyResponse(**item) for item in data]

    async def revoke_api_key(self, prefix: str) -> Dict[str, str]:
        """
        Revoke an API key by prefix.

        Args:
            prefix: API key prefix (e.g., jebat_abc123)
        """
        await self._delete(f"/auth/api-keys/{prefix}")
        return {"message": "API key revoked"}

    # ==================== User Profile ====================

    async def get_profile(self) -> UserResponse:
        """Get current user profile."""
        data = await self._get("/auth/me")
        return UserResponse(**data)

    async def get_user(self, user_id: str) -> UserResponse:
        """Get user by ID (admin only)."""
        data = await self._get(f"/auth/users/{user_id}")
        return UserResponse(**data)

    # ==================== Chat ====================

    async def chat(
        self,
        message: str,
        user_id: Optional[str] = None,
        mode: str = "deliberate",
        timeout: int = 30,
    ) -> ChatResponse:
        """
        Send a chat message (blocking).

        Args:
            message: User message
            user_id: User ID (uses current user if not provided)
            mode: Thinking mode (fast, deliberate, deep, strategic, creative, critical)
            timeout: Request timeout in seconds

        Returns:
            ChatResponse
        """
        data = await self._post("/chat", json={
            "message": message,
            "user_id": user_id,
            "mode": mode,
            "timeout": timeout,
        })
        return ChatResponse(**data)

    async def chat_stream(
        self,
        message: str,
        user_id: Optional[str] = None,
        mode: str = "deliberate",
        timeout: int = 30,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream chat response via Server-Sent Events.

        Args:
            message: User message
            user_id: User ID
            mode: Thinking mode
            timeout: Request timeout

        Yields:
            StreamChunk objects
        """
        url = f"{self.base_url}/api/v1/chat"
        payload = {
            "message": message,
            "user_id": user_id,
            "mode": mode,
            "timeout": timeout,
            "stream": True,
        }

        async with self._client.stream("POST", url, json=payload, timeout=timeout) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        yield StreamChunk(
                            type="content",
                            content=data,
                        )
                    except Exception as e:
                        yield StreamChunk(type="error", content=str(e))

    async def chat_websocket(
        self,
        message: str,
        mode: str = "deliberate",
        user_id: Optional[str] = None,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream chat via WebSocket (requires separate WebSocket connection).

        Args:
            message: User message
            mode: Thinking mode
            user_id: User ID

        Yields:
            StreamChunk objects
        """
        from .websocket import JebatWebSocketClient

        ws_url = self.base_url.replace("http", "ws") + "/ws/chat"
        async with JebatWebSocketClient(ws_url, self._token) as ws:
            await ws.send_chat(message, mode)
            async for chunk in ws.stream({"message": message, "mode": mode}):
                yield chunk

    # ==================== Memories ====================

    async def list_memories(
        self,
        user_id: Optional[str] = None,
        query: Optional[str] = None,
        layer: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> MemoryListResponse:
        """List memories with optional filtering."""
        params = {"limit": limit, "offset": offset}
        if user_id:
            params["user_id"] = user_id
        if query:
            params["query"] = query
        if layer:
            params["layer"] = layer

        data = await self._get("/memories", params=params)
        return MemoryListResponse(**data)

    async def create_memory(
        self,
        content: str,
        user_id: str,
        layer: str = "M1_EPISODIC",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryItem:
        """Create a new memory."""
        data = await self._post("/memories", json={
            "content": content,
            "user_id": user_id,
            "layer": layer,
            "metadata": metadata,
        })
        return MemoryItem(**data)

    async def search_memories(
        self,
        query: str,
        user_id: Optional[str] = None,
        layer: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> MemoryListResponse:
        """Search memories."""
        params = {"query": query, "limit": limit, "offset": offset}
        if user_id:
            params["user_id"] = user_id
        if layer:
            params["layer"] = layer

        data = await self._get("/memories", params=params)
        return MemoryListResponse(**data)

    # ==================== Agents ====================

    async def list_agents(self) -> AgentListResponse:
        """List all agents."""
        data = await self._get("/agents")
        return AgentListResponse(**data)

    async def get_agent(self, agent_id: str) -> AgentInfo:
        """Get agent by ID."""
        data = await self._get(f"/agents/{agent_id}")
        return AgentInfo(**data)

    async def execute_agent(
        self,
        task: str,
        agent_id: Optional[str] = None,
        mode: str = "deliberate",
        timeout: int = 30,
    ) -> AgentExecuteResponse:
        """Execute an agent task."""
        data = await self._post("/agents/execute", json={
            "task": task,
            "agent_id": agent_id,
            "mode": mode,
            "timeout": timeout,
        })
        return AgentExecuteResponse(**data)

    # ==================== Channels ====================

    async def list_channels(self) -> List[ChannelInfo]:
        """List all channel configurations."""
        data = await self._get("/channels")
        return [ChannelInfo(**item) for item in data]

    async def get_channel(self, channel_id: str) -> ChannelInfo:
        """Get channel by ID."""
        data = await self._get(f"/channels/{channel_id}")
        return ChannelInfo(**data)

    async def update_channel_config(
        self,
        channel_id: str,
        config: Dict[str, Any],
    ) -> ChannelInfo:
        """Update channel configuration."""
        data = await self._put(f"/channels/{channel_id}", json={"config": config})
        return ChannelInfo(**data)

    async def connect_channel(self, channel_id: str) -> Dict[str, str]:
        """Connect a channel."""
        data = await self._post(f"/channels/{channel_id}/connect")
        return data

    async def disconnect_channel(self, channel_id: str) -> Dict[str, str]:
        """Disconnect a channel."""
        data = await self._post(f"/channels/{channel_id}/disconnect")
        return data

    # ==================== Monitoring ====================

    async def get_health(self) -> HealthResponse:
        """Get system health."""
        data = await self._get("/health")
        return HealthResponse(**data)

    async def get_status(self) -> StatusResponse:
        """Get system status."""
        data = await self._get("/status")
        return StatusResponse(**data)

    async def get_metrics(self) -> MetricsResponse:
        """Get system metrics."""
        data = await self._get("/metrics")
        return MetricsResponse(**data)

    # ==================== Swarm ====================

    async def execute_swarm(
        self,
        description: str,
        user_id: Optional[str] = None,
        execution_mode: str = "consensus",
        required_capabilities: Optional[List[str]] = None,
        enable_search: bool = True,
        search_queries: Optional[List[str]] = None,
        max_agents: int = 5,
    ) -> SwarmTaskResponse:
        """Execute a task through the swarm orchestrator."""
        data = await self._post("/swarm/execute", json={
            "description": description,
            "user_id": user_id,
            "execution_mode": execution_mode,
            "required_capabilities": required_capabilities,
            "enable_search": enable_search,
            "search_queries": search_queries,
            "max_agents": max_agents,
        })
        return SwarmTaskResponse(**data)

    async def plan_swarm(
        self,
        description: str,
        execution_mode: str = "consensus",
        required_capabilities: Optional[List[str]] = None,
        max_agents: int = 5,
    ) -> SwarmPlanResponse:
        """Get swarm execution plan without executing."""
        data = await self._post("/swarm/plan", json={
            "description": description,
            "execution_mode": execution_mode,
            "required_capabilities": required_capabilities,
            "max_agents": max_agents,
        })
        return SwarmPlanResponse(**data)

    # ==================== Context Manager ====================

    @asynccontextmanager
    async def session(self):
        """Context manager for temporary session overrides."""
        old_token = self._token
        old_refresh = self._refresh_token
        try:
            yield self
        finally:
            self._token = old_token
            self._refresh_token = old_refresh
            if old_token:
                self._client.headers["Authorization"] = f"Bearer {old_token}"
            else:
                self._client.headers.pop("Authorization", None)