"""
JEBAT — provider registry and factory.

Supported providers:
- ollama
- openai
- anthropic
- gemini
- github
"""

from __future__ import annotations

import json
import os
from typing import Dict, Optional, Type

from jebat_cli_new.models import ProviderConfig, Provider
from jebat_cli_new.runner import ollama_complete
from jebat_cli_new.provider_openai import OpenAIProviderImpl
from jebat_cli_new.provider_anthropic import AnthropicProviderImpl
from jebat_cli_new.provider_gemini import GeminiProviderImpl
from jebat_cli_new.provider_github import GitHubModelsProviderImpl


class OllamaProviderImpl:
    def __init__(self, config: Optional[ProviderConfig] = None):
        self.config = config or ProviderConfig(id="ollama", name="Ollama", api_base="http://127.0.0.1:11434", kind="ollama")

    def complete(self, request):
        text, latency_ms = ollama_complete(
            model=request.model,
            prompt=request.prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            host=self.config.api_base or "http://127.0.0.1:11434",
        )
        return type(
            "obj",
            (object,),
            {
                "text": text,
                "model": request.model,
                "provider": "ollama",
                "tokens_used": 0,
                "latency_ms": latency_ms,
            },
        )()


def _default_api_base(kind: str) -> str:
    return {
        "ollama": "http://127.0.0.1:11434",
        "openai": "https://api.openai.com/v1",
        "anthropic": "https://api.anthropic.com",
        "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
        "github": "https://models.github.ai/inference",
    }.get(kind, "")


def _default_model(kind: str) -> str:
    return {
        "ollama": "qwen2.5-coder:7b",
        "openai": "gpt-4o-mini",
        "anthropic": "claude-sonnet-4-20250514",
        "gemini": "gemini-2.5-pro",
        "github": "openai/gpt-4o-mini",
    }.get(kind, "")


def _provider_factory(config: ProviderConfig, kind: Optional[str] = None):
    kind = (kind or config.kind or "ollama").lower()
    if kind == "ollama":
        return OllamaProviderImpl(config)
    if kind == "openai":
        return OpenAIProviderImpl(config)
    if kind == "anthropic":
        return AnthropicProviderImpl(config)
    if kind == "gemini":
        return GeminiProviderImpl(config)
    if kind == "github":
        return GitHubModelsProviderImpl(config)

    class AnyProvider:
        def __init__(self, cfg: ProviderConfig):
            self.cfg = cfg

        def complete(self, request):
            return type(
                "obj",
                (object,),
                {
                    "text": f"[{self.cfg.id}] {request.prompt[:80]}... (placeholder provider)",
                    "model": request.model,
                    "provider": self.cfg.id,
                    "tokens_used": 0,
                    "latency_ms": 0,
                },
            )()

    return AnyProvider(config)


class ProviderRegistry:
    def __init__(self, path: Optional[str] = None):
        root = os.path.expanduser("~/.jebat")
        os.makedirs(root, exist_ok=True)
        self.path = path or os.path.join(root, "jebat-cli-providers.json")
        self.providers: Dict[str, Type[Provider]] = {}
        self.configs: Dict[str, ProviderConfig] = {}
        self._load()
        # Ensure ollama is always registered
        if "ollama" not in self.configs:
            self.configs["ollama"] = ProviderConfig(
                id="ollama", name="Ollama", api_base="http://127.0.0.1:11434",
                model="qwen2.5-coder:7b", kind="ollama"
            )
        if "ollama" not in self.providers:
            self.providers["ollama"] = OllamaProviderImpl(self.configs["ollama"])

    def _load(self):
        if not os.path.exists(self.path):
            return
        try:
            data = json.load(open(self.path, "r", encoding="utf-8"))
        except Exception:
            return
        for item in data:
            try:
                cfg = ProviderConfig(**item)
            except Exception:
                continue
            self.configs[cfg.id] = cfg
            self.providers[cfg.id] = _provider_factory(cfg)

    def save(self):
        data = []
        for cfg in self.configs.values():
            try:
                data.append({
                    "id": cfg.id,
                    "name": cfg.name,
                    "api_base": cfg.api_base or "",
                    "model": cfg.model,
                    "api_key": cfg.api_key,
                    "kind": cfg.kind,
                    "meta": cfg.meta,
                })
            except Exception:
                continue
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def register(self, provider_id: str, impl, cfg: Optional[ProviderConfig] = None):
        self.providers[provider_id] = impl
        if cfg:
            self.configs[cfg.id] = cfg
        else:
            if provider_id not in self.configs:
                self.configs[provider_id] = ProviderConfig(
                    id=provider_id, name=provider_id, kind="openai",
                    model="gpt-4o-mini", api_base=""
                )
        self.save()

    def get(self, provider_id: str):
        return self.providers.get(provider_id)

    def ids(self):
        return list(self.providers.keys())
