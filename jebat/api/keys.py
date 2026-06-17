"""Shared API key validation logic for JEBAT API.

Provides:
    validate_api_key_against_redis — check a key against Redis-stored keys
    get_key_info — return metadata about the current key

This module lives between jebat.api.auth (middleware) and routers.auth (endpoints)
to break the circular import dependency.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

_REDIS_PREFIX = "jebat:auth:"
_MAX_HISTORY = 50


def _key_id(key: str) -> str:
    """Deterministic short hash of a key for identification (full SHA-256 as Redis key suffix)."""
    return hashlib.sha256(key.encode()).hexdigest()[:12]


def _key_hash(key: str) -> str:
    """Full SHA-256 hex digest for secure comparison."""
    return hashlib.sha256(key.encode()).hexdigest()


def generate_key(prefix: str = "jebat") -> str:
    """Generate a cryptographically secure API key."""
    raw = secrets.token_urlsafe(32)
    return f"{prefix}_{raw}"


async def _get_redis_client():
    """Get the Redis client, or None if unavailable."""
    try:
        from jebat.database.connection_manager import get_redis_manager
        rm = get_redis_manager()
        return rm.client
    except Exception:
        return None


async def validate_api_key_against_redis(provided_key: str) -> bool:
    """Check if a key is valid against Redis-stored keys.

    Checks in order:
    1. Redis current key (jebat:auth:current_key) — compared via full SHA-256 hash
    2. Grace-period deprecated keys (jebat:auth:grace:{key_id}) — value is the hash, compared

    Returns True if the key matches any valid stored key.
    """
    client = await _get_redis_client()
    if client is None:
        return False

    try:
        provided_hash = _key_hash(provided_key)

        # 1. Check current active key
        current_stored = await client.get(f"{_REDIS_PREFIX}current_key")
        if current_stored and secrets.compare_digest(provided_hash, current_stored):
            return True

        # 2. Check grace-period keys
        kid = _key_id(provided_key)
        grace_stored = await client.get(f"{_REDIS_PREFIX}grace:{kid}")
        if grace_stored and secrets.compare_digest(provided_hash, grace_stored):
            return True

    except Exception as exc:
        logger.warning("Redis key validation error: %s", exc)

    return False


async def get_key_info() -> dict[str, Any]:
    """Return metadata about the current key (never exposes the key itself)."""
    client = await _get_redis_client()
    if client is None:
        return {"status": "unavailable", "reason": "Redis not connected"}

    try:
        current_hash = await client.get(f"{_REDIS_PREFIX}current_key")
        if not current_hash:
            return {
                "key_id": "none",
                "created_at": "unknown",
                "rotated_count": 0,
                "grace_keys_active": 0,
                "env_key_active": bool(os.getenv("JEBAT_API_KEY")),
            }

        # Count grace-period keys
        grace_keys = 0
        cursor = 0
        pattern = f"{_REDIS_PREFIX}grace:*"
        while True:
            cursor, keys = await client.scan(cursor=cursor, match=pattern, count=100)
            grace_keys += len(keys)
            if cursor == 0:
                break

        history_len = await client.llen(f"{_REDIS_PREFIX}history")

        return {
            "key_id": current_hash[:12],
            "created_at": await client.get(f"{_REDIS_PREFIX}created_at") or "unknown",
            "rotated_count": history_len,
            "grace_keys_active": grace_keys,
            "env_key_active": bool(os.getenv("JEBAT_API_KEY")),
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


async def store_new_key(new_key: str) -> None:
    """Store the new current key (as SHA-256 hash) in Redis."""
    client = await _get_redis_client()
    if client is None:
        raise RuntimeError("Redis not available")

    key_hash = _key_hash(new_key)
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    await client.set(f"{_REDIS_PREFIX}current_key", key_hash)
    await client.set(f"{_REDIS_PREFIX}created_at", now_iso)


async def deprecate_old_key(old_key: str, grace_ttl: int) -> None:
    """Move the old key to grace period with TTL."""
    client = await _get_redis_client()
    if client is None:
        return

    old_hash = _key_hash(old_key)
    kid = _key_id(old_key)
    # Store the hash as value so we can compare on validation
    await client.set(f"{_REDIS_PREFIX}grace:{kid}", old_hash, ex=grace_ttl)


async def log_rotation(old_key_id: Optional[str], new_key_id: str, grace_ttl: int) -> None:
    """Log a rotation event to the history list."""
    client = await _get_redis_client()
    if client is None:
        return

    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    event = json.dumps({
        "ts": now_iso,
        "old_key_id": old_key_id,
        "new_key_id": new_key_id,
        "grace_ttl": grace_ttl,
    })
    await client.lpush(f"{_REDIS_PREFIX}history", event)
    await client.ltrim(f"{_REDIS_PREFIX}history", 0, _MAX_HISTORY - 1)


async def check_rate_limit(max_per_hour: int = 10) -> bool:
    """Check rotation rate limit. Returns True if allowed, False if exceeded."""
    client = await _get_redis_client()
    if client is None:
        return True  # Allow if Redis is down

    try:
        rate_key = f"{_REDIS_PREFIX}rotate_rate"
        count = await client.incr(rate_key)
        if count == 1:
            await client.expire(rate_key, 3600)
        return count <= max_per_hour
    except Exception:
        return True


async def revoke_grace_key(key_id: str) -> bool:
    """Immediately delete a grace-period key from Redis.

    Args:
        key_id: The key_id (first 12 hex chars of SHA-256) of the grace key to revoke.

    Returns:
        True if the key was found and deleted, False otherwise.
    """
    client = await _get_redis_client()
    if client is None:
        return False

    grace_key = f"{_REDIS_PREFIX}grace:{key_id}"
    deleted = await client.delete(grace_key)
    return deleted > 0


async def revoke_all_grace_keys() -> int:
    """Immediately delete all grace-period keys from Redis.

    Returns:
        Number of keys revoked.
    """
    client = await _get_redis_client()
    if client is None:
        return 0

    grace_keys: list[str] = []
    cursor = 0
    pattern = f"{_REDIS_PREFIX}grace:*"
    while True:
        cursor, keys = await client.scan(cursor=cursor, match=pattern, count=100)
        grace_keys.extend(keys)
        if cursor == 0:
            break

    if not grace_keys:
        return 0

    deleted = await client.delete(*grace_keys)
    return deleted


async def log_revocation(key_id: Optional[str], count: int) -> None:
    """Log a revocation event to the history list for audit trail."""
    client = await _get_redis_client()
    if client is None:
        return

    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    event = json.dumps({
        "ts": now_iso,
        "type": "revoke",
        "key_id": key_id,
        "revoked_count": count,
    })
    await client.lpush(f"{_REDIS_PREFIX}history", event)
    await client.ltrim(f"{_REDIS_PREFIX}history", 0, _MAX_HISTORY - 1)
