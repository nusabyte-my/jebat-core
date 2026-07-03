"""
JEBAT — unified coding-agent CLI runner.
This module contains the actual Ollama completion helper used by main commands.
"""

from __future__ import annotations

import json
import time
import urllib.request
from typing import Optional, Tuple


def ollama_complete(
    model: str = "qwen2.5-coder:7b",
    prompt: str = "",
    temperature: float = 0.2,
    max_tokens: int = 4096,
    host: str = "http://127.0.0.1:11434",
) -> Tuple[str, int]:
    url = f"{host.rstrip('/')}/api/generate"
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt or "",
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_ctx": 4096,
                "num_predict": max_tokens,
            },
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    start = time.time()
    with urllib.request.urlopen(req, timeout=300) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    latency_ms = int((time.time() - start) * 1000)
    text = (body.get("response") or "").strip()
    return text, latency_ms
