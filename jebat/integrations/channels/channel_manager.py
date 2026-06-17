"""Channel manager for multi-platform messaging integration."""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ChannelManager:
    """Manages messaging channels and routes messages."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        ultra_loop: Any = None,
    ):
        self.config = config or {}
        self.ultra_loop = ultra_loop
        self._channels: Dict[str, Any] = {}
        self._handlers: List[Callable] = []
        self._messages_sent = 0
        self._messages_received = 0
        self._errors = 0

    def register_channel(self, name: str, channel: Any) -> None:
        self._channels[name] = channel

    def list_channels(self) -> List[str]:
        return list(self._channels.keys())

    async def send_message(self, channel_name: str, message: str, recipient: str, **kwargs: Any) -> None:
        channel = self._channels.get(channel_name)
        if channel:
            try:
                await channel.send_message(recipient, message, **kwargs)
                self._messages_sent += 1
            except Exception as e:
                self._errors += 1
                logger.error(f"Failed to send message on {channel_name}: {e}")

    async def broadcast(self, message: str) -> None:
        for name, channel in self._channels.items():
            try:
                if hasattr(channel, "send_message"):
                    await channel.send_message("broadcast", message)
                    self._messages_sent += 1
            except Exception:
                self._errors += 1

    def add_message_handler(self, handler: Callable) -> None:
        self._handlers.append(handler)

    async def process_message(self, channel_name: str, message: str, sender: str) -> None:
        self._messages_received += 1
        for handler in self._handlers:
            try:
                await handler(channel_name, message, sender)
            except Exception as e:
                self._errors += 1
                logger.error(f"Handler error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        return {
            "messages_sent": self._messages_sent,
            "messages_received": self._messages_received,
            "errors": self._errors,
            "channel_count": len(self._channels),
        }
