"""
JEBAT — Gemini provider implementation via OpenAI-compatible endpoint.
"""

from __future__ import annotations

import json, time, urllib.request
from typing import Optional

from jebat_cli_new.models import ProviderConfig, CompletionRequest, CompletionResponse, resolve_api_key


class GeminiProviderImpl:
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.api_base = (config.api_base or "https://generativelanguage.googleapis.com/v1beta/openai").rstrip("/")
        self.api_key = resolve_api_key(config)

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        url = f"{self.api_base}/chat/completions"
        body = {
            "model": request.model or self.config.model,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        t0 = time.perf_counter()
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        latency_ms = int((time.perf_counter() - t0) * 1000)

        text = raw["choices"][0]["message"]["content"]
        usage = raw.get("usage", {})
        tokens = usage.get("total_tokens", 0)

        return CompletionResponse(
            text=text,
            model=raw.get("model", request.model),
            provider=self.config.id,
            tokens_used=tokens,
            latency_ms=latency_ms,
        )
