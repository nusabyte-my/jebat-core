"""
JEBAT — Anthropic provider implementation (stdlib urllib, no deps).
"""

from __future__ import annotations

import json, time, urllib.request
from typing import Optional

from jebat_cli_new.models import ProviderConfig, CompletionRequest, CompletionResponse, resolve_api_key


class AnthropicProviderImpl:
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.api_base = (config.api_base or "https://api.anthropic.com").rstrip("/")
        self.api_key = resolve_api_key(config)

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        url = f"{self.api_base}/v1/messages"
        body = {
            "model": request.model or self.config.model,
            "max_tokens": request.max_tokens,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": request.temperature,
        }
        headers = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
            "x-api-key": self.api_key,
        }

        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        t0 = time.perf_counter()
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        latency_ms = int((time.perf_counter() - t0) * 1000)

        text = raw["content"][0]["text"] if raw.get("content") else ""
        usage = raw.get("usage", {})
        tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)

        return CompletionResponse(
            text=text,
            model=raw.get("model", request.model),
            provider=self.config.id,
            tokens_used=tokens,
            latency_ms=latency_ms,
        )
