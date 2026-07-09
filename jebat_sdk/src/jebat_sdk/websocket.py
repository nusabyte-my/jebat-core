"""
WebSocket client for JEBAT SDK streaming.

Provides WebSocket support for real-time chat streaming.
"""

import asyncio
import json
from typing import AsyncGenerator, Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import logging

import websockets
from websockets.client import WebSocketClientProtocol

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """WebSocket connection state."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    CLOSED = "closed"


@dataclass
class StreamChunk:
    """Stream chunk from WebSocket."""
    type: str  # "content", "thinking", "complete", "error"
    content: str = ""
    data: Optional[Dict[str, Any]] = None

    def is_final(self) -> bool:
        return self.type in ("complete", "error")


class JebatWebSocketClient:
    """
    WebSocket client for JEBAT streaming API.

    Usage:
        async with JebatWebSocketClient("ws://localhost:8000/ws/chat", token) as ws:
            async for chunk in ws.stream(chat_request):
                print(chunk.content, end="", flush=True)
    """

    def __init__(
        self,
        url: str,
        token: str,
        auto_reconnect: bool = True,
        max_reconnect_attempts: int = 5,
        reconnect_delay: float = 1.0,
        ping_interval: float = 20.0,
        ping_timeout: float = 10.0,
    ):
        """
        Initialize WebSocket client.

        Args:
            url: WebSocket URL (e.g., ws://localhost:8000/ws/chat)
            token: JWT access token for authentication
            auto_reconnect: Whether to auto-reconnect on disconnect
            max_reconnect_attempts: Maximum reconnection attempts
            reconnect_delay: Initial delay between reconnects (seconds)
            ping_interval: Ping interval in seconds
            ping_timeout: Ping timeout in seconds
        """
        self.url = url
        self.token = token
        self.auto_reconnect = auto_reconnect
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_delay = reconnect_delay
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout

        self._ws: Optional[WebSocketClientProtocol] = None
        self._state = ConnectionState.DISCONNECTED
        self._reconnect_attempts = 0
        self._receive_task: Optional[asyncio.Task] = None
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._callbacks: Dict[str, list] = {
            "connect": [],
            "disconnect": [],
            "message": [],
            "error": [],
        }

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def is_connected(self) -> bool:
        return self._state == ConnectionState.CONNECTED

    def on(self, event: str, callback: Callable):
        """Register event callback."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    async def connect(self) -> None:
        """Establish WebSocket connection."""
        if self._state == ConnectionState.CONNECTED:
            return

        self._state = ConnectionState.CONNECTING
        logger.info(f"Connecting to {self.url}")

        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            self._ws = await websockets.connect(
                self.url,
                extra_headers=headers,
                ping_interval=self.ping_interval,
                ping_timeout=self.ping_timeout,
            )

            self._state = ConnectionState.CONNECTED
            self._reconnect_attempts = 0
            logger.info("WebSocket connected")

            # Start receive loop
            self._receive_task = asyncio.create_task(self._receive_loop())

            # Trigger connect callbacks
            for cb in self._callbacks["connect"]:
                await self._safe_call(cb)

        except Exception as e:
            self._state = ConnectionState.DISCONNECTED
            logger.error(f"Connection failed: {e}")
            await self._trigger_error(e)
            raise

    async def disconnect(self) -> None:
        """Disconnect WebSocket."""
        self._state = ConnectionState.CLOSED
        self.auto_reconnect = False

        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        if self._ws:
            await self._ws.close()
            self._ws = None

        logger.info("WebSocket disconnected")
        await self._trigger_disconnect()

    async def _receive_loop(self) -> None:
        """Background task to receive messages."""
        try:
            async for message in self._ws:
                try:
                    data = json.loads(message)
                    await self._message_queue.put(data)
                    await self._trigger_message(data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON: {message}")
                except Exception as e:
                    logger.error(f"Message handling error: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Receive loop error: {e}")

        finally:
            if self.auto_reconnect and self._state != ConnectionState.CLOSED:
                await self._handle_reconnect()

    async def _handle_reconnect(self) -> None:
        """Handle automatic reconnection."""
        if self._state == ConnectionState.CLOSED:
            return

        self._state = ConnectionState.RECONNECTING

        while self._reconnect_attempts < 5:
            self._reconnect_attempts += 1
            delay = self.reconnect_delay * (2 ** (self._reconnect_attempts - 1))
            logger.info(f"Reconnecting in {delay}s (attempt {self._reconnect_attempts})")
            await asyncio.sleep(delay)

            try:
                await self.connect()
                return
            except Exception as e:
                logger.warning(f"Reconnect failed: {e}")

        logger.error("Max reconnect attempts reached")
        self._state = ConnectionState.DISCONNECTED
        await self._trigger_error(Exception("Max reconnect attempts reached"))

    async def send(self, data: Dict[str, Any]) -> None:
        """Send JSON message."""
        if not self._ws or not self.is_connected:
            raise ConnectionError("Not connected")
        await self._ws.send(json.dumps(data))

    async def stream(
        self,
        chat_request: Dict[str, Any],
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream chat response via WebSocket.

        Args:
            chat_request: Chat request dict with message, mode, etc.

        Yields:
            StreamChunk objects
        """
        if not self.is_connected:
            raise ConnectionError("Not connected")

        # Send chat request
        await self.send({"type": "chat", "data": chat_request})

        # Yield chunks from queue
        while True:
            try:
                # Wait for next message with timeout
                data = await asyncio.wait_for(
                    self._message_queue.get(),
                    timeout=30.0,
                )

                chunk = StreamChunk(
                    type=data.get("type", "content"),
                    content=data.get("content", ""),
                    data=data.get("data"),
                )
                yield chunk

                if chunk.is_final():
                    break

            except asyncio.TimeoutError:
                logger.warning("Stream timeout")
                yield StreamChunk(type="error", content="Stream timeout")
                break
            except Exception as e:
                logger.error(f"Stream error: {e}")
                yield StreamChunk(type="error", content=str(e))
                break

    async def send_chat(self, message: str, mode: str = "deliberate") -> None:
        """Send a chat message."""
        await self.send({
            "type": "chat",
            "data": {"message": message, "mode": mode, "stream": True}
        })

    # Event callbacks
    async def _safe_call(self, callback: Callable) -> None:
        """Safely call a callback."""
        try:
            result = callback()
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            logger.error(f"Callback error: {e}")

    async def _trigger_message(self, data: Dict[str, Any]) -> None:
        for cb in self._callbacks["message"]:
            await self._safe_call(lambda: cb(data))

    async def _trigger_connect(self) -> None:
        for cb in self._callbacks["connect"]:
            await self._safe_call(cb)

    async def _trigger_disconnect(self) -> None:
        for cb in self._callbacks["disconnect"]:
            await self._safe_call(cb)

    async def _trigger_error(self, error: Exception) -> None:
        for cb in self._callbacks["error"]:
            await self._safe_call(lambda: cb(error))

    async def __aenter__(self) -> "JebatWebSocketClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect()


class JebatWebSocketClientSync:
    """
    Synchronous wrapper for WebSocket client.

    Use this for synchronous code that needs streaming.
    """

    def __init__(self, *args, **kwargs):
        self._async_client = JebatWebSocketClient(*args, **kwargs)
        self._loop = None

    def _get_loop(self):
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop

    def connect(self) -> None:
        loop = self._get_loop()
        loop.run_until_complete(self._async_client.connect())

    def disconnect(self) -> None:
        loop = self._get_loop()
        loop.run_until_complete(self._async_client.disconnect())

    def send_chat(self, message: str, mode: str = "deliberate") -> None:
        loop = self._get_loop()
        loop.run_until_complete(self._async_client.send_chat(message, mode))

    def stream_chat(
        self,
        message: str,
        mode: str = "deliberate",
    ):
        """Stream chat response (blocking generator)."""
        loop = self._get_loop()

        async def _stream():
            self._async_client.stream({
                "message": message,
                "mode": mode,
            })
            async for chunk in self._async_client.stream({"message": message, "mode": mode}):
                yield chunk

        return loop.run_until_complete(self._async_generator(loop, _stream()))

    def _async_generator(self, loop, gen):
        """Convert async generator to sync generator."""
        while True:
            try:
                item = loop.run_until_complete(gen.__anext__())
                yield item
            except StopAsyncIteration:
                break

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()