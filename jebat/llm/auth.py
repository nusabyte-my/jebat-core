"""Provider authentication status checking."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List


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
