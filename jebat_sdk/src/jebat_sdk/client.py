"""
Synchronous JEBAT API Client.

Provides a clean interface to the JEBAT REST API.
"""

import time
from typing import Optional, Dict, Any, List, Union, Iterator
from contextlib import contextmanager

import httpx
from pydantic import BaseModel

from .models import *
from .exceptions import (
    JebatError,
    map_http_error,
    AuthenticationError,
    RateLimitError,
)
from .retry import standard_retry, is_retryable_exception


class JebatClient:
    """
    Synchronous JEBAT API client.

    Usage:
        client = JebatClient(base_url="http://localhost:8000")
        token = client.login("username", "password")
        client.set_token(token)
        response = client.chat("Hello, JEBAT!")
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
        max_retries: int = 3,
    ):
        """
        Initialize client.

        Args:
            base_url: API base URL (e.g., http://localhost:8000)
            timeout: Request timeout in seconds
            headers: Default headers
            max_retries: Maximum retry attempts
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

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers=default_headers,
        )

        self._token: Optional[str] = None
        self._refresh_token: Optional[str] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

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

    def close(self) -> None:
        """Close HTTP client."""
        self._client.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retries: Optional[int] = None,
    ) -> httpx.Response:
        """Make HTTP request with retry logic."""
        url = f"/api/v1{path}" if not path.startswith("/api/v1") else path
        retries = retries if retries is not None else self.max_retries

        @standard_retry
        def _do_request():
            response = self._client.request(
                method=method,
                url=url,
                json=json,
                params=params,
                headers=headers,
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
                    error_data = {"detail": response.text}

                error = map_http_error(
                    response.status_code,
                    error_data.get("detail", f"HTTP {response.status_code}"),
                    error_data,
                )
                raise error

            return response

        return _do_request()

    def _get(self, path: str, **kwargs) -> Dict[str, Any]:
        response = self._request("GET", path, **kwargs)
        return response.json()

    def _post(self, path: str, **kwargs) -> Dict[str, Any]:
        response = self._request("POST", path, **kwargs)
        return response.json()

    def _put(self, path: str, **kwargs) -> Dict[str, Any]:
        response = self._request("PUT", path, **kwargs)
        return response.json()

    def _delete(self, path: str, **kwargs) -> Dict[str, Any]:
        response = self._request("DELETE", path, **kwargs)
        if response.status_code == 204:
            return {}
        return response.json()

    # ==================== Authentication ====================

    def login(self, username: str, password: str) -> TokenResponse:
        """
        Authenticate user and get tokens.

        Args:
            username: Username
            password: Password

        Returns:
            TokenResponse with access_token and refresh_token
        """
        data = self._post("/auth/login", json={"username": username, "password": password})
        token_response = TokenResponse(**data)
        self.set_token(token_response.access_token, token_response.refresh_token)
        return token_response

    def refresh_token(self, refresh_token: Optional[str] = None) -> TokenResponse:
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

        data = self._post("/auth/refresh", json={"refresh_token": token})
        token_response = TokenResponse(**data)
        self.set_token(token_response.access_token, token_response.refresh_token)
        return token_response

    def logout(self, refresh_token: Optional[str] = None) -> Dict[str, str]:
        """
        Logout by revoking refresh token.

        Args:
            refresh_token: Refresh token to revoke (uses stored if not provided)

        Returns:
            Success message
        """
        token = refresh_token or self._refresh_token
        if token:
            self._post("/auth/logout", json={"refresh_token": token})
        self.clear_tokens()
        return {"message": "Logged out"}

    # ==================== API Keys ====================

    def create_api_key(self, name: str, expires_in_days: Optional[int] = None) -> APIKeyResponse:
        """
        Create a new API key.

        Args:
            name: Key name
            expires_in_days: Optional expiry in days

        Returns:
            APIKeyResponse with full key (only returned once)
        """
        data = self._post("/auth/api-keys", json={
            "name": name,
            "expires_in_days": expires_in_days,
        })
        return APIKeyResponse(**data)

    def list_api_keys(self) -> List[APIKeyResponse]:
        """List all API keys for current user."""
        data = self._get("/auth/api-keys")
        return [APIKeyResponse(**item) for item in data]

    def revoke_api_key(self, prefix: str) -> Dict[str, str]:
        """
        Revoke an API key by prefix.

        Args:
            prefix: API key prefix (e.g., jebat_abc123)
        """
        self._delete(f"/auth/api-keys/{prefix}")
        return {"message": "API key revoked"}

    # ==================== User Profile ====================

    def get_profile(self) -> UserResponse:
        """Get current user profile."""
        data = self._get("/auth/me")
        return UserResponse(**data)

    def get_user(self, user_id: str) -> UserResponse:
        """Get user by ID (admin only)."""
        data = self._get(f"/auth/users/{user_id}")
        return UserResponse(**data)

    # ==================== Chat ====================

    def chat(
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
        data = self._post("/chat", json={
            "message": message,
            "user_id": user_id,
            "mode": mode,
            "timeout": timeout,
        })
        return ChatResponse(**data)

    def chat_stream(
        self,
        message: str,
        user_id: Optional[str] = None,
        mode: str = "deliberate",
        timeout: int = 30,
    ) -> Iterator[StreamChunk]:
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
        import httpx
        import json

        url = f"{self.base_url}/api/v1/chat/stream"
        payload = {
            "message": message,
            "user_id": user_id,
            "mode": mode,
            "timeout": timeout,
            "stream": True,
        }

        with self._client.stream("POST", url, json=payload, timeout=timeout) as response:
            for response in self._handle_sse(response):
                yield response

    def _handle_sse(self, response: httpx.Response) -> Iterator[StreamChunk]:
        """Parse SSE response."""
        for line in response.iter_lines():
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

    # ==================== Memories ====================

    def list_memories(
        self,
        user_id: Optional[str] = None,
        query: Optional[str] = None,
        layer: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> MemoryListResponse:
        """
        List memories with optional filtering.

        Args:
            user_id: Filter by user
            query: Search query
            layer: Memory layer filter
            limit: Max results
            offset: Pagination offset
        """
        params = {"limit": limit, "offset": offset}
        if user_id:
            params["user_id"] = user_id
        if query:
            params["query"] = query
        if layer:
            params["layer"] = layer

        data = self._get("/memories", params=params)
        return MemoryListResponse(**data)

    def create_memory(
        self,
        content: str,
        user_id: str,
        layer: str = "M1_EPISODIC",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryItem:
        """
        Create a new memory.

        Args:
            content: Memory content
            user_id: User ID
            layer: Memory layer
            metadata: Optional metadata
        """
        data = self._post("/memories", json={
            "content": content,
            "user_id": user_id,
            "layer": layer,
            "metadata": metadata,
        })
        return MemoryItem(**data)

    def search_memories(
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

        data = self._get("/memories", params=params)
        return MemoryListResponse(**data)

    # ==================== Agents ====================

    def list_agents(self) -> AgentListResponse:
        """List all agents."""
        data = self._get("/agents")
        return AgentListResponse(**data)

    def get_agent(self, agent_id: str) -> AgentInfo:
        """Get agent by ID."""
        data = self._get(f"/agents/{agent_id}")
        return AgentInfo(**data)

    def execute_agent(
        self,
        task: str,
        agent_id: Optional[str] = None,
        mode: str = "deliberate",
        timeout: int = 30,
    ) -> AgentExecuteResponse:
        """
        Execute an agent task.

        Args:
            task: Task description
            agent_id: Optional specific agent
            mode: Execution mode
            timeout: Timeout in seconds
        """
        data = self._post("/agents/execute", json={
            "task": task,
            "agent_id": agent_id,
            "mode": mode,
            "timeout": timeout,
        })
        return AgentExecuteResponse(**data)

    # ==================== Channels ====================

    def list_channels(self) -> List[ChannelInfo]:
        """List all channel configurations."""
        data = self._get("/channels")
        return [ChannelInfo(**item) for item in data]

    def get_channel(self, channel_id: str) -> ChannelInfo:
        """Get channel by ID."""
        data = self._get(f"/channels/{channel_id}")
        return ChannelInfo(**data)

    def update_channel_config(
        self,
        channel_id: str,
        config: Dict[str, Any],
    ) -> ChannelInfo:
        """Update channel configuration."""
        data = self._put(f"/channels/{channel_id}", json={"config": config})
        return ChannelInfo(**data)

    def connect_channel(self, channel_id: str) -> Dict[str, str]:
        """Connect a channel."""
        data = self._post(f"/channels/{channel_id}/connect")
        return data

    def disconnect_channel(self, channel_id: str) -> Dict[str, str]:
        """Disconnect a channel."""
        data = self._post(f"/channels/{channel_id}/disconnect")
        return data

    # ==================== Monitoring ====================

    def get_health(self) -> HealthResponse:
        """Get system health."""
        data = self._get("/health")
        return HealthResponse(**data)

    def get_status(self) -> StatusResponse:
        """Get system status."""
        data = self._get("/status")
        return StatusResponse(**data)

    def get_metrics(self) -> MetricsResponse:
        """Get system metrics."""
        data = self._get("/metrics")
        return MetricsResponse(**data)

    # ==================== Swarm ====================

    def execute_swarm(
        self,
        description: str,
        user_id: Optional[str] = None,
        execution_mode: str = "consensus",
        required_capabilities: Optional[List[str]] = None,
        enable_search: bool = True,
        search_queries: Optional[List[str]] = None,
        max_agents: int = 5,
    ) -> SwarmTaskResponse:
        """
        Execute a task through the swarm orchestrator.

        Args:
            description: Task description
            user_id: User ID
            execution_mode: single, swarm, or consensus
            required_capabilities: Required agent capabilities
            enable_search: Enable web search
            search_queries: Custom search queries
            max_agents: Max agents to involve
        """
        data = self._post("/swarm/execute", json={
            "description": description,
            "user_id": user_id,
            "execution_mode": execution_mode,
            "required_capabilities": required_capabilities,
            "enable_search": enable_search,
            "search_queries": search_queries,
            "max_agents": max_agents,
        })
        return SwarmTaskResponse(**data)

    def plan_swarm(
        self,
        description: str,
        execution_mode: str = "consensus",
        required_capabilities: Optional[List[str]] = None,
        max_agents: int = 5,
    ) -> SwarmPlanResponse:
        """Get swarm execution plan without executing."""
        data = self._post("/swarm/plan", json={
            "description": description,
            "execution_mode": execution_mode,
            "required_capabilities": required_capabilities,
            "max_agents": max_agents,
        })
        return SwarmPlanResponse(**data)