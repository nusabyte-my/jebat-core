"""
JEBAT — OpenAI provider implementation (stdlib urllib, no deps).
"""

from __future__ import annotations
import json, time, urllib.request
from typing import Callable, Optional

from jebat_cli_new.models import ProviderConfig, CompletionRequest, CompletionResponse, resolve_api_key, BROWSER_UA


class OpenAIProviderImpl:
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.api_base = (config.api_base or "https://api.openai.com/v1").rstrip("/")
        self.api_key = resolve_api_key(config)

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        url = f"{self.api_base}/chat/completions"
        body = {
            "model": request.model or self.config.model,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": False,
        }
        headers = {"Content-Type": "application/json", "User-Agent": BROWSER_UA}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
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

    def complete_stream(
        self,
        request: CompletionRequest,
        on_token: Optional[Callable[[str], None]] = None,
    ) -> CompletionResponse:
        """Stream completion tokens in real-time via SSE."""
        url = f"{self.api_base}/chat/completions"
        body = {
            "model": request.model or self.config.model,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": True,
        }
        headers = {"Content-Type": "application/json", "User-Agent": BROWSER_UA}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        t0 = time.perf_counter()

        collected_tokens: list[str] = []
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                for raw_line in resp:
                    line = raw_line.decode("utf-8").strip()
                    if not line or not line.startswith("data:"):
                        continue
                    payload_str = line[5:].strip()
                    if payload_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload_str)
                        choices = chunk.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                collected_tokens.append(content)
                                if on_token:
                                    on_token(content)
                    except Exception:
                        continue
        except Exception as e:
            collected_tokens.append(f"\n[Stream Error: {e}]")

        latency_ms = int((time.perf_counter() - t0) * 1000)
        full_text = "".join(collected_tokens).strip()

        return CompletionResponse(
            text=full_text,
            model=request.model or self.config.model,
            provider=self.config.id,
            tokens_used=len(full_text.split()),
            latency_ms=latency_ms,
        )
