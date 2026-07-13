"""
JEBAT WhatsApp Channel Integration

WhatsApp Business API integration for JEBAT AI Assistant.

Features:
- Send/receive messages
- Media support (images, documents)
- Group chat support
- End-to-end encryption ready
- Webhook handling

Usage:
    from jebat.integrations.channels.whatsapp import WhatsAppChannel

    channel = WhatsAppChannel(
        phone_number_id="YOUR_PHONE_NUMBER_ID",
        access_token="YOUR_ACCESS_TOKEN",
        verify_token="YOUR_VERIFY_TOKEN",
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

import aiohttp

logger = logging.getLogger(__name__)


class WhatsAppChannel:
    """
    WhatsApp Business API channel integration.

    Supports:
    - Text messages
    - Media messages (images, documents, audio)
    - Group chats
    - Read receipts
    - Webhook verification
    """

    def __init__(
        self,
        phone_number_id: str,
        access_token: str,
        verify_token: str,
        ultra_loop=None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize WhatsApp channel.

        Args:
            phone_number_id: WhatsApp Business API phone number ID
            access_token: Meta API access token
            verify_token: Webhook verification token
            ultra_loop: Ultra-Loop instance for message processing
            config: Additional configuration
        """
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.verify_token = verify_token
        self.ultra_loop = ultra_loop
        self.config = config or {}

        # API endpoint
        self.base_url = "https://graph.facebook.com/v18.0"

        # Session
        self._session: Optional[aiohttp.ClientSession] = None
        self._running = False

        # Message handlers
        self.message_handlers: List[Callable] = []

        logger.info("WhatsAppChannel initialized")

    async def start(self):
        """Start WhatsApp channel"""
        if self._running:
            logger.warning("WhatsApp channel already running")
            return

        self._session = aiohttp.ClientSession()
        self._running = True

        # Verify connection
        try:
            account_info = await self._api_call(f"/{self.phone_number_id}")
            logger.info(
                f"WhatsApp channel started: {account_info.get('name', 'unknown')}"
            )
        except Exception as e:
            logger.error(f"Failed to start WhatsApp channel: {e}")
            raise

        logger.info("WhatsApp channel ready to receive webhooks")

    async def stop(self):
        """Stop WhatsApp channel"""
        self._running = False

        if self._session:
            await self._session.close()
            self._session = None

        logger.info("WhatsApp channel stopped")

    async def _api_call(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict] = None,
    ) -> Dict:
        """
        Make WhatsApp API call.

        Args:
            endpoint: API endpoint
            method: HTTP method
            data: Request data

        Returns:
            API response
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        async with self._session.request(
            method,
            url,
            headers=headers,
            json=data if method == "POST" else None,
            params=data if method == "GET" else None,
        ) as response:
            result = await response.json()

            if response.status != 200:
                raise Exception(
                    f"WhatsApp API error: {result.get('error', {}).get('message', 'Unknown error')}"
                )

            return result

    async def send_message(
        self,
        recipient: str,
        message: str,
        message_type: str = "text",
        **kwargs,
    ):
        """
        Send message via WhatsApp.

        Args:
            recipient: Recipient phone number (with country code)
            message: Message text
            message_type: Type of message (text, image, document, etc.)
            **kwargs: Additional arguments
        """
        endpoint = f"/{self.phone_number_id}/messages"

        if message_type == "text":
            data = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "text",
                "text": {
                    "body": message,
                    "preview_url": kwargs.get("preview_url", True),
                },
            }
        elif message_type == "image":
            data = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "image",
                "image": {
                    "link": message,  # Image URL
                    "caption": kwargs.get("caption", ""),
                },
            }
        elif message_type == "document":
            data = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "document",
                "document": {
                    "link": message,  # Document URL
                    "caption": kwargs.get("caption", ""),
                    "filename": kwargs.get("filename", "document.pdf"),
                },
            }
        else:
            raise ValueError(f"Unsupported message type: {message_type}")

        try:
            result = await self._api_call(endpoint, method="POST", data=data)
            message_id = result.get("messages", [{}])[0].get("id")
            logger.info(f"Sent WhatsApp message to {recipient}: {message_id}")
            return message_id

        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            raise

    async def send_template(
        self,
        recipient: str,
        template_name: str,
        language: str = "en_US",
        components: Optional[List[Dict]] = None,
    ):
        """
        Send template message (for initiating conversations).

        Args:
            recipient: Recipient phone number
            template_name: Template name from Meta Business Manager
            language: Template language code
            components: Template components (variables, buttons, etc.)
        """
        endpoint = f"/{self.phone_number_id}/messages"

        data = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language,
                },
                "components": components or [],
            },
        }

        try:
            result = await self._api_call(endpoint, method="POST", data=data)
            message_id = result.get("messages", [{}])[0].get("id")
            logger.info(f"Sent WhatsApp template to {recipient}: {message_id}")
            return message_id

        except Exception as e:
            logger.error(f"Failed to send WhatsApp template: {e}")
            raise

    async def mark_as_read(self, message_id: str):
        """
        Mark message as read.

        Args:
            message_id: Message ID to mark as read
        """
        endpoint = f"/{self.phone_number_id}/messages"

        data = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }

        try:
            await self._api_call(endpoint, method="POST", data=data)
            logger.debug(f"Marked message {message_id} as read")
        except Exception as e:
            logger.error(f"Failed to mark message as read: {e}")

    async def process_webhook(self, data: Dict) -> Dict:
        """
        Process incoming webhook from WhatsApp.

        Args:
            data: Webhook payload

        Returns:
            Response dict
        """
        try:
            # Handle verification challenge
            if isinstance(data, dict) and data.get("hub.mode") == "subscribe":
                return await self._handle_verification(data)

            # Handle messages
            if isinstance(data, dict) and "entry" in data:
                await self._handle_messages(data)

            return {"status": "ok"}

        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            return {"status": "error", "message": str(e)}

    async def _handle_verification(self, data: Dict) -> Dict:
        """Handle webhook verification challenge"""
        mode = data.get("hub.mode")
        token = data.get("hub.verify_token")
        challenge = data.get("hub.challenge")

        if mode == "subscribe" and token == self.verify_token:
            logger.info("WhatsApp webhook verified")
            return {"status": "verified", "challenge": str(challenge)}
        else:
            logger.warning("Webhook verification failed")
            return {"status": "forbidden", "code": 403}

    async def _handle_messages(self, data: Dict):
        """Handle incoming messages"""
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})

                # Check for messages
                messages = value.get("messages", [])
                for message in messages:
                    await self._process_message(message, value)

                # Check for status updates
                statuses = value.get("statuses", [])
                for status in statuses:
                    await self._process_status(status)

    def _extract_content(self, message: Dict, message_type: str) -> str:
        """Extract human-readable content from a WhatsApp message."""
        if message_type == "text":
            return message.get("text", {}).get("body", "")
        if message_type in ("image", "document", "audio", "voice", "video", "sticker"):
            caption = message.get(message_type, {}).get("caption", "")
            label = message_type.capitalize()
            return f"[{label}]{(': ' + caption) if caption else ''}"
        return "[Unsupported message]"

    async def _process_through_ultra_loop(self, text: str, user_id: str) -> str:
        """
        Bridge a user message to the Ultra-Loop and produce a reply.

        Stores the message in memory and generates a response via
        Ultra-Think. Always returns a safe string so callers can reply.
        """
        try:
            if self.ultra_loop and getattr(self.ultra_loop, "memory_manager", None):
                await self.ultra_loop.memory_manager.store(
                    content=text,
                    user_id=str(user_id),
                )

            ultra_think = (
                getattr(self.ultra_loop, "ultra_think", None)
                if self.ultra_loop
                else None
            )
            if ultra_think:
                from jebat.features.ultra_think import ThinkingMode

                result = await ultra_think.think(
                    problem=text,
                    mode=ThinkingMode.DELIBERATE,
                    user_id=str(user_id),
                    timeout=30,
                )
                return result.conclusion

            return f"✅ Message received: {text[:200]}"

        except Exception as e:
            logger.error(f"WhatsApp Ultra-Loop error: {e}")
            return "⚠️ Sorry, I couldn't process that message right now."

    async def _process_message(self, message: Dict, metadata: Dict):
        """Process individual message"""
        from_number = message.get("from", "")
        message_id = message.get("id", "")
        message_type = message.get("type", "")
        timestamp = message.get("timestamp", "")

        logger.info(f"Received WhatsApp message from {from_number}: {message_id}")

        content = self._extract_content(message, message_type)
        if not content:
            return

        # Process through Ultra-Loop if connected
        reply = await self._process_through_ultra_loop(content, from_number)

        # Acknowledge read receipt best-effort
        try:
            if message_id:
                await self.mark_as_read(message_id)
        except Exception as e:
            logger.debug(f"Failed to mark message read: {e}")

        try:
            await self.send_message(from_number, reply)
        except Exception as e:
            logger.error(f"Failed to send WhatsApp reply: {e}")

        # Call message handlers
        for handler in self.message_handlers:
            try:
                await handler(from_number, content, message)
            except Exception as e:
                logger.error(f"Message handler error: {e}")

    async def _process_status(self, status: Dict):
        """Process message status updates"""
        message_id = status.get("id", "")
        recipient = status.get("recipient_id", "")
        status_type = status.get("status", "")

        logger.debug(f"Message {message_id} status: {status_type}")

        # Handle different statuses
        if status_type == "delivered":
            logger.info(f"Message {message_id} delivered to {recipient}")
        elif status_type == "read":
            logger.info(f"Message {message_id} read by {recipient}")
        elif status_type == "failed":
            error = status.get("errors", [{}])[0]
            logger.error(
                f"Message {message_id} failed: {error.get('message', 'Unknown')}"
            )

    def add_message_handler(self, handler: Callable):
        """
        Add message handler.

        Args:
            handler: Async callable that receives (from_number, content, message)
        """
        self.message_handlers.append(handler)
        logger.info(f"Added WhatsApp message handler: {handler.__name__}")


async def create_whatsapp_channel(
    phone_number_id: str,
    access_token: str,
    verify_token: str,
    ultra_loop=None,
    config: Optional[Dict[str, Any]] = None,
) -> WhatsAppChannel:
    """
    Factory function to create WhatsApp channel.

    Args:
        phone_number_id: WhatsApp Business API phone number ID
        access_token: Meta API access token
        verify_token: Webhook verification token
        ultra_loop: Ultra-Loop instance
        config: Configuration

    Returns:
        WhatsAppChannel instance
    """
    channel = WhatsAppChannel(
        phone_number_id=phone_number_id,
        access_token=access_token,
        verify_token=verify_token,
        ultra_loop=ultra_loop,
        config=config,
    )
    return channel
