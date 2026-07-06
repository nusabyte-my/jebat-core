"""
Perisai — Nexus Multi-Channel Bot Orchestrator

Named after the Malay shield — protection and unified communication.
Orchestrates bots across Telegram, Discord, Slack, Signal, Matrix,
and WhatsApp with a single configuration and unified message routing.
"""

from __future__ import annotations

import json
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional


# ─── Channel Types ──────────────────────────────────────────────

@dataclass
class ChannelConfig:
    """Configuration for a messaging channel."""
    channel_id: str
    platform: str  # telegram, discord, slack, signal, matrix, whatsapp
    enabled: bool = True
    bot_token: str = ""
    webhook_url: str = ""
    api_key: str = ""
    default_channel: str = ""  # Default chat/group ID
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IncomingMessage:
    """A message received from any platform."""
    message_id: str
    platform: str
    channel_id: str
    sender_id: str
    sender_name: str
    content: str
    timestamp: str
    reply_to: str | None = None
    attachments: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OutgoingMessage:
    """A message to be sent to any platform."""
    platform: str
    channel_id: str
    content: str
    reply_to: str | None = None
    parse_mode: str = "markdown"
    attachments: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


# ─── Platform Adapters (Abstract) ──────────────────────────────

class PlatformAdapter:
    """Base class for platform-specific adapters."""

    platform: str = "base"

    async def send_message(self, msg: OutgoingMessage) -> dict[str, Any]:
        raise NotImplementedError

    async def poll_messages(self) -> list[IncomingMessage]:
        raise NotImplementedError

    async def health_check(self) -> bool:
        raise False


class TelegramAdapter(PlatformAdapter):
    """Telegram Bot API adapter."""

    platform = "telegram"

    def __init__(self, bot_token: str) -> None:
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    async def send_message(self, msg: OutgoingMessage) -> dict[str, Any]:
        """Send message via Telegram Bot API."""
        import urllib.request

        payload = {
            "chat_id": msg.channel_id,
            "text": msg.content,
            "parse_mode": "Markdown" if msg.parse_mode == "markdown" else None,
        }
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            req = urllib.request.Request(
                f"{self.base_url}/sendMessage",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def health_check(self) -> bool:
        """Verify bot token is valid."""
        import urllib.request
        try:
            with urllib.request.urlopen(f"{self.base_url}/getMe", timeout=5) as resp:
                data = json.loads(resp.read())
                return data.get("ok", False)
        except Exception:
            return False


class DiscordAdapter(PlatformAdapter):
    """Discord Bot adapter via webhooks."""

    platform = "discord"

    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    async def send_message(self, msg: OutgoingMessage) -> dict[str, Any]:
        """Send message via Discord webhook."""
        import urllib.request

        payload = {"content": msg.content}
        try:
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return {"ok": resp.status == 204}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def health_check(self) -> bool:
        return self.webhook_url.startswith("https://discord.com/api/webhooks/")


class SlackAdapter(PlatformAdapter):
    """Slack Bot adapter via webhooks."""

    platform = "slack"

    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    async def send_message(self, msg: OutgoingMessage) -> dict[str, Any]:
        """Send message via Slack webhook."""
        import urllib.request

        payload = {"text": msg.content}
        try:
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return {"ok": resp.status == 200}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def health_check(self) -> bool:
        return "hooks.slack.com" in self.webhook_url


class WebhookAdapter(PlatformAdapter):
    """Generic webhook adapter for Matrix, Signal, WhatsApp, etc."""

    platform = "webhook"

    def __init__(self, webhook_url: str, api_key: str = "") -> None:
        self.webhook_url = webhook_url
        self.api_key = api_key

    async def send_message(self, msg: OutgoingMessage) -> dict[str, Any]:
        """Send message via generic webhook."""
        import urllib.request

        payload = {"content": msg.content, "channel": msg.channel_id}
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode(),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return {"ok": resp.status in (200, 201, 204)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def health_check(self) -> bool:
        return bool(self.webhook_url)


# ─── Adapter Factory ────────────────────────────────────────────

ADAPTERS = {
    "telegram": TelegramAdapter,
    "discord": DiscordAdapter,
    "slack": SlackAdapter,
    "signal": WebhookAdapter,
    "matrix": WebhookAdapter,
    "whatsapp": WebhookAdapter,
}


def create_adapter(config: ChannelConfig) -> PlatformAdapter:
    """Create a platform adapter from config."""
    adapter_cls = ADAPTERS.get(config.platform, WebhookAdapter)

    if config.platform == "telegram":
        return TelegramAdapter(bot_token=config.bot_token)
    elif config.platform in ("discord",):
        return DiscordAdapter(webhook_url=config.webhook_url)
    elif config.platform in ("slack",):
        return SlackAdapter(webhook_url=config.webhook_url)
    else:
        return WebhookAdapter(webhook_url=config.webhook_url, api_key=config.api_key)


# ─── Nexus Store ────────────────────────────────────────────────

class NexusStore:
    """Persistent storage for Nexus channel configs and message logs."""

    def __init__(self, data_dir: str | Path | None = None) -> None:
        self.data_dir = Path(data_dir or "~/.jebat/nexus").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.data_dir / "channels.json"
        self.messages_file = self.data_dir / "messages.jsonl"

    def load_channels(self) -> list[ChannelConfig]:
        """Load channel configurations."""
        if not self.config_file.exists():
            return []
        data = json.loads(self.config_file.read_text(encoding="utf-8"))
        return [
            ChannelConfig(
                channel_id=c["channel_id"],
                platform=c["platform"],
                enabled=c.get("enabled", True),
                bot_token=c.get("bot_token", ""),
                webhook_url=c.get("webhook_url", ""),
                api_key=c.get("api_key", ""),
                default_channel=c.get("default_channel", ""),
                metadata=c.get("metadata", {}),
            )
            for c in data.get("channels", [])
        ]

    def save_channels(self, channels: list[ChannelConfig]) -> None:
        """Save channel configurations."""
        data = {
            "channels": [
                {
                    "channel_id": c.channel_id,
                    "platform": c.platform,
                    "enabled": c.enabled,
                    "bot_token": c.bot_token,
                    "webhook_url": c.webhook_url,
                    "api_key": c.api_key,
                    "default_channel": c.default_channel,
                    "metadata": c.metadata,
                }
                for c in channels
            ]
        }
        self.config_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def log_message(self, msg: IncomingMessage | OutgoingMessage, direction: str) -> None:
        """Log a message."""
        record = {
            "direction": direction,
            "platform": msg.platform,
            "channel_id": msg.channel_id,
            "content": msg.content[:500],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with self.messages_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def get_message_log(self, limit: int = 50) -> list[dict]:
        """Load recent messages."""
        if not self.messages_file.exists():
            return []
        messages = []
        for line in self.messages_file.read_text(encoding="utf-8").splitlines():
            if line.strip():
                messages.append(json.loads(line))
        return messages[-limit:]


# ─── Perisai Nexus Engine ───────────────────────────────────────

class PerisaiNexus:
    """
    Perisai — Multi-Channel Bot Orchestrator.

    Manages connections to multiple messaging platforms,
    routes messages, and provides unified bot responses.
    """

    def __init__(self, data_dir: str | Path | None = None) -> None:
        self.store = NexusStore(data_dir=data_dir)
        self.adapters: dict[str, PlatformAdapter] = {}
        self._handlers: list[Callable[[IncomingMessage], str | None]] = []
        self._load_adapters()

    def _load_adapters(self) -> None:
        """Load and initialize adapters from stored config."""
        channels = self.store.load_channels()
        for config in channels:
            if config.enabled:
                try:
                    adapter = create_adapter(config)
                    self.adapters[config.channel_id] = adapter
                except Exception:
                    pass

    def add_channel(self, config: ChannelConfig) -> None:
        """Add a new channel configuration."""
        channels = self.store.load_channels()
        # Replace if exists
        channels = [c for c in channels if c.channel_id != config.channel_id]
        channels.append(config)
        self.store.save_channels(channels)

        # Initialize adapter
        if config.enabled:
            adapter = create_adapter(config)
            self.adapters[config.channel_id] = adapter

    def remove_channel(self, channel_id: str) -> bool:
        """Remove a channel configuration."""
        channels = self.store.load_channels()
        original = len(channels)
        channels = [c for c in channels if c.channel_id != channel_id]
        if len(channels) < original:
            self.store.save_channels(channels)
            self.adapters.pop(channel_id, None)
            return True
        return False

    def list_channels(self) -> list[dict[str, Any]]:
        """List all configured channels."""
        channels = self.store.load_channels()
        return [
            {
                "channel_id": c.channel_id,
                "platform": c.platform,
                "enabled": c.enabled,
                "has_token": bool(c.bot_token or c.webhook_url),
            }
            for c in channels
        ]

    def register_handler(self, handler: Callable[[IncomingMessage], str | None]) -> None:
        """Register a message handler function."""
        self._handlers.append(handler)

    async def send(self, channel_id: str, content: str, **kwargs) -> dict[str, Any]:
        """
        Send a message to a specific channel.

        Args:
            channel_id: Channel identifier
            content: Message content
            **kwargs: Additional options (reply_to, parse_mode, etc.)

        Returns:
            Response dict with 'ok' status
        """
        adapter = self.adapters.get(channel_id)
        if adapter is None:
            return {"ok": False, "error": f"Unknown channel: {channel_id}"}

        msg = OutgoingMessage(
            platform=adapter.platform,
            channel_id=channel_id,
            content=content,
            reply_to=kwargs.get("reply_to"),
            parse_mode=kwargs.get("parse_mode", "markdown"),
        )

        result = await adapter.send_message(msg)
        self.store.log_message(msg, direction="outgoing")
        return result

    async def broadcast(
        self,
        content: str,
        platforms: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """
        Broadcast a message to all channels (or filtered subset).

        Args:
            content: Message content
            platforms: Filter to specific platforms
            exclude: Exclude specific channel IDs

        Returns:
            Dict of channel_id -> response
        """
        results = {}
        exclude = exclude or []

        for channel_id, adapter in self.adapters.items():
            if channel_id in exclude:
                continue
            if platforms and adapter.platform not in platforms:
                continue

            msg = OutgoingMessage(
                platform=adapter.platform,
                channel_id=channel_id,
                content=content,
            )
            result = await adapter.send_message(msg)
            self.store.log_message(msg, direction="outgoing")
            results[channel_id] = result

        return results

    async def health_check(self) -> dict[str, dict[str, Any]]:
        """Check health of all configured channels."""
        results = {}
        for channel_id, adapter in self.adapters.items():
            try:
                healthy = await adapter.health_check()
                results[channel_id] = {
                    "platform": adapter.platform,
                    "healthy": healthy,
                }
            except Exception as e:
                results[channel_id] = {
                    "platform": adapter.platform,
                    "healthy": False,
                    "error": str(e),
                }
        return results

    def get_stats(self) -> dict[str, Any]:
        """Get Nexus statistics."""
        channels = self.store.load_channels()
        messages = self.store.get_message_log(100)

        platforms = {}
        for c in channels:
            platforms[c.platform] = platforms.get(c.platform, 0) + 1

        return {
            "total_channels": len(channels),
            "active_channels": len([c for c in channels if c.enabled]),
            "platforms": platforms,
            "total_messages": len(messages),
            "recent_messages": messages[-5:],
        }


# ─── CLI Entry Point ────────────────────────────────────────────

def main():
    """CLI entry point for Perisai Nexus."""
    import argparse

    parser = argparse.ArgumentParser(description="Perisai — Multi-Channel Bot Orchestrator")
    sub = parser.add_subparsers(dest="action")

    sub.add_parser("list", help="List configured channels")
    sub.add_parser("stats", help="Show Nexus statistics")
    sub.add_parser("health", help="Health check all channels")

    add_p = sub.add_parser("add", help="Add a channel")
    add_p.add_argument("platform", choices=["telegram", "discord", "slack", "signal", "matrix", "whatsapp"])
    add_p.add_argument("channel_id", help="Channel identifier")
    add_p.add_argument("--token", default="", help="Bot token")
    add_p.add_argument("--webhook", default="", help="Webhook URL")
    add_p.add_argument("--api-key", default="", help="API key")

    rm_p = sub.add_parser("remove", help="Remove a channel")
    rm_p.add_argument("channel_id", help="Channel to remove")

    send_p = sub.add_parser("send", help="Send a message")
    send_p.add_argument("channel_id", help="Target channel")
    send_p.add_argument("content", help="Message content")

    bc_p = sub.add_parser("broadcast", help="Broadcast to all channels")
    bc_p.add_argument("content", help="Message content")
    bc_p.add_argument("--platform", action="append", help="Filter by platform")

    args = parser.parse_args()
    nexus = PerisaiNexus()

    if args.action == "list":
        channels = nexus.list_channels()
        if not channels:
            print("  No channels configured.")
            print("  Use: jebat nexus add <platform> <channel_id>")
        else:
            print(f"\n📡 Channels ({len(channels)}):")
            for c in channels:
                status = "✅" if c["enabled"] and c["has_token"] else "⚠️"
                print(f"  {status} [{c['platform']}] {c['channel_id']}")

    elif args.action == "add":
        config = ChannelConfig(
            channel_id=args.channel_id,
            platform=args.platform,
            bot_token=args.token,
            webhook_url=args.webhook,
            api_key=args.api_key,
        )
        nexus.add_channel(config)
        print(f"  ✅ Added {args.platform} channel: {args.channel_id}")

    elif args.action == "remove":
        if nexus.remove_channel(args.channel_id):
            print(f"  ✅ Removed channel: {args.channel_id}")
        else:
            print(f"  ❌ Channel not found: {args.channel_id}")

    elif args.action == "send":
        import asyncio
        result = asyncio.run(nexus.send(args.channel_id, args.content))
        if result.get("ok"):
            print(f"  ✅ Message sent to {args.channel_id}")
        else:
            print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")

    elif args.action == "broadcast":
        import asyncio
        platforms = args.platform if hasattr(args, "platform") and args.platform else None
        results = asyncio.run(nexus.broadcast(args.content, platforms=platforms))
        print(f"\n📡 Broadcast to {len(results)} channels:")
        for ch, res in results.items():
            status = "✅" if res.get("ok") else "❌"
            print(f"  {status} {ch}")

    elif args.action == "health":
        import asyncio
        results = asyncio.run(nexus.health_check())
        print(f"\n🏥 Health Check:")
        for ch, info in results.items():
            status = "✅" if info["healthy"] else "❌"
            print(f"  {status} [{info['platform']}] {ch}")

    elif args.action == "stats":
        stats = nexus.get_stats()
        print(f"\n📊 Nexus Stats:")
        print(f"   Channels: {stats['active_channels']}/{stats['total_channels']}")
        print(f"   Platforms: {', '.join(f'{k}({v})' for k, v in stats['platforms'].items())}")
        print(f"   Messages: {stats['total_messages']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
