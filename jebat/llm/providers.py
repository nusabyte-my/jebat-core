"""LLM providers with failover and streaming support."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

from jebat.llm.config import JebatLLMConfig


class BaseProvider:
    name: str = "base"

    async def generate(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> str:
        raise NotImplementedError

    async def generate_stream(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> AsyncIterator[str]:
        """Default: yield the full response as a single chunk (non-streaming providers)."""
        result = await self.generate(prompt, system_prompt=system_prompt, **kwargs)
        yield result


class LocalEchoProvider(BaseProvider):
    name = "local"

    async def generate(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> str:
        return f"[local echo] system: {system_prompt} | prompt: {prompt}"

    async def generate_stream(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> AsyncIterator[str]:
        """Simulate token-by-token streaming for local echo."""
        full = await self.generate(prompt, system_prompt=system_prompt, **kwargs)
        words = full.split(" ")
        for i, word in enumerate(words):
            prefix = "" if i == 0 else " "
            yield prefix + word
            await asyncio.sleep(0.02)  # simulate token delay


class OpenAIProvider(BaseProvider):
    name = "openai"

    async def generate(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> str:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI()
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            resp = await client.chat.completions.create(
                model=kwargs.get("model", "gpt-4o"),
                messages=messages,
                temperature=kwargs.get("temperature", 0.2),
                max_tokens=kwargs.get("max_tokens", 4096),
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:
            raise RuntimeError(f"OpenAI provider error: {exc}") from exc

    async def generate_stream(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> AsyncIterator[str]:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI()
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            stream = await client.chat.completions.create(
                model=kwargs.get("model", "gpt-4o"),
                messages=messages,
                temperature=kwargs.get("temperature", 0.2),
                max_tokens=kwargs.get("max_tokens", 4096),
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content
        except Exception as exc:
            raise RuntimeError(f"OpenAI streaming error: {exc}") from exc


class AnthropicProvider(BaseProvider):
    name = "anthropic"

    async def generate(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> str:
        try:
            import anthropic
            client = anthropic.AsyncAnthropic()
            resp = await client.messages.create(
                model=kwargs.get("model", "claude-sonnet-4-20250514"),
                max_tokens=kwargs.get("max_tokens", 4096),
                system=system_prompt if system_prompt else anthropic.NOT_GIVEN,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.content[0].text if resp.content else ""
        except Exception as exc:
            raise RuntimeError(f"Anthropic provider error: {exc}") from exc

    async def generate_stream(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> AsyncIterator[str]:
        try:
            import anthropic
            client = anthropic.AsyncAnthropic()
            async with client.messages.stream(
                model=kwargs.get("model", "claude-sonnet-4-20250514"),
                max_tokens=kwargs.get("max_tokens", 4096),
                system=system_prompt if system_prompt else anthropic.NOT_GIVEN,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as exc:
            raise RuntimeError(f"Anthropic streaming error: {exc}") from exc


class OllamaProvider(BaseProvider):
    name = "ollama"

    def __init__(self, base_url: Optional[str] = None) -> None:
        self._base_url = base_url or "http://localhost:11434"

    async def generate(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> str:
        import httpx
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": kwargs.get("model", "qwen2.5-coder:7b"),
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": kwargs.get("temperature", 0.2),
                        "num_predict": kwargs.get("max_tokens", 4096),
                    },
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")

    async def generate_stream(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> AsyncIterator[str]:
        import httpx
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/api/chat",
                json={
                    "model": kwargs.get("model", "qwen2.5-coder:7b"),
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": kwargs.get("temperature", 0.2),
                        "num_predict": kwargs.get("max_tokens", 4096),
                    },
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

_PROVIDER_MAP: Dict[str, type] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "ollama": OllamaProvider,
    "local": LocalEchoProvider,
}


def _get_provider(name: str) -> BaseProvider:
    cls = _PROVIDER_MAP.get(name)
    if cls is None:
        return LocalEchoProvider()
    return cls()


def list_supported_providers() -> List[Dict[str, str]]:
    return [
        {"name": "openai", "description": "OpenAI API"},
        {"name": "anthropic", "description": "Anthropic Claude"},
        {"name": "ollama", "description": "Ollama local"},
        {"name": "local", "description": "Local echo provider"},
    ]


# ---------------------------------------------------------------------------
# Failover generation
# ---------------------------------------------------------------------------

async def generate_with_failover(
    config: JebatLLMConfig,
    prompt: str,
    system_prompt: str = "",
    **kwargs: Any,
) -> Tuple[str, str]:
    """Try the primary provider, then fall back through the list."""
    providers_to_try = [config.provider] + list(config.fallback_providers)
    last_error: Optional[Exception] = None

    for provider_name in providers_to_try:
        provider = _get_provider(provider_name)
        try:
            result = await provider.generate(
                prompt,
                system_prompt=system_prompt,
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                **kwargs,
            )
            return result, provider_name
        except Exception as exc:
            last_error = exc
            continue

    raise RuntimeError(
        f"All providers failed. Last error: {last_error}"
    )


async def generate_stream_with_failover(
    config: JebatLLMConfig,
    prompt: str,
    system_prompt: str = "",
    **kwargs: Any,
) -> AsyncIterator[str]:
    """Try the primary provider's stream, then fall back through the list.

    Yields text chunks as they arrive. The provider name is sent as the
    first SSE event so the client knows which backend is active.
    """
    providers_to_try = [config.provider] + list(config.fallback_providers)
    last_error: Optional[Exception] = None

    for provider_name in providers_to_try:
        provider = _get_provider(provider_name)
        try:
            # Yield provider info as first event
            yield {"type": "metadata", "provider": provider_name, "model": config.model}
            async for chunk in provider.generate_stream(
                prompt,
                system_prompt=system_prompt,
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                **kwargs,
            ):
                yield {"type": "token", "content": chunk}
            yield {"type": "done", "provider": provider_name}
            return
        except Exception as exc:
            last_error = exc
            continue

    yield {"type": "error", "message": f"All providers failed: {last_error}"}
