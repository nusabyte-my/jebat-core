"""
JEBAT — streaming support hooks for providers.
Provides a base class for streaming responses.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable, Generator, Optional


@dataclass
class StreamChunk:
    text: str
    done: bool = False
    model: str = ""
    provider: str = ""
    tokens_used: int = 0


class StreamHandler:
    """Base class for streaming responses from providers."""

    def __init__(self, provider: str = "", model: str = ""):
        self.provider = provider
        self.model = model
        self.start_time = 0.0
        self.tokens = 0

    def stream(self, generator: Generator[StreamChunk, None, None]) -> str:
        """Consume a stream generator, printing chunks as they arrive."""
        self.start_time = time.perf_counter()
        full_text = []
        try:
            for chunk in generator:
                if chunk.text:
                    sys.stdout.write(chunk.text)
                    sys.stdout.flush()
                    full_text.append(chunk.text)
                if chunk.done:
                    self.tokens = chunk.tokens_used
                    break
        except KeyboardInterrupt:
            print("\n[Stream interrupted]")
        finally:
            latency_ms = int((time.perf_counter() - self.start_time) * 1000)
            print(f"\n[stream] {self.provider}/{self.model} {latency_ms}ms {self.tokens} tokens")
        return "".join(full_text)


def ollama_stream(model: str, prompt: str, temperature: float = 0.2,
                  max_tokens: int = 4096, host: str = "http://127.0.0.1:11434") -> Generator[StreamChunk, None, None]:
    """Stream from Ollama's streaming API."""
    import urllib.request
    url = f"{host}/api/generate"
    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": temperature,
            "num_ctx": 4096,
            "num_predict": max_tokens,
        },
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")

    with urllib.request.urlopen(req, timeout=300) as resp:
        buffer = ""
        while True:
            chunk = resp.read(1024)
            if not chunk:
                break
            buffer += chunk.decode("utf-8", errors="replace")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    text = obj.get("response", "")
                    done = obj.get("done", False)
                    if done:
                        yield StreamChunk(text=text, done=True, model=model, provider="ollama")
                        return
                    yield StreamChunk(text=text)
                except json.JSONDecodeError:
                    continue


def openai_stream(model: str, prompt: str, temperature: float = 0.2,
                  max_tokens: int = 4096, api_base: str = "https://api.openai.com/v1",
                  api_key: str = "") -> Generator[StreamChunk, None, None]:
    """Stream from OpenAI-compatible streaming API."""
    import urllib.request
    url = f"{api_base}/chat/completions"
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }).encode("utf-8")
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")

    with urllib.request.urlopen(req, timeout=300) as resp:
        buffer = ""
        while True:
            chunk = resp.read(1024)
            if not chunk:
                break
            buffer += chunk.decode("utf-8", errors="replace")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line or not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    yield StreamChunk(text="", done=True, model=model, provider="openai")
                    return
                try:
                    obj = json.loads(data)
                    delta = obj.get("choices", [{}])[0].get("delta", {})
                    text = delta.get("content", "")
                    if text:
                        yield StreamChunk(text=text)
                except (json.JSONDecodeError, IndexError, KeyError):
                    continue
