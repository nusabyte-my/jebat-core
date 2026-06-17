"""Provider authentication status checking."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

# ── Secrets env loading ────────────────────────────────────────────────────

_secrets_loaded = False


def _ensure_secrets_loaded() -> None:
    """Load ~/.jebat/secrets.env into os.environ once per process.

    Called automatically by get_provider_secret and list_provider_auth_status,
    so any code that checks provider keys automatically picks up secrets.env.
    Also safe to call explicitly (idempotent).
    """
    global _secrets_loaded
    if _secrets_loaded:
        return
    _secrets_loaded = True

    candidates = [
        Path.home() / ".jebat" / "secrets.env",
        Path.cwd() / ".env",
    ]
    env_path = None
    for p in candidates:
        if p.exists():
            env_path = p
            break
    if env_path is None:
        return

    try:
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("'\"")
                if key and value and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        pass


# ── Provider auth store (webui / container paths) ──────────────────────────

@dataclass
class ProviderAuthStatus:
    provider: str
    configured: bool
    key_env_var: str = ""


def list_provider_auth_status() -> List[ProviderAuthStatus]:
    providers = [
        ProviderAuthStatus(provider="openai", configured=bool(os.getenv("OPENAI_API_KEY")), key_env_var="OPENAI_API_KEY"),
        ProviderAuthStatus(provider="google", configured=bool(os.getenv("GOOGLE_API_KEY")), key_env_var="GOOGLE_API_KEY"),
        ProviderAuthStatus(provider="anthropic", configured=bool(os.getenv("ANTHROPIC_API_KEY")), key_env_var="ANTHROPIC_API_KEY"),
        ProviderAuthStatus(provider="openrouter", configured=bool(os.getenv("OPENROUTER_API_KEY")), key_env_var="OPENROUTER_API_KEY"),
        ProviderAuthStatus(provider="ollama", configured=bool(os.getenv("OLLAMA_HOST")), key_env_var="OLLAMA_HOST"),
        ProviderAuthStatus(provider="local", configured=True, key_env_var=""),
    ]
    return providers
