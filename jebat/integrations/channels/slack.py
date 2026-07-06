"""
JEBAT Slack Channel Integration

Slack bot integration for JEBAT AI Assistant.

Features:
- Slash commands (/jebat think, /jebat status)
- Interactive messages
- Thread support
- App mentions
- Channel configuration

Usage:
    from jebat.integrations.channels.slack import SlackChannel

    channel = SlackChannel(
        bot_token="xoxb-YOUR-TOKEN",
        signing_secret="YOUR-SECRET",
        ultra_loop=loop,
    )
    await channel.start()
"""

import asyncio
import hashlib
import hmac
import json
import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class SlackChannel:
    """
    Slack bot channel integration.

    Supports:
    - Slash commands
    - Interactive messages
    - App mentions
    - Thread conversations
    - Channel configuration
    """

    def __init__(
        self,
        bot_token: str,
        signing_secret: str,
        ultra_loop=None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Slack channel.

        Args:
            bot_token: Slack bot token (xoxb-...)
            signing_secret: Slack signing secret
            ultra_loop: Ultra-Loop instance
            config: Additional configuration
        """
        self.bot_token = bot_token
        self.signing_secret = signing_secret
        self.ultra_loop = ultra_loop
        self.config = config or {}

        self._session = None
        self._running = False

        # Event handlers
        self.message_handlers: List[Callable] = []

        logger.info("SlackChannel initialized")

    async def start(self):
        """Start Slack bot"""
        if self._running:
            logger.warning("Slack bot already running")
            return

        try:
            import aiohttp

            self._session = aiohttp.ClientSession()

            # Verify token
            auth_test = await self._api_call("auth.test")
            logger.info(f"Slack bot started: {auth_test.get('user', 'unknown')}")

            self._running = True

        except ImportError:
            logger.error("aiohttp not installed. Run: pip install aiohttp")
            raise
        except Exception as e:
            logger.error(f"Failed to start Slack bot: {e}")
            raise

    async def stop(self):
        """Stop Slack bot"""
        self._running = False

        if self._session:
            await self._session.close()
            self._session = None

        logger.info("Slack bot stopped")

    async def _api_call(
        self,
        method: str,
        data: Optional[Dict] = None,
    ) -> Dict:
        """Make Slack API call"""
        url = f"https://slack.com/api/{method}"
        headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json",
        }

        async with self._session.post(
            url, headers=headers, json=data or {}
        ) as response:
            result = await response.json()

            if not result.get("ok"):
                raise Exception(
                    f"Slack API error: {result.get('error', 'Unknown error')}"
                )

            return result

    async def send_message(
        self,
        channel: str,
        text: str,
        thread_ts: Optional[str] = None,
        blocks: Optional[List[Dict]] = None,
        **kwargs,
    ):
        """
        Send message to Slack channel.

        Args:
            channel: Channel ID or name
            text: Message text
            thread_ts: Thread timestamp (for replies)
            blocks: Rich message blocks
            **kwargs: Additional arguments
        """
        data = {
            "channel": channel,
            "text": text,
            **kwargs,
        }

        if thread_ts:
            data["thread_ts"] = thread_ts

        if blocks:
            data["blocks"] = blocks

        try:
            result = await self._api_call("chat.postMessage", data)
            logger.debug(f"Sent Slack message to {channel}")
            return result

        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            raise

    async def send_ephemeral(
        self,
        channel: str,
        user: str,
        text: str,
        thread_ts: Optional[str] = None,
    ):
        """Send ephemeral message (visible only to user)"""
        data = {
            "channel": channel,
            "user": user,
            "text": text,
        }

        if thread_ts:
            data["thread_ts"] = thread_ts

        await self._api_call("chat.postEphemeral", data)

    async def process_interaction(
        self,
        payload: Dict,
        headers: Dict,
    ) -> Dict:
        """
        Process Slack interaction (slash command, action, event).

        Args:
            payload: Request payload
            headers: Request headers

        Returns:
            Response dict
        """
        # Verify signature
        if not self._verify_signature(payload, headers):
            return {"status": "error", "message": "Invalid signature"}

        # Handle different interaction types
        if "command" in payload:
            return await self._handle_slash_command(payload)
        elif "type" in payload and payload["type"] == "block_actions":
            return await self._handle_block_action(payload)
        elif "type" in payload and payload["type"] == "url_verification":
            return {"challenge": payload["challenge"]}

        return {"status": "ok"}

    def _verify_signature(self, payload: Dict, headers: Dict) -> bool:
        """Verify Slack request signature"""
        signature = headers.get("X-Slack-Signature", "")
        timestamp = headers.get("X-Slack-Request-Timestamp", "")

        # Check timestamp (5 minute window)
        import time

        if abs(time.time() - int(timestamp)) > 300:
            return False

        # Verify signature
        sig_basestring = f"v0:{timestamp}:{json.dumps(payload)}"
        my_signature = (
            "v0="
            + hmac.new(
                self.signing_secret.encode(), sig_basestring.encode(), hashlib.sha256
            ).hexdigest()
        )

        return hmac.compare_digest(signature, my_signature)

    async def _handle_slash_command(self, payload: Dict) -> Dict:
        """Handle slash command"""
        command = payload.get("command", "")
        text = payload.get("text", "").strip()
        channel = payload.get("channel_id")
        user_id = payload.get("user_id")
        response_url = payload.get("response_url")

        logger.info(f"Slack command: {command} by {user_id}")

        if command == "/jebat":
            if not text:
                return {
                    "text": "Usage: `/jebat <question>`\nExample: `/jebat What is AI?`",
                    "response_type": "ephemeral",
                }

            # Process with Ultra-Think
            if self.ultra_loop and self.ultra_loop.ultra_think:
                try:
                    from jebat.features.ultra_think import ThinkingMode

                    result = await self.ultra_loop.ultra_think.think(
                        problem=text,
                        mode=ThinkingMode.DELIBERATE,
                        user_id=user_id,
                        timeout=30,
                    )

                    # Send response
                    blocks = [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*🗡️ JEBAT Thinking Result*\n\n{result.conclusion[:2000]}",
                            },
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"Confidence: {result.confidence:.1%} | Steps: {len(result.reasoning_steps)}",
                                },
                            ],
                        },
                    ]

                    await self.send_message(channel, text="", blocks=blocks)

                    return {"status": "ok"}

                except Exception as e:
                    return {
                        "text": f"Error: {str(e)}",
                        "response_type": "ephemeral",
                    }
            else:
                return {
                    "text": "JEBAT is not initialized",
                    "response_type": "ephemeral",
                }

        elif command == "/jebat-status":
            if self.ultra_loop:
                metrics = self.ultra_loop.get_metrics()
                text = (
                    f"*🗡️ JEBAT Status*\n\n"
                    f"• Cycles: {metrics.get('total_cycles', 0)}\n"
                    f"• Success: {metrics.get('successful_cycles', 0)}\n"
                    f"• Failed: {metrics.get('failed_cycles', 0)}"
                )
            else:
                text = "JEBAT is not initialized"

            return {"text": text, "response_type": "in_channel"}

        else:
            return {
                "text": f"Unknown command: {command}",
                "response_type": "ephemeral",
            }

    async def _handle_block_action(self, payload: Dict) -> Dict:
        """Handle interactive block action"""
        actions = payload.get("actions", [])
        user = payload.get("user", {})
        channel = payload.get("channel", {})

        for action in actions:
            action_id = action.get("action_id")
            value = action.get("value")

            logger.info(f"Slack action: {action_id} by {user.get('id')}")

            # Handle specific actions
            if action_id == "think_again":
                # Re-run thinking with different mode
                pass

        return {"status": "ok"}

    def add_message_handler(self, handler: Callable):
        """Add message handler"""
        self.message_handlers.append(handler)
        logger.info(f"Added Slack message handler: {handler.__name__}")


async def create_slack_channel(
    bot_token: str,
    signing_secret: str,
    ultra_loop=None,
    config: Optional[Dict[str, Any]] = None,
) -> SlackChannel:
    """Factory function to create Slack channel"""
    channel = SlackChannel(
        bot_token=bot_token,
        signing_secret=signing_secret,
        ultra_loop=ultra_loop,
        config=config,
    )
    return channel
