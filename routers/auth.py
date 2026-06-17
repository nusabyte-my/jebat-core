"""Auth key management endpoints for JEBAT API.

Provides:
    POST /api/auth/rotate-key — Generate a new API key, deprecate the old one
    GET  /api/auth/key-info   — Show current key metadata (never the key itself)
"""

from __future__ import annotations

import logging
import os
import secrets
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from jebat.api.keys import (
    check_rate_limit,
    generate_key,
    get_key_info,
    log_rotation,
    revoke_all_grace_keys,
    revoke_grace_key,
    store_new_key,
    validate_api_key_against_redis,
    _key_id,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)

_DEFAULT_GRACE_TTL = 86400  # 24 hours


class RotateKeyRequest(BaseModel):
    grace_period_seconds: int = Field(
        default=_DEFAULT_GRACE_TTL,
        ge=300,
        le=604800,
        description="How long the old key remains valid (5 min – 7 days). Default: 86400 (24h).",
    )
    prefix: str = Field(
        default="jebat",
        min_length=2,
        max_length=16,
        description="Key prefix for identification. Default: 'jebat'.",
    )


class RotateKeyResponse(BaseModel):
    new_key: str
    key_id: str
    old_key_id: Optional[str] = None
    grace_period_seconds: int
    message: str


class KeyInfoResponse(BaseModel):
    key_id: str
    created_at: str
    rotated_count: int
    grace_keys_active: int
    env_key_active: bool


class RevokeKeyRequest(BaseModel):
    key_id: Optional[str] = Field(
        default=None,
        description="Key ID (first 12 hex chars) of the grace key to revoke. Omit to revoke all grace keys.",
    )


class RevokeKeyResponse(BaseModel):
    revoked: bool
    key_id: Optional[str] = None
    revoked_count: int
    message: str


async def _authenticate_request(
    authorization: Optional[str], x_api_key: Optional[str]
) -> str:
    """Authenticate the caller with the current valid key. Returns the key or raises."""
    from jebat.api.auth import _extract_bearer_token

    provided_key = _extract_bearer_token(authorization) or x_api_key
    if not provided_key:
        raise HTTPException(status_code=401, detail="API key required to rotate")

    env_key = os.getenv("JEBAT_API_KEY", "")
    if env_key and secrets.compare_digest(provided_key, env_key):
        return provided_key

    if await validate_api_key_against_redis(provided_key):
        return provided_key

    logger.warning("Failed rotation attempt with invalid key")
    raise HTTPException(status_code=403, detail="Invalid API key — cannot rotate")


@router.post("/rotate-key", response_model=RotateKeyResponse)
async def rotate_api_key(
    req: RotateKeyRequest,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> RotateKeyResponse:
    """Generate a new API key and deprecate the old one.

    The old key remains valid for the grace period (default 24h) so existing
    clients can transition. Requires the current valid key to authenticate.

    Rate-limited: maximum 10 rotations per hour.
    """
    # --- Authenticate ---
    provided_key = await _authenticate_request(authorization, x_api_key)

    # --- Rate limit ---
    if not await check_rate_limit():
        raise HTTPException(status_code=429, detail="Rate limit exceeded — max 10 rotations per hour")

    # --- Get old key info before rotating ---
    from jebat.api.keys import _get_redis_client, _REDIS_PREFIX
    client = await _get_redis_client()
    if client is None:
        raise HTTPException(status_code=503, detail="Redis not available — key rotation requires Redis")

    old_hash = await client.get(f"{_REDIS_PREFIX}current_key")
    old_key_id = old_hash[:12] if old_hash else None

    # --- Generate new key and store ---
    new_key = generate_key(req.prefix)
    new_key_id = _key_id(new_key)

    # Store new key as hash
    await store_new_key(new_key)

    # Deprecate old key with grace period
    # We need the raw old key to deprecate, but we only have the hash.
    # Since we can't reverse the hash, we store a grace entry using the
    # new key's ID and trust that the middleware validates against the hash.
    # Actually, we need to reconstruct: the old key was stored as hash.
    # For grace period, we store the hash directly under a grace key.
    if old_hash:
        await client.set(f"{_REDIS_PREFIX}grace:{old_key_id}", old_hash, ex=req.grace_period_seconds)

    # Log rotation
    await log_rotation(old_key_id, new_key_id, req.grace_period_seconds)

    logger.info("API key rotated: %s -> %s (grace: %ds)", old_key_id, new_key_id, req.grace_period_seconds)

    return RotateKeyResponse(
        new_key=new_key,
        key_id=new_key_id,
        old_key_id=old_key_id,
        grace_period_seconds=req.grace_period_seconds,
        message=f"Key rotated. Old key valid for {req.grace_period_seconds}s (grace period). Update your clients with the new key.",
    )


@router.get("/key-info", response_model=KeyInfoResponse)
async def get_current_key_info() -> dict:
    """Show metadata about the current API key (never exposes the key itself).

    Returns key_id, creation time, rotation count, grace-period keys active,
    and whether an env var key is also configured.
    """
    return await get_key_info()


@router.post("/revoke-key", response_model=RevokeKeyResponse)
async def revoke_key(
    req: RevokeKeyRequest,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> RevokeKeyResponse:
    """Immediately revoke grace-period API key(s) without waiting for TTL expiry.

    Use this for emergency key revocation — if a key is compromised, revoke it
    immediately instead of waiting for the grace period to expire.

    Provide `key_id` to revoke a single grace key, or omit it to revoke all
    grace-period keys at once. Requires the current valid key to authenticate.
    """
    await _authenticate_request(authorization, x_api_key)

    if req.key_id:
        revoked = await revoke_grace_key(req.key_id)
        if revoked:
            logger.info("Revoked grace key: %s", req.key_id)
            return RevokeKeyResponse(
                revoked=True,
                key_id=req.key_id,
                revoked_count=1,
                message=f"Grace key {req.key_id} revoked immediately.",
            )
        raise HTTPException(status_code=404, detail=f"No grace key found with id {req.key_id}")
    else:
        count = await revoke_all_grace_keys()
        logger.info("Revoked all %d grace keys", count)
        return RevokeKeyResponse(
            revoked=count > 0,
            revoked_count=count,
            message=f"Revoked {count} grace key(s)." if count > 0 else "No grace keys to revoke.",
        )
