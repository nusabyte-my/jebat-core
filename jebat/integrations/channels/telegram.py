"""Telegram channel adapter."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class TelegramChannel:
    """Telegram bot channel adapter."""

    def __init__(
        self,
        bot_token: str = "",
        ultra_loop: Any = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.bot_token = bot_token
        self.ultra_loop = ultra_loop
        self.config = config or {}
        self._running = False

    async def start(self) -> None:
        self._running = True
        logger.info("Telegram channel started")

    async def stop(self) -> None:
        self._running = False
        logger.info("Telegram channel stopped")

    async def send_message(self, recipient: str, message: str, **kwargs: Any) -> None:
        logger.info(f"Telegram: sending to {recipient}")


async def create_telegram_channel(
    bot_token: str = "",
    ultra_loop: Any = None,
    config: Optional[Dict[str, Any]] = None,
) -> TelegramChannel:
    channel = TelegramChannel(
        bot_token=bot_token,
        ultra_loop=ultra_loop,
        config=config or {},
    )
    return channel
