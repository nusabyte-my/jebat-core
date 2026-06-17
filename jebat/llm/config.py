"""LLM configuration loading and management."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml


@dataclass
class JebatLLMConfig:
    provider: str = "openai"
    model: str = "gpt-5.4"
    fallback_providers: Tuple[str, ...] = ("local",)
    temperature: float = 0.2
    max_tokens: int = 4096
    timeout: int = 30


def load_llm_config(path: Optional[Path] = None) -> JebatLLMConfig:
    if path and path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return JebatLLMConfig(
                provider=data.get("provider", "openai"),
                model=data.get("model", "gpt-5.4"),
                fallback_providers=tuple(data.get("fallback_providers", ["local"])),
                temperature=data.get("temperature", 0.2),
                max_tokens=data.get("max_tokens", 4096),
                timeout=data.get("timeout", 30),
            )
        except Exception:
            pass
    return JebatLLMConfig()
