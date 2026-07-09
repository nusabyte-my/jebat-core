"""
JEBAT — Ollama provider implementation.
"""

from __future__ import annotations

from typing import Optional
from jebat_cli_new.providers import Provider, ProviderConfig, CompletionRequest, CompletionResponse


class OllamaProvider:
    def __init__(self, config: Optional[ProviderConfig] = None):
        self.config = config or ProviderConfig(id="ollama", name="Ollama", api_base="http://127.0.0.1:11434", kind="ollama")

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        import urllib.request
        import urllib.error
        import json
        import time

        host = self.config.api_base or "http://127.0.0.1:11434"
        url = f"{host}/api/generate"
        payload = json.dumps(
            {
                "model": request.model,
                "prompt": request.prompt,
                "stream": False,
                "options": {"temperature": request.temperature, "num_ctx": 4096, "num_predict": request.max_tokens},
            }
        ).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        start = time.time()
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc
        latency = int((time.time() - start) * 1000)
        resp_text = body.get("response", "")
        tokens_used = int(body.get("total_tokens") or body.get("eval_count") or 0)
        return CompletionResponse(text=resp_text, model=request.model, provider="ollama", tokens_used=tokens_used, latency_ms=latency)
