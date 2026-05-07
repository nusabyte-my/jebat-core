"""
JEBAT LLM streaming support.

Provides async generators that yield text chunks from each provider,
suitable for Server-Sent Events (SSE) or WebSocket streaming.

Usage::

    from apps.api.llm.streaming import stream_generate

    async for chunk in stream_generate(config, prompt, system_prompt):
        await send_sse(chunk)
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import urljoin

from .config import JebatLLMConfig

logger = logging.getLogger(__name__)


def _httpx():
    import httpx as _mod
    return _mod


async def _stream_openai(
    api_key: str,
    model: str,
    prompt: str,
    system_prompt: str,
    temperature: float,
    max_tokens: int,
) -> AsyncIterator[str]:
    """Stream from OpenAI Chat Completions API."""
    try:
        from openai import AsyncOpenAI
    except ImportError as exc:
        raise RuntimeError("openai package is not installed") from exc

    client = AsyncOpenAI(api_key=api_key)
    stream = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


async def _stream_anthropic(
    api_key: str,
    model: str,
    prompt: str,
    system_prompt: str,
    temperature: float,
    max_tokens: int,
) -> AsyncIterator[str]:
    """Stream from Anthropic Messages API."""
    try:
        import anthropic
    except ImportError as exc:
        raise RuntimeError("anthropic package is not installed") from exc

    client = anthropic.AsyncAnthropic(api_key=api_key)
    async with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def _stream_openrouter(
    api_key: str,
    model: str,
    prompt: str,
    system_prompt: str,
    temperature: float,
    max_tokens: int,
) -> AsyncIterator[str]:
    """Stream from OpenRouter (OpenAI-compatible SSE)."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }
    httpx = _httpx()
    async with httpx.AsyncClient(timeout=180) as client:
        async with client.stream(
            "POST",
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    delta = data.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield content
                except (json.JSONDecodeError, IndexError, KeyError):
                    continue


async def _stream_ollama(
    model: str,
    host: str,
    prompt: str,
    system_prompt: str,
    temperature: float,
) -> AsyncIterator[str]:
    """Stream from Ollama /api/generate endpoint."""
    payload = {
        "model": model,
        "system": system_prompt,
        "prompt": prompt,
        "stream": True,
        "options": {"temperature": temperature},
    }
    httpx = _httpx()
    async with httpx.AsyncClient(timeout=180) as client:
        async with client.stream(
            "POST",
            urljoin(host.rstrip("/") + "/", "api/generate"),
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    chunk = data.get("response", "")
                    if chunk:
                        yield chunk
                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    continue


async def _stream_google(
    api_key: str,
    model: str,
    prompt: str,
    system_prompt: str,
    temperature: float,
    max_tokens: int,
) -> AsyncIterator[str]:
    """Stream from Google Gemini API via streamGenerateContent."""
    model_name = model if model.startswith("gemini") else f"gemini-{model}"
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model_name}:streamGenerateContent?alt=sse&key={api_key}"
    )
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }
    httpx = _httpx()
    async with httpx.AsyncClient(timeout=180) as client:
        async with client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:].strip()
                try:
                    data = json.loads(data_str)
                    candidates = data.get("candidates", [])
                    for candidate in candidates:
                        content = candidate.get("content", {})
                        for part in content.get("parts", []):
                            text = part.get("text")
                            if isinstance(text, str) and text:
                                yield text
                except (json.JSONDecodeError, KeyError):
                    continue


async def _stream_local(prompt: str, system_prompt: str) -> AsyncIterator[str]:
    """Local echo provider — yields the full response as a single chunk."""
    preface = system_prompt.strip() if system_prompt else "JEBAT local fallback"
    yield f"{preface}\n\n{prompt}".strip()


async def stream_generate(
    config: JebatLLMConfig,
    prompt: str,
    system_prompt: str | None = None,
) -> AsyncIterator[str]:
    """Stream text chunks from the configured LLM provider.

    Yields strings as they arrive from the provider.
    Falls back to non-streaming (single chunk) if the provider doesn't
    support streaming or if an error occurs.
    """
    from .auth import get_provider_secret

    provider = config.provider.lower()
    sys_prompt = system_prompt or "You are JEBAT."

    try:
        if provider == "openai":
            api_key = get_provider_secret("openai")
            async for chunk in _stream_openai(
                api_key, config.model, prompt, sys_prompt,
                config.temperature, config.max_tokens,
            ):
                yield chunk
        elif provider == "anthropic":
            api_key = get_provider_secret("anthropic")
            async for chunk in _stream_anthropic(
                api_key, config.model, prompt, sys_prompt,
                config.temperature, config.max_tokens,
            ):
                yield chunk
        elif provider == "openrouter":
            api_key = get_provider_secret("openrouter")
            async for chunk in _stream_openrouter(
                api_key, config.model, prompt, sys_prompt,
                config.temperature, config.max_tokens,
            ):
                yield chunk
        elif provider == "ollama":
            async for chunk in _stream_ollama(
                config.model, config.ollama_host, prompt, sys_prompt,
                config.temperature,
            ):
                yield chunk
        elif provider == "google":
            api_key = get_provider_secret("google")
            async for chunk in _stream_google(
                api_key, config.model, prompt, sys_prompt,
                config.temperature, config.max_tokens,
            ):
                yield chunk
        elif provider == "local":
            async for chunk in _stream_local(prompt, sys_prompt):
                yield chunk
        else:
            raise ValueError(f"unsupported provider for streaming: {provider}")
    except Exception as exc:
        logger.warning("Streaming failed for %s, yielding error: %s", provider, exc)
        yield f"[Streaming error: {exc}]"


__all__ = ["stream_generate"]
