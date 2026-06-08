from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urljoin

from .auth import get_provider_secret
from .config import JebatLLMConfig
from .ninerouter_provider import build_ninerouter_provider
from .token_usage import TokenUsage, usage_from_texts


class LLMProvider(Protocol):
    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        ...


@dataclass(slots=True)
class ProviderGeneration:
    text: str
    usage: TokenUsage


def _input_for_usage(prompt: str, system_prompt: str | None = None) -> str:
    return "\n\n".join(part for part in [system_prompt or "", prompt] if part)


@dataclass(slots=True)
class LocalEchoProvider:
    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        return (await self.generate_with_metadata(prompt=prompt, system_prompt=system_prompt)).text

    async def generate_with_metadata(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> ProviderGeneration:
        preface = system_prompt.strip() if system_prompt else "JEBAT local fallback"
        text = f"{preface}\n\n{prompt}".strip()
        return ProviderGeneration(
            text=text,
            usage=usage_from_texts(_input_for_usage(prompt, system_prompt), text, provider="local"),
        )


@dataclass(slots=True)
class OpenAIProvider:
    api_key: str
    model: str
    temperature: float
    max_tokens: int

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        return (await self.generate_with_metadata(prompt=prompt, system_prompt=system_prompt)).text

    async def generate_with_metadata(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> ProviderGeneration:
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
        if not text:
            output = getattr(response, "output", []) or []
            parts: list[str] = []
            for item in output:
                for content in getattr(item, "content", []) or []:
                    maybe_text = getattr(content, "text", "")
                    if isinstance(maybe_text, str) and maybe_text:
                        parts.append(maybe_text)
            text = "\n".join(parts).strip()
        if not text:
            raise RuntimeError("OpenAI response did not contain text output")
        return ProviderGeneration(
            text=text,
            usage=usage_from_texts(
                _input_for_usage(prompt, system_prompt),
                text,
                model=self.model,
                provider="openai",
                raw_usage=getattr(response, "usage", None),
            ),
        )


@dataclass(slots=True)
class AnthropicProvider:
    api_key: str
    model: str
    temperature: float
    max_tokens: int

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        return (await self.generate_with_metadata(prompt=prompt, system_prompt=system_prompt)).text

    async def generate_with_metadata(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> ProviderGeneration:
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
        text = "\n".join(parts).strip()
        if not text:
            raise RuntimeError("Anthropic response did not contain text output")
        return ProviderGeneration(
            text=text,
            usage=usage_from_texts(
                _input_for_usage(prompt, system_prompt),
                text,
                model=self.model,
                provider="anthropic",
                raw_usage=getattr(response, "usage", None),
            ),
        )


@dataclass(slots=True)
class GoogleProvider:
    api_key: str
    model: str
    temperature: float
    max_tokens: int

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        return (await self.generate_with_metadata(prompt=prompt, system_prompt=system_prompt)).text

    async def generate_with_metadata(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> ProviderGeneration:
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
        import httpx

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
        text = "\n".join(parts).strip()
        if not text:
            raise RuntimeError("Google response did not contain text output")
        return ProviderGeneration(
            text=text,
            usage=usage_from_texts(
                _input_for_usage(prompt, system_prompt),
                text,
                model=self.model,
                provider="google",
                raw_usage=data.get("usageMetadata", {}),
            ),
        )


@dataclass(slots=True)
class OpenRouterProvider:
    api_key: str
    model: str
    temperature: float
    max_tokens: int

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        return (await self.generate_with_metadata(prompt=prompt, system_prompt=system_prompt)).text

    async def generate_with_metadata(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> ProviderGeneration:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt or "You are JEBAT."},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        import httpx

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
        text = ""
        if choices:
            message = choices[0].get("message", {})
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                text = content.strip()
        if not text:
            raise RuntimeError("OpenRouter response did not contain text output")
        return ProviderGeneration(
            text=text,
            usage=usage_from_texts(
                _input_for_usage(prompt, system_prompt),
                text,
                model=self.model,
                provider="openrouter",
                raw_usage=data.get("usage", {}),
            ),
        )


@dataclass(slots=True)
class LlamaCppProvider:
    model: str
    host: str
    temperature: float
    top_p: float
    top_k: int
    max_tokens: int

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        return (await self.generate_with_metadata(prompt=prompt, system_prompt=system_prompt)).text

    async def generate_with_metadata(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> ProviderGeneration:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt or "You are JEBAT."},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        import httpx

        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                urljoin(self.host.rstrip("/") + "/", "v1/chat/completions"),
                json=payload,
            )
            response.raise_for_status()
        data = response.json()
        choices = data.get("choices", [])
        text = ""
        if choices:
            message = choices[0].get("message", {})
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                text = content.strip()
        if not text:
            raise RuntimeError("llama.cpp response did not contain text output")
        return ProviderGeneration(
            text=text,
            usage=usage_from_texts(
                _input_for_usage(prompt, system_prompt),
                text,
                model=self.model,
                provider="llamacpp",
                raw_usage=data.get("usage", {}),
            ),
        )


@dataclass(slots=True)
class OllamaProvider:
    model: str
    host: str
    temperature: float

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        return (await self.generate_with_metadata(prompt=prompt, system_prompt=system_prompt)).text

    async def generate_with_metadata(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> ProviderGeneration:
        payload = {
            "model": self.model,
            "system": system_prompt or "You are JEBAT.",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        import httpx

        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                urljoin(self.host.rstrip("/") + "/", "api/generate"),
                json=payload,
            )
            response.raise_for_status()
        data = response.json()
        text = str(data.get("response", "")).strip()
        if not text:
            raise RuntimeError("Ollama response did not contain text output")
        raw_usage = {
            key: value
            for key, value in data.items()
            if key in {"prompt_eval_count", "eval_count", "total_duration", "load_duration"}
        }
        return ProviderGeneration(
            text=text,
            usage=usage_from_texts(
                _input_for_usage(prompt, system_prompt),
                text,
                model=self.model,
                provider="ollama",
                raw_usage=raw_usage,
            ),
        )


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
    if provider == "llamacpp":
        return LlamaCppProvider(
            model=config.model,
            host=config.llamacpp_host,
            temperature=config.temperature,
            top_p=config.top_p,
            top_k=config.top_k,
            max_tokens=config.max_tokens,
        )
    if provider == "ollama":
        return OllamaProvider(
            model=config.model,
            host=config.ollama_host,
            temperature=config.temperature,
        )
    if provider == "ninerouter":
        return build_ninerouter_provider(config)
    if provider == "local":
        return LocalEchoProvider()
    raise ValueError(f"unsupported provider: {config.provider}")


async def generate_with_failover(
    config: JebatLLMConfig,
    prompt: str,
    system_prompt: str | None = None,
    *,
    return_metadata: bool = False,
) -> tuple[str | ProviderGeneration, str]:
    attempts = [config.provider, *[name for name in config.fallback_providers if name != config.provider]]
    errors: list[str] = []
    for provider_name in attempts:
        candidate = JebatLLMConfig(
            provider=provider_name,
            model=config.model,
            temperature=config.temperature,
            top_p=config.top_p,
            top_k=config.top_k,
            max_tokens=config.max_tokens,
            ollama_host=config.ollama_host,
            llamacpp_host=config.llamacpp_host,
            fallback_providers=(),
            history_path=config.history_path,
        )
        try:
            provider = build_provider(candidate)
            if return_metadata and hasattr(provider, "generate_with_metadata"):
                return await provider.generate_with_metadata(prompt=prompt, system_prompt=system_prompt), provider_name
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
        {"name": "llamacpp", "env": "LLAMA_CPP_HOST", "notes": "llama.cpp OpenAI-compatible server"},
        {"name": "ollama", "env": "OLLAMA_HOST", "notes": "Local Ollama daemon"},
        {"name": "ninerouter", "env": "NINEROUTER_HOST + NINEROUTER_API_KEY", "notes": "9Router FREE AI proxy (kr/oc/glm/mm/vtx models)"},
        {"name": "local", "env": "-", "notes": "Deterministic offline fallback"},
    ]
