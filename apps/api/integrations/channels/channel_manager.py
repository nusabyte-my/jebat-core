"""
JEBAT Channel Manager

Multi-channel management for messaging integrations.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ChannelManager:
    """
    Channel manager for messaging integrations.

    Features:
    - Multi-channel support (Telegram, WhatsApp, Discord, etc.)
    - Message routing
    - Response handling
    - Channel health monitoring
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, ultra_loop=None):
        """
        Initialize the channel manager.

        Args:
            config: Configuration dictionary
            ultra_loop: Ultra-Loop instance for message processing
        """
        self.config = config or {}
        self.ultra_loop = ultra_loop
        self._channels: Dict[str, Any] = {}
        self._running = False

        # Message routing
        self._message_handlers: List[Callable] = []

        # Channel statistics
        self._stats = {
            "messages_received": 0,
            "messages_sent": 0,
            "errors": 0,
        }

        logger.info("ChannelManager initialized")

    def register_channel(self, name: str, channel: Any):
        """
        Register a channel.

        Args:
            name: Channel name
            channel: Channel instance
        """
        self._channels[name] = channel
        logger.info(f"Registered channel: {name}")

    def get_channel(self, name: str) -> Optional[Any]:
        """
        Get a channel by name.

        Args:
            name: Channel name

        Returns:
            Channel instance or None
        """
        return self._channels.get(name)

    def list_channels(self) -> List[str]:
        """
        List all registered channels.

        Returns:
            List of channel names
        """
        return list(self._channels.keys())

    async def start_all(self):
        """Start all registered channels"""
        if self._running:
            logger.warning("Channel manager already running")
            return

        self._running = True

        for name, channel in self._channels.items():
            try:
                if hasattr(channel, "start"):
                    await channel.start()
                    logger.info(f"Started channel: {name}")
            except Exception as e:
                logger.error(f"Failed to start channel {name}: {e}")
                self._stats["errors"] += 1

    async def stop_all(self):
        """Stop all registered channels"""
        self._running = False

        for name, channel in self._channels.items():
            try:
                if hasattr(channel, "stop"):
                    await channel.stop()
                    logger.info(f"Stopped channel: {name}")
            except Exception as e:
                logger.error(f"Error stopping channel {name}: {e}")

    async def send_message(
        self,
        channel: str,
        message: str,
        recipient: str,
        **kwargs,
    ):
        """
        Send a message to a channel.

        Args:
            channel: Channel name
            message: Message text
            recipient: Recipient identifier
            **kwargs: Additional arguments
        """
        if channel not in self._channels:
            logger.error(f"Channel not found: {channel}")
            self._stats["errors"] += 1
            return

        try:
            ch = self._channels[channel]

            if hasattr(ch, "send_message"):
                await ch.send_message(recipient, message, **kwargs)
                self._stats["messages_sent"] += 1
                logger.debug(f"Sent message to {channel}:{recipient}")
            else:
                logger.error(f"Channel {channel} doesn't support send_message")

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self._stats["errors"] += 1

    async def broadcast(self, message: str, channels: Optional[List[str]] = None):
        """
        Broadcast message to multiple channels.

        Args:
            message: Message text
            channels: List of channel names (None = all)
        """
        if channels is None:
            channels = list(self._channels.keys())

        for channel in channels:
            try:
                await self.send_message(channel, message, "broadcast")
            except Exception as e:
                logger.error(f"Broadcast error on {channel}: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get channel manager statistics.

        Returns:
            Statistics dictionary
        """
        return {
            **self._stats,
            "channels": list(self._channels.keys()),
            "channel_count": len(self._channels),
            "running": self._running,
        }

    def add_message_handler(self, handler: Callable):
        """
        Add a message handler.

        Args:
            handler: Async callable that receives (channel, message, sender)
        """
        self._message_handlers.append(handler)
        logger.info(f"Added message handler: {handler.__name__}")

    async def process_message(self, channel: str, message: str, sender: str):
        """
        Process incoming message through handlers.

        Args:
            channel: Channel name
            message: Message text
            sender: Sender identifier
        """
        self._stats["messages_received"] += 1

        for handler in self._message_handlers:
            try:
                await handler(channel, message, sender)
            except Exception as e:
                logger.error(f"Message handler error: {e}")
                self._stats["errors"] += 1


__all__ = ["ChannelManager"]
