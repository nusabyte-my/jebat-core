"""System status, health, and LLM provider endpoints."""

from __future__ import annotations

import time
from typing import Any, Dict

from fastapi import APIRouter

from jebat.llm.auth import list_provider_auth_status
from jebat.llm.config import load_llm_config
from jebat.llm.providers import list_supported_providers

router = APIRouter(prefix="/api", tags=["status"])

_START_TIME = time.time()


@router.get("/status")
async def system_status() -> Dict[str, Any]:
    """Full system status including uptime, version, and provider info."""
    config = load_llm_config()
    providers = list_provider_auth_status()
    return {
        "service": "jebat-api",
        "version": "6.1.0",
        "status": "running",
        "uptime_s": round(time.time() - _START_TIME, 1),
        "llm": {
            "provider": config.provider,
            "model": config.model,
            "fallback_providers": list(config.fallback_providers),
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        },
        "providers": [
            {"name": p.provider, "configured": p.configured, "key_env_var": p.key_env_var}
            for p in providers
        ],
    }


@router.get("/providers")
async def get_providers() -> Dict[str, Any]:
    """List all supported LLM providers and their auth status."""
    supported = list_supported_providers()
    auth = list_provider_auth_status()
    auth_set = {a.provider: a.configured for a in auth}
    return {
        "providers": [
            {"name": s["name"], "description": s["description"], "configured": auth_set.get(s["name"], False)}
            for s in supported
        ],
    }


@router.get("/config/llm")
async def get_llm_config() -> Dict[str, Any]:
    """Current LLM configuration."""
    config = load_llm_config()
    return {
        "provider": config.provider,
        "model": config.model,
        "fallback_providers": list(config.fallback_providers),
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "timeout": config.timeout,
    }
