"""JEBAT Social Media Module — Pengacara (The Advocate).

Telegram Bot, X/Twitter, and Discord webhook integration.
"""

from jebat.features.social_media.social_media import (
    TelegramMessage, TelegramChat,
    telegram_send, telegram_get_updates, telegram_list_chats, telegram_send_photo,
    Tweet,
    twitter_search, twitter_post, twitter_timeline,
    discord_webhook_send,
    SOCIAL_MEDIA_TOOLS, list_social_media_tools,
)

__all__ = [
    "TelegramMessage", "TelegramChat",
    "telegram_send", "telegram_get_updates", "telegram_list_chats", "telegram_send_photo",
    "Tweet",
    "twitter_search", "twitter_post", "twitter_timeline",
    "discord_webhook_send",
    "SOCIAL_MEDIA_TOOLS", "list_social_media_tools",
]