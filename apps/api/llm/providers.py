from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urljoin

import httpx

from .auth import get_provider_secret
from .config import JebatLLMConfig


class LLMProvider(Protocol):
    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        ...


@dataclass(slots=True)
class LocalEchoProvider:
    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        preface = system_prompt.strip() if system_prompt else "JEBAT local fallback"
        return f"{preface}\n\n{prompt}".strip()


@dataclass(slots=True)
class OpenAIProvider:
    api_key: str
    model: str
    temperature: float
    max_tokens: int

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise RuntimeError("openai package is not installed") from exc

        client = AsyncOpenAI(api_key=self.api_key)
        response = await client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt or "You are JEBAT."}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": prompt}],
                },
            ],
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
        )
        text = getattr(response, "output_text", "") or ""
        if text:
            return text.strip()
        # Conservative fallback parsing for SDK differences
        output = getattr(response, "output", []) or []
        parts: list[str] = []
        for item in output:
            for content in getattr(item, "content", []) or []:
                maybe_text = getattr(content, "text", "")
                if isinstance(maybe_text, str) and maybe_text:
                    parts.append(maybe_text)
        if parts:
            return "\n".join(parts).strip()
        raise RuntimeError("OpenAI response did not contain text output")


@dataclass(slots=True)
class AnthropicProvider:
    api_key: str
    model: str
    temperature: float
    max_tokens: int

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        try:
            import anthropic
        except ImportError as exc:
            raise RuntimeError("anthropic package is not installed") from exc

        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        response = await client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_prompt or "You are JEBAT.",
            messages=[{"role": "user", "content": prompt}],
        )
        parts: list[str] = []
        for block in response.content:
            text = getattr(block, "text", None)
            if isinstance(text, str):
                parts.append(text)
        if parts:
            return "\n".join(parts).strip()
        raise RuntimeError("Anthropic response did not contain text output")


@dataclass(slots=True)
class GoogleProvider:
    api_key: str
    model: str
    temperature: float
    max_tokens: int

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        model_name = self.model if self.model.startswith("gemini") else f"gemini/{self.model}"
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt or "You are JEBAT."}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            },
        }
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model_name}:generateContent?key={self.api_key}"
        )
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
        data = response.json()
        candidates = data.get("candidates", [])
        parts: list[str] = []
        for candidate in candidates:
            content = candidate.get("content", {})
            for part in content.get("parts", []):
                text = part.get("text")
                if isinstance(text, str):
                    parts.append(text)
        if parts:
            return "\n".join(parts).strip()
        raise RuntimeError("Google response did not contain text output")


@dataclass(slots=True)
class OpenRouterProvider:
    api_key: str
    model: str
    temperature: float
    max_tokens: int

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt or "You are JEBAT."},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
        data = response.json()
        choices = data.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()
        raise RuntimeError("OpenRouter response did not contain text output")


@dataclass(slots=True)
class OllamaProvider:
    model: str
    host: str
    temperature: float
    speculative_model: str | None = None

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        payload = {
            "model": self.model,
            "system": system_prompt or "You are JEBAT.",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        if self.speculative_model:
            # Use Ollama's speculative decoding parameter
            payload["speculative"] = self.speculative_model

        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                urljoin(self.host.rstrip("/") + "/", "api/generate"),
                json=payload,
            )
            response.raise_for_status()
        data = response.json()
        text = str(data.get("response", "")).strip()
        if text:
            return text
        raise RuntimeError("Ollama response did not contain text output")


def build_provider(config: JebatLLMConfig) -> LLMProvider:
    provider = config.provider.lower()
    if provider == "openai":
        api_key = get_provider_secret("openai")
        return OpenAIProvider(
            api_key=api_key,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    if provider == "google":
        api_key = get_provider_secret("google")
        return GoogleProvider(
            api_key=api_key,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    if provider == "anthropic":
        api_key = get_provider_secret("anthropic")
        return AnthropicProvider(
            api_key=api_key,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    if provider == "openrouter":
        api_key = get_provider_secret("openrouter")
        return OpenRouterProvider(
            api_key=api_key,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    if provider == "ollama":
        return OllamaProvider(
            model=config.model,
            host=config.ollama_host,
            temperature=config.temperature,
            speculative_model=config.speculative_model,
        )
    if provider == "local":
        return LocalEchoProvider()
    raise ValueError(f"unsupported provider: {config.provider}")


async def generate_with_failover(
    config: JebatLLMConfig,
    prompt: str,
    system_prompt: str | None = None,
) -> tuple[str, str]:
    attempts = [config.provider, *[name for name in config.fallback_providers if name != config.provider]]
    errors: list[str] = []
    for provider_name in attempts:
        candidate = JebatLLMConfig(
            provider=provider_name,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            ollama_host=config.ollama_host,
            fallback_providers=(),
            history_path=config.history_path,
        )
        try:
            provider = build_provider(candidate)
            return await provider.generate(prompt=prompt, system_prompt=system_prompt), provider_name
        except Exception as exc:
            errors.append(f"{provider_name}: {exc}")
    raise RuntimeError("all providers failed: " + "; ".join(errors))


def list_supported_providers() -> list[dict[str, str]]:
    return [
        {"name": "openai", "env": "OPENAI_API_KEY", "notes": "OpenAI Responses API"},
        {"name": "google", "env": "GOOGLE_API_KEY or GEMINI_API_KEY", "notes": "Google Gemini API"},
        {"name": "anthropic", "env": "ANTHROPIC_API_KEY", "notes": "Anthropic Messages API"},
        {"name": "openrouter", "env": "OPENROUTER_API_KEY", "notes": "OpenRouter chat completions"},
        {"name": "ollama", "env": "OLLAMA_HOST", "notes": "Local Ollama daemon"},
        {"name": "local", "env": "-", "notes": "Deterministic offline fallback"},
    ]
