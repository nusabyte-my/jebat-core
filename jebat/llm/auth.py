from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProviderAuthStatus:
    provider: str
    configured: bool
    env_vars: tuple[str, ...]
    notes: str


PROVIDER_ENV_MAP = {
    "openai": ("OPENAI_API_KEY",),
    "google": ("GOOGLE_API_KEY", "GEMINI_API_KEY"),
    "anthropic": ("ANTHROPIC_API_KEY",),
    "openrouter": ("OPENROUTER_API_KEY",),
    "ollama": ("OLLAMA_HOST",),
    "local": (),
}

PROVIDER_PRIORITY = (
    "openai",
    "google",
    "anthropic",
    "openrouter",
    "ollama",
    "local",
)


def get_provider_secret(provider: str) -> str:
    provider_name = provider.strip().lower()
    env_vars = PROVIDER_ENV_MAP.get(provider_name)
    if env_vars is None:
        raise RuntimeError(f"unknown provider: {provider}")
    if not env_vars:
        return ""
    for env_name in env_vars:
        value = os.getenv(env_name, "").strip()
        if value:
            return value
    raise RuntimeError(
        f"missing required environment variable for {provider_name}: one of {', '.join(env_vars)}"
    )


def list_provider_auth_status() -> list[ProviderAuthStatus]:
    statuses: list[ProviderAuthStatus] = []
    for provider, env_vars in PROVIDER_ENV_MAP.items():
        configured = True if not env_vars else any(os.getenv(name, "").strip() for name in env_vars)
        note = "Local fallback" if provider == "local" else "Configured" if configured else "Missing credentials"
        statuses.append(
            ProviderAuthStatus(
                provider=provider,
                configured=configured,
                env_vars=env_vars,
                notes=note,
            )
        )
    return statuses


def select_best_provider(preferred: str, fallbacks: tuple[str, ...] = ()) -> str:
    ordered = []
    for name in (preferred, *fallbacks, *PROVIDER_PRIORITY):
        normalized = name.strip().lower()
        if normalized and normalized not in ordered:
            ordered.append(normalized)
    status_by_provider = {item.provider: item for item in list_provider_auth_status()}
    for provider in ordered:
        status = status_by_provider.get(provider)
        if status and status.configured:
            return provider
    return "local"
