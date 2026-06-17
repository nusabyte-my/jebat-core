"""JEBAT Social Media Module — Pengacara (The Advocate).

Social media integration for NusaByte marketing and community:
  - Telegram Bot API (send, receive, manage groups)
  - X/Twitter API (tweet, search, timeline)
  - LinkedIn (future — post articles)
  - Discord (future — webhook posting)

Safety: All posting tools require CONFIRM tier.
        Read-only tools (search, timeline) are AUTO tier.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx


# ── Telegram Bot ──────────────────────────────────────────────────────────

@dataclass(slots=True)
class TelegramMessage:
    chat_id: int | str
    text: str
    message_id: int = 0
    from_user: str = ""
    date: str = ""
    reply_to: int = 0


@dataclass(slots=True)
class TelegramChat:
    chat_id: int | str
    title: str = ""
    type: str = ""  # private, group, supergroup, channel
    username: str = ""


async def telegram_send(
    chat_id: int | str,
    text: str,
    api_token: str | None = None,
    parse_mode: str = "Markdown",
    reply_to: int | None = None,
    silent: bool = False,
) -> TelegramMessage:
    """Send a message via Telegram Bot API.

    Safety: CONFIRM (posts content externally)

    Args:
        chat_id: Target chat ID or @username
        text: Message text (supports Markdown/HTML)
        api_token: Bot token (default: TELEGRAM_BOT_TOKEN env)
        parse_mode: Markdown, HTML, or empty string
        reply_to: Message ID to reply to
        silent: Send without notification
    """
    token = api_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set. Create a bot via @BotFather.")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_notification": silent,
    }
    if reply_to:
        payload["reply_to_message_id"] = reply_to

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()

    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data.get('description', 'unknown')}")

    msg = data["result"]
    return TelegramMessage(
        chat_id=msg["chat"]["id"],
        text=msg["text"],
        message_id=msg["message_id"],
        from_user=msg.get("from", {}).get("username", ""),
        date=str(msg.get("date", "")),
        reply_to=msg.get("reply_to_message", {}).get("message_id", 0) if "reply_to_message" in msg else 0,
    )


async def telegram_get_updates(
    api_token: str | None = None,
    offset: int = 0,
    limit: int = 100,
    timeout: int = 0,
) -> list[TelegramMessage]:
    """Get recent messages/updates from Telegram Bot.

    Safety: AUTO (read-only)
    """
    token = api_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set.")

    url = f"https://api.telegram.org/bot{token}/getUpdates"
    params = {"offset": offset, "limit": limit, "timeout": timeout}

    async with httpx.AsyncClient(timeout=timeout + 10) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()

    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data.get('description', 'unknown')}")

    messages: list[TelegramMessage] = []
    for update in data.get("result", []):
        if "message" in update:
            msg = update["message"]
            messages.append(TelegramMessage(
                chat_id=msg["chat"]["id"],
                text=msg.get("text", ""),
                message_id=msg["message_id"],
                from_user=msg.get("from", {}).get("username", ""),
                date=str(msg.get("date", "")),
            ))

    return messages


async def telegram_list_chats(
    api_token: str | None = None,
) -> list[TelegramChat]:
    """List all chats the bot is in.

    Safety: AUTO (read-only)
    """
    updates = await telegram_get_updates(api_token=api_token, limit=100)
    chats: dict[int, TelegramChat] = {}

    # Extract chat info from updates
    token = api_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url, params={"limit": 100})
        data = response.json()

    for update in data.get("result", []):
        if "message" in update:
            chat = update["message"]["chat"]
            cid = chat["id"]
            if cid not in chats:
                chats[cid] = TelegramChat(
                    chat_id=cid,
                    title=chat.get("title", ""),
                    type=chat.get("type", ""),
                    username=chat.get("username", ""),
                )

    return list(chats.values())


async def telegram_send_photo(
    chat_id: int | str,
    photo_url: str,
    caption: str = "",
    api_token: str | None = None,
) -> TelegramMessage:
    """Send a photo via Telegram Bot API.

    Safety: CONFIRM (posts content externally)
    """
    token = api_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set.")

    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    payload = {"chat_id": chat_id, "photo": photo_url}
    if caption:
        payload["caption"] = caption

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()

    data = response.json()
    msg = data["result"]
    return TelegramMessage(
        chat_id=msg["chat"]["id"],
        text=caption,
        message_id=msg["message_id"],
    )


# ── X/Twitter ─────────────────────────────────────────────────────────────

@dataclass(slots=True)
class Tweet:
    tweet_id: str
    text: str
    author: str
    created_at: str
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    url: str = ""


async def twitter_search(
    query: str,
    limit: int = 10,
    api_key: str | None = None,
    api_secret: str | None = None,
    access_token: str | None = None,
    access_secret: str | None = None,
) -> list[Tweet]:
    """Search tweets on X/Twitter.

    Safety: AUTO (read-only search)

    Requires: Twitter API v2 credentials (env vars or explicit)
    """
    bearer = api_key or os.getenv("TWITTER_BEARER_TOKEN", "")
    if not bearer:
        raise ValueError("TWITTER_BEARER_TOKEN not set. Get one from developer.x.com.")

    url = "https://api.twitter.com/2/tweets/search/recent"
    params = {
        "query": query,
        "max_results": min(limit, 100),
        "tweet.fields": "created_at,public_metrics,author_id",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(
            url, params=params,
            headers={"Authorization": f"Bearer {bearer}"},
        )
        response.raise_for_status()

    data = response.json()
    tweets: list[Tweet] = []

    for tweet_data in data.get("data", []):
        metrics = tweet_data.get("public_metrics", {})
        tweets.append(Tweet(
            tweet_id=tweet_data["id"],
            text=tweet_data["text"],
            author=tweet_data.get("author_id", ""),
            created_at=tweet_data.get("created_at", ""),
            likes=metrics.get("like_count", 0),
            retweets=metrics.get("retweet_count", 0),
            replies=metrics.get("reply_count", 0),
            url=f"https://x.com/i/status/{tweet_data['id']}",
        ))

    return tweets[:limit]


async def twitter_post(
    text: str,
    api_key: str | None = None,
    api_secret: str | None = None,
    access_token: str | None = None,
    access_secret: str | None = None,
) -> Tweet:
    """Post a tweet on X/Twitter.

    Safety: CONFIRM (posts content externally)

    Requires: Twitter OAuth 1.0a credentials for posting
    """
    # Twitter v2 posting requires OAuth 1.0a which is complex
    # For now, provide a structured placeholder that can be filled in
    key = api_key or os.getenv("TWITTER_API_KEY", "")
    secret = api_secret or os.getenv("TWITTER_API_SECRET", "")
    token = access_token or os.getenv("TWITTER_ACCESS_TOKEN", "")
    token_secret = access_secret or os.getenv("TWITTER_ACCESS_SECRET", "")

    if not all([key, secret, token, token_secret]):
        raise ValueError(
            "Twitter OAuth credentials not set. Required env vars:\n"
            "  TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET"
        )

    # Use Twitter API v2 with OAuth 1.0a
    # Note: This requires oauth1 signature generation
    # Simplified version using httpx with pre-signed headers
    url = "https://api.twitter.com/2/tweets"

    # For proper OAuth 1.0a signing, we'd need authlib or requests_oauthlib
    # This is a placeholder that will work once oauth signing is added
    try:
        from authlib.integrations.httpx_client import OAuth1ClientAsync
        async with OAuth1ClientAsync(
            key, secret, token, token_secret,
        ) as client:
            response = await client.post(url, json={"text": text})
            response.raise_for_status()

        data = response.json()
        tweet_data = data.get("data", {})
        return Tweet(
            tweet_id=tweet_data.get("id", ""),
            text=tweet_data.get("text", text),
            author="",
            created_at=datetime.now().isoformat(),
            url=f"https://x.com/i/status/{tweet_data.get('id', '')}",
        )
    except ImportError:
        raise RuntimeError(
            "authlib not installed. Install with: pip install authlib\n"
            "Or use the Twitter API directly with OAuth 1.0a signing."
        )


async def twitter_timeline(
    username: str,
    limit: int = 10,
    bearer_token: str | None = None,
) -> list[Tweet]:
    """Get recent tweets from a user's timeline.

    Safety: AUTO (read-only)
    """
    bearer = bearer_token or os.getenv("TWITTER_BEARER_TOKEN", "")
    if not bearer:
        raise ValueError("TWITTER_BEARER_TOKEN not set.")

    # First get user ID
    user_url = f"https://api.twitter.com/2/users/by/username/{username}"
    async with httpx.AsyncClient(timeout=15) as client:
        user_resp = await client.get(
            user_url,
            headers={"Authorization": f"Bearer {bearer}"},
        )
        user_resp.raise_for_status()

    user_data = user_resp.json().get("data", {})
    user_id = user_data.get("id", "")

    if not user_id:
        raise ValueError(f"User @{username} not found on Twitter")

    # Get tweets
    tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
    params = {
        "max_results": min(limit, 100),
        "tweet.fields": "created_at,public_metrics",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        tweets_resp = await client.get(
            tweets_url, params=params,
            headers={"Authorization": f"Bearer {bearer}"},
        )
        tweets_resp.raise_for_status()

    tweets: list[Tweet] = []
    for tweet_data in tweets_resp.json().get("data", []):
        metrics = tweet_data.get("public_metrics", {})
        tweets.append(Tweet(
            tweet_id=tweet_data["id"],
            text=tweet_data["text"],
            author=username,
            created_at=tweet_data.get("created_at", ""),
            likes=metrics.get("like_count", 0),
            retweets=metrics.get("retweet_count", 0),
            url=f"https://x.com/{username}/status/{tweet_data['id']}",
        ))

    return tweets[:limit]


# ── Discord Webhook (simple posting) ──────────────────────────────────────

async def discord_webhook_send(
    webhook_url: str,
    content: str,
    username: str = "JEBAT",
    embed_title: str | None = None,
    embed_description: str | None = None,
    embed_color: int = 0x5865F2,  # Discord blurple
) -> dict[str, Any]:
    """Send a message via Discord webhook.

    Safety: CONFIRM (posts content externally)
    """
    payload: dict[str, Any] = {
        "username": username,
        "content": content,
    }

    if embed_title:
        payload["embeds"] = [{
            "title": embed_title,
            "description": embed_description or "",
            "color": embed_color,
        }]

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(webhook_url, json=payload)
        response.raise_for_status()

    return {"status": "sent", "webhook": webhook_url.split("?")[0]}


# ── Tool Registry (map for discovery, actual registration below) ───────────

SOCIAL_MEDIA_TOOLS: dict[str, dict[str, Any]] = {
    "telegram_send": {
        "description": "Send a message via Telegram Bot API",
        "safety": "confirm",
        "handler": telegram_send,
        "parameters": {
            "chat_id": {"type": "string", "description": "Target chat ID or @username"},
            "text": {"type": "string", "description": "Message text (Markdown supported)"},
            "parse_mode": {"type": "string", "description": "Markdown, HTML, or empty"},
        },
    },
    "telegram_get_updates": {
        "description": "Get recent messages/updates from Telegram Bot",
        "safety": "auto",
        "handler": telegram_get_updates,
        "parameters": {"limit": {"type": "integer", "description": "Max updates to fetch"}},
    },
    "telegram_list_chats": {
        "description": "List all chats the Telegram bot is in",
        "safety": "auto",
        "handler": telegram_list_chats,
        "parameters": {},
    },
    "telegram_send_photo": {
        "description": "Send a photo via Telegram Bot API",
        "safety": "confirm",
        "handler": telegram_send_photo,
        "parameters": {
            "chat_id": {"type": "string"},
            "photo_url": {"type": "string"},
            "caption": {"type": "string"},
        },
    },
    "twitter_search": {
        "description": "Search tweets on X/Twitter",
        "safety": "auto",
        "handler": twitter_search,
        "parameters": {"query": {"type": "string"}, "limit": {"type": "integer"}},
    },
    "twitter_post": {
        "description": "Post a tweet on X/Twitter",
        "safety": "confirm",
        "handler": twitter_post,
        "parameters": {"text": {"type": "string"}},
    },
    "twitter_timeline": {
        "description": "Get recent tweets from a user's timeline",
        "safety": "auto",
        "handler": twitter_timeline,
        "parameters": {"username": {"type": "string"}, "limit": {"type": "integer"}},
    },
    "discord_webhook_send": {
        "description": "Send a message via Discord webhook",
        "safety": "confirm",
        "handler": discord_webhook_send,
        "parameters": {
            "webhook_url": {"type": "string"},
            "content": {"type": "string"},
            "username": {"type": "string"},
        },
    },
}


def list_social_media_tools() -> list[dict[str, str]]:
    """List all available social media tools."""
    return [
        {"name": name, "description": info["description"], "safety": info["safety"]}
        for name, info in SOCIAL_MEDIA_TOOLS.items()
    ]


# ── Agent Tool Registration (auto-loaded by _ensure_tools_imported) ───────
#
# Registers all social media functions as agent-callable tools.
# Registration happens at import time — no need for manual init.

from jebat.tools import register_tool as _register

_register(
    "telegram_send",
    handler=telegram_send,
    schema={
        "type": "object",
        "properties": {
            "chat_id": {"type": "string", "description": "Target chat ID or @username"},
            "text": {"type": "string", "description": "Message text (Markdown supported)"},
            "parse_mode": {"type": "string", "default": "Markdown", "description": "Markdown, HTML, or empty"},
            "silent": {"type": "boolean", "default": False, "description": "Send without notification"},
        },
        "required": ["chat_id", "text"],
    },
    safety_tier="confirm",
    timeout=15,
    description="Send a message via Telegram Bot API. Requires TELEGRAM_BOT_TOKEN env var.",
)

_register(
    "telegram_read",
    handler=telegram_get_updates,
    schema={
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "default": 50, "description": "Max updates to fetch"},
        },
    },
    safety_tier="auto",
    timeout=15,
    description="Read recent messages from the Telegram bot.",
)

_register(
    "twitter_search",
    handler=twitter_search,
    schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "limit": {"type": "integer", "default": 10, "description": "Max results"},
        },
        "required": ["query"],
    },
    safety_tier="auto",
    timeout=15,
    description="Search tweets on X/Twitter. Requires TWITTER_BEARER_TOKEN env var.",
)

_register(
    "twitter_post",
    handler=twitter_post,
    schema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Tweet text (max 280 chars)"},
        },
        "required": ["text"],
    },
    safety_tier="confirm",
    timeout=30,
    description="Post a tweet on X/Twitter. Requires full OAuth credentials.",
)

_register(
    "twitter_timeline",
    handler=twitter_timeline,
    schema={
        "type": "object",
        "properties": {
            "username": {"type": "string", "description": "Twitter username (without @)"},
            "limit": {"type": "integer", "default": 10, "description": "Max tweets"},
        },
        "required": ["username"],
    },
    safety_tier="auto",
    timeout=15,
    description="Get recent tweets from a user's timeline. Requires TWITTER_BEARER_TOKEN env var.",
)

_register(
    "discord_send",
    handler=discord_webhook_send,
    schema={
        "type": "object",
        "properties": {
            "webhook_url": {"type": "string", "description": "Discord webhook URL"},
            "content": {"type": "string", "description": "Message content"},
            "username": {"type": "string", "default": "JEBAT", "description": "Bot display name"},
            "embed_title": {"type": "string", "description": "Optional embed title"},
            "embed_description": {"type": "string", "description": "Optional embed description"},
        },
        "required": ["webhook_url", "content"],
    },
    safety_tier="confirm",
    timeout=15,
    description="Send a message to Discord via webhook URL.",
)


# ── Unified send_message (the one tool agents actually use) ───────────────

async def send_message(
    target: str,
    message: str,
    platform: str = "telegram",
) -> dict[str, Any]:
    """Send a message to a messaging platform.

    Routes to the correct platform handler based on the 'platform' argument.

    Args:
        target: Destination identifier:
            - Telegram: chat_id (e.g. '-1001234567890') or @username
            - Twitter: tweet text (same as message)
            - Discord: webhook URL
        message: The message text to send.
        platform: 'telegram', 'twitter', or 'discord'.
    """
    if platform == "telegram":
        result = await telegram_send(chat_id=target, text=message)
        return {
            "status": "sent",
            "platform": "telegram",
            "chat_id": result.chat_id,
            "message_id": result.message_id,
        }
    elif platform == "twitter":
        result = await twitter_post(text=message)
        return {
            "status": "sent",
            "platform": "twitter",
            "tweet_id": result.tweet_id,
            "url": result.url,
        }
    elif platform == "discord":
        result = await discord_webhook_send(webhook_url=target, content=message)
        return {
            "status": "sent",
            "platform": "discord",
            **result,
        }
    else:
        return {"status": "error", "error": f"Unknown platform: {platform}. Use telegram, twitter, or discord."}


_register(
    "send_message",
    handler=send_message,
    schema={
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "The message text to send."},
            "target": {"type": "string", "description": "Destination: Telegram chat ID, Discord webhook URL, or 'self' for Twitter."},
            "platform": {
                "type": "string",
                "enum": ["telegram", "twitter", "discord"],
                "default": "telegram",
                "description": "Platform to deliver to.",
            },
        },
        "required": ["message", "target"],
    },
    safety_tier="confirm",
    timeout=30,
    description="Send a message to Telegram, X/Twitter, or Discord. "
                "The agent uses this to deliver results, notifications, or status updates.",
)