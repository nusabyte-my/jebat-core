"""
JEBAT — shared data models for providers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Protocol


@dataclass
class ProviderConfig:
    id: str
    name: str
    api_base: Optional[str] = None
    model: str = "qwen2.5-coder:7b"
    api_key: Optional[str] = None
    kind: str = "ollama"
    meta: Dict[str, Any] = field(default_factory=dict)


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
