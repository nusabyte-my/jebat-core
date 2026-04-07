"""
JEBAT Telegram Channel Integration

Telegram bot integration for JEBAT AI Assistant.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class TelegramChannel:
    """
    Telegram channel integration.

    Features:
    - Receive messages from Telegram
    - Send responses to Telegram
    - Group chat support
    - Command handling
    """

    def __init__(
        self,
        bot_token: str,
        ultra_loop=None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Telegram channel.

        Args:
            bot_token: Telegram bot token
            ultra_loop: Ultra-Loop instance for message processing
            config: Additional configuration
        """
        self.bot_token = bot_token
        self.ultra_loop = ultra_loop
        self.config = config or {}

        # Message handlers
        self.message_handlers: List[Callable] = []

        # Bot state
        self._running = False
        self._session = None

        logger.info("TelegramChannel initialized")

    async def start(self):
        """Start the Telegram bot"""
        if self._running:
            logger.warning("Telegram bot already running")
            return

        try:
            # Import aiohttp for async HTTP requests
            import aiohttp

            self._session = aiohttp.ClientSession()
            self._running = True

            # Get bot info to verify token
            bot_info = await self._api_call("getMe")
            logger.info(f"Telegram bot started: @{bot_info.get('username', 'unknown')}")

            # Start polling for messages
            asyncio.create_task(self._poll_messages())

        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")
            raise

    async def stop(self):
        """Stop the Telegram bot"""
        self._running = False

        if self._session:
            await self._session.close()
            self._session = None

        logger.info("Telegram bot stopped")

    async def _api_call(self, method: str, data: Optional[Dict] = None) -> Dict:
        """
        Make Telegram API call.

        Args:
            method: API method name
            data: Request data

        Returns:
            API response
        """
        url = f"https://api.telegram.org/bot{self.bot_token}/{method}"

        async with self._session.post(url, json=data or {}) as response:
            result = await response.json()

            if not result.get("ok"):
                raise Exception(
                    f"Telegram API error: {result.get('description', 'Unknown error')}"
                )

            return result.get("result", {})

    async def _poll_messages(self):
        """Poll for new messages from Telegram"""
        offset = 0

        while self._running:
            try:
                # Get updates
                updates = await self._api_call(
                    "getUpdates",
                    {
                        "offset": offset,
                        "timeout": 30,
                    },
                )

                for update in updates:
                    offset = max(offset, update.get("update_id", 0) + 1)

                    # Process message
                    if "message" in update:
                        await self._process_message(update["message"])

            except Exception as e:
                logger.error(f"Error polling messages: {e}")
                await asyncio.sleep(5)

    async def _process_message(self, message: Dict):
        """
        Process incoming message.

        Args:
            message: Telegram message object
        """
        try:
            chat_id = message.get("chat", {}).get("id")
            user_id = message.get("from", {}).get("id")
            text = message.get("text", "")

            logger.info(
                f"Received message from {user_id} in chat {chat_id}: {text[:50]}..."
            )

            # Handle commands
            if text.startswith("/"):
                await self._handle_command(chat_id, user_id, text)
                return

            # Process through Ultra-Loop if connected
            if self.ultra_loop:
                response = await self._process_through_ultra_loop(
                    text, user_id, chat_id
                )
                await self.send_message(chat_id, response)
            else:
                # Fallback: echo response
                await self.send_message(
                    chat_id, f"Message received: {text}\n\n(Ultra-Loop not connected)"
                )

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def _handle_command(self, chat_id: int, user_id: int, command: str):
        """
        Handle Telegram command.

        Args:
            chat_id: Chat identifier
            user_id: User identifier
            command: Command text
        """
        cmd = command.split()[0].lower()

        if cmd == "/start":
            await self.send_message(
                chat_id,
                "🗡️ **JEBAT** - AI Assistant\n\n"
                "I'm here to help you! Send me any message and I'll process it.\n\n"
                "Commands:\n"
                "/start - Start the bot\n"
                "/help - Show help\n"
                "/status - System status\n",
            )

        elif cmd == "/help":
            await self.send_message(
                chat_id,
                "**JEBAT Help**\n\n"
                "I'm an AI assistant with eternal memory.\n\n"
                "Just send me any message and I'll:\n"
                "- Remember our conversation\n"
                "- Process your requests\n"
                "- Execute tasks through agents\n\n",
            )

        elif cmd == "/status":
            if self.ultra_loop:
                metrics = self.ultra_loop.get_metrics()
                status = (
                    "**JEBAT Status**\n\n"
                    f"Cycles: {metrics.get('total_cycles', 0)}\n"
                    f"Success Rate: {metrics.get('successful_cycles', 0) / max(metrics.get('total_cycles', 1), 1) * 100:.1f}%\n"
                )
            else:
                status = "**JEBAT Status**\n\nUltra-Loop not connected\n"

            await self.send_message(chat_id, status)

        else:
            await self.send_message(
                chat_id, f"Unknown command: {cmd}\nUse /help for available commands."
            )

    async def _process_through_ultra_loop(
        self, text: str, user_id: int, chat_id: int
    ) -> str:
        """
        Process message through Ultra-Loop.

        Args:
            text: Message text
            user_id: User identifier
            chat_id: Chat identifier

        Returns:
            Response text
        """
        try:
            # Store message in memory
            if self.ultra_loop.memory_manager:
                await self.ultra_loop.memory_manager.store(
                    content=text,
                    user_id=str(user_id),
                )

            # For now, return simple acknowledgment
            # In full implementation, this would trigger Ultra-Loop cycle
            return f"✅ Message processed: {text[:50]}..."

        except Exception as e:
            logger.error(f"Error processing through Ultra-Loop: {e}")
            return f"Error processing message: {e}"

    async def send_message(
        self, chat_id: int, text: str, reply_to: Optional[int] = None
    ):
        """
        Send message to Telegram chat.

        Args:
            chat_id: Chat identifier
            text: Message text
            reply_to: Message ID to reply to
        """
        try:
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
            }

            if reply_to:
                data["reply_to_message_id"] = reply_to

            await self._api_call("sendMessage", data)
            logger.debug(f"Sent message to {chat_id}")

        except Exception as e:
            logger.error(f"Failed to send message: {e}")


async def create_telegram_channel(
    bot_token: str,
    ultra_loop=None,
    config: Optional[Dict[str, Any]] = None,
) -> TelegramChannel:
    """
    Factory function to create Telegram channel.

    Args:
        bot_token: Telegram bot token
        ultra_loop: Ultra-Loop instance
        config: Configuration

    Returns:
        TelegramChannel instance
    """
    channel = TelegramChannel(
        bot_token=bot_token,
        ultra_loop=ultra_loop,
        config=config,
    )
    return channel
