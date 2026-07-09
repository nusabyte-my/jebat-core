"""
JEBAT — shared data models for providers.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Protocol


@dataclass
class ProviderConfig:
    id: str
    name: str
    api_base: Optional[str] = None
    model: str = "qwen2.5-coder:7b"
    api_key: Optional[str] = None
    kind: str = "ollama"
    # Auth: how the API key is supplied.
    #   "key"   -> inline `api_key` (paste it)
    #   "env"   -> read from environment variable named `auth_ref`
    #   "store" -> look up a named key in ~/.jebat/auth/tokens.json (`auth_ref`)
    auth_method: str = "key"
    auth_ref: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


def resolve_api_key(cfg) -> str:
    """Resolve the effective API key for a provider config.

    Supports inline key, environment variable, or the named-key auth store.
    Works with both the models.ProviderConfig and the inline REPL ProviderConfig
    (duck-typed via getattr).
    """
    method = getattr(cfg, "auth_method", "key") or "key"
    ref = getattr(cfg, "auth_ref", None)
    inline = getattr(cfg, "api_key", None)
    if method == "env":
        return os.environ.get(ref, "") if ref else ""
    if method == "store":
        if ref:
            try:
                path = Path.home() / ".jebat" / "auth" / "tokens.json"
                data = json.loads(path.read_text(encoding="utf-8"))
                return data.get("api_keys", {}).get(ref, {}).get("key", "") or ""
            except Exception:
                return ""
        return ""
    return inline or ""


@dataclass
class CompletionRequest:
    provider: str
    model: str
    prompt: str
    temperature: float = 0.2
    max_tokens: int = 4096
    stream: bool = False
    tools: bool = False


@dataclass
class CompletionResponse:
    text: str
    model: str
    provider: str
    tokens_used: int = 0
    latency_ms: int = 0


class Provider(Protocol):
    def complete(self, request: CompletionRequest) -> CompletionResponse:
        ...
