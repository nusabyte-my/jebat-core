"""
JEBAT Python SDK

Python client library for JEBAT AI Assistant REST API.

Installation:
    pip install jebat-sdk

Usage:
    from jebat_sdk import JEBATClient

    client = JEBATClient(base_url="http://localhost:8000")

    # Chat with JEBAT
    response = await client.chat("What is AI?")
    print(response.response)

    # Store memory
    memory = await client.store_memory("I prefer Python", user_id="user1")

    # Search memories
    memories = await client.search_memories("Python", user_id="user1")
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aiohttp


@dataclass
class ChatResponse:
    """Chat response model"""

    response: str
    confidence: float
    thinking_steps: int
    execution_time: float
    user_id: Optional[str]


@dataclass
class Memory:
    """Memory model"""

    id: str
    content: str
    layer: str
    user_id: str
    created_at: str
    heat_score: float


@dataclass
class SystemStatus:
    """System status model"""

    status: str
    version: str
    timestamp: str
    components: Dict[str, str]


@dataclass
class Metrics:
    """System metrics model"""

    ultra_loop: Dict[str, Any]
    ultra_think: Dict[str, Any]
    memory: Dict[str, Any]
    timestamp: str


class JEBATClient:
    """
    JEBAT API Client.

    Provides Pythonic interface to JEBAT REST API.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize JEBAT client.

        Args:
            base_url: JEBAT API base URL
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            )

        return self._session

    async def close(self):
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def health(self) -> Dict[str, Any]:
        """
        Check API health.

        Returns:
            Health status dict
        """
        session = await self._get_session()
        async with session.get(f"{self.base_url}/api/v1/health") as response:
            response.raise_for_status()
            return await response.json()

    async def status(self) -> SystemStatus:
        """
        Get system status.

        Returns:
            SystemStatus object
        """
        session = await self._get_session()
        async with session.get(f"{self.base_url}/api/v1/status") as response:
            response.raise_for_status()
            data = await response.json()
            return SystemStatus(**data)

    async def metrics(self) -> Metrics:
        """
        Get system metrics.

        Returns:
            Metrics object
        """
        session = await self._get_session()
        async with session.get(f"{self.base_url}/api/v1/metrics") as response:
            response.raise_for_status()
            data = await response.json()
            return Metrics(**data)

    async def chat(
        self,
        message: str,
        user_id: Optional[str] = None,
        mode: str = "deliberate",
        timeout: int = 30,
    ) -> ChatResponse:
        """
        Chat with JEBAT.

        Args:
            message: User message
            user_id: Optional user identifier
            mode: Thinking mode (fast, deliberate, deep, strategic, creative, critical)
            timeout: Timeout in seconds

        Returns:
            ChatResponse object
        """
        session = await self._get_session()

        payload = {
            "message": message,
            "user_id": user_id,
            "mode": mode,
            "timeout": timeout,
        }

        async with session.post(
            f"{self.base_url}/api/v1/chat/completions",
            json=payload,
        ) as response:
            response.raise_for_status()
            data = await response.json()
            return ChatResponse(**data)

    async def store_memory(
        self,
        content: str,
        user_id: str,
        layer: str = "M1_EPISODIC",
    ) -> Memory:
        """
        Store a memory.

        Args:
            content: Memory content
            user_id: User identifier
            layer: Memory layer (M0, M1_EPISODIC, M2_SEMANTIC, M3_CONCEPTUAL, M4_PROCEDURAL)

        Returns:
            Memory object
        """
        session = await self._get_session()

        payload = {
            "content": content,
            "user_id": user_id,
            "layer": layer,
        }

        async with session.post(
            f"{self.base_url}/api/v1/memories",
            json=payload,
        ) as response:
            response.raise_for_status()
            data = await response.json()
            return Memory(**data)

    async def list_memories(
        self,
        user_id: str,
        limit: int = 10,
    ) -> List[Memory]:
        """
        List user memories.

        Args:
            user_id: User identifier
            limit: Maximum results

        Returns:
            List of Memory objects
        """
        session = await self._get_session()

        params = {
            "user_id": user_id,
            "limit": limit,
        }

        async with session.get(
            f"{self.base_url}/api/v1/memories",
            params=params,
        ) as response:
            response.raise_for_status()
            data = await response.json()
            return [Memory(**m) for m in data]

    async def search_memories(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
    ) -> List[Memory]:
        """
        Search memories.

        Args:
            query: Search query
            user_id: User identifier
            limit: Maximum results

        Returns:
            List of Memory objects
        """
        session = await self._get_session()

        params = {
            "query": query,
            "user_id": user_id,
            "limit": limit,
        }

        async with session.get(
            f"{self.base_url}/api/v1/memories",
            params=params,
        ) as response:
            response.raise_for_status()
            data = await response.json()
            return [Memory(**m) for m in data]

    async def list_agents(self) -> Dict[str, Any]:
        """
        List available agents.

        Returns:
            Agents dict
        """
        session = await self._get_session()
        async with session.get(f"{self.base_url}/api/v1/agents") as response:
            response.raise_for_status()
            return await response.json()


# Convenience functions for synchronous usage


def create_client(
    base_url: str = "http://localhost:8000",
    api_key: Optional[str] = None,
) -> JEBATClient:
    """
    Create JEBAT client.

    Args:
        base_url: JEBAT API base URL
        api_key: Optional API key

    Returns:
        JEBATClient instance
    """
    return JEBATClient(base_url=base_url, api_key=api_key)


# Example usage


async def example():
    """Example usage of JEBAT SDK"""
    async with JEBATClient() as client:
        # Check health
        health = await client.health()
        print(f"Health: {health}")

        # Chat
        response = await client.chat("What is artificial intelligence?")
        print(f"Response: {response.response}")
        print(f"Confidence: {response.confidence:.1%}")

        # Store memory
        memory = await client.store_memory(
            "I prefer Python for development",
            user_id="example_user",
        )
        print(f"Stored memory: {memory.id}")

        # Search memories
        memories = await client.search_memories("Python", user_id="example_user")
        print(f"Found {len(memories)} memories")


if __name__ == "__main__":
    asyncio.run(example())
