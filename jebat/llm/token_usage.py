from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from typing import Any, Mapping


@dataclass(slots=True)
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cached_tokens: int = 0
    raw_usage: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def usage_from_texts(
    prompt: str,
    completion: str,
    *,
    model: str = "",
    provider: str = "",
    raw_usage: Any = None,
) -> TokenUsage:
    normalized = _normalize_provider_usage(raw_usage)
    prompt_tokens = normalized.get("prompt_tokens")
    completion_tokens = normalized.get("completion_tokens")
    total_tokens = normalized.get("total_tokens")
    cached_tokens = normalized.get("cached_tokens", 0)

    if prompt_tokens is None:
        prompt_tokens = estimate_tokens(prompt, model=model, provider=provider)
    if completion_tokens is None:
        completion_tokens = estimate_tokens(completion, model=model, provider=provider)
    if total_tokens is None:
        total_tokens = prompt_tokens + completion_tokens

    return TokenUsage(
        prompt_tokens=max(0, int(prompt_tokens)),
        completion_tokens=max(0, int(completion_tokens)),
        total_tokens=max(0, int(total_tokens)),
        cached_tokens=max(0, int(cached_tokens)),
        raw_usage=normalized.get("raw_usage", {}),
    )


def estimate_tokens(text: str, *, model: str = "", provider: str = "") -> int:
    stripped = text.strip()
    if not stripped:
        return 0

    token_count = _estimate_with_tiktoken(stripped, model=model, provider=provider)
    if token_count is not None:
        return token_count

    # Conservative fallback when a model tokenizer is unavailable locally.
    pieces = re.findall(r"\w+|[^\w\s]", stripped, re.UNICODE)
    heuristic = max(len(stripped) // 4, int(len(pieces) * 0.75))
    return max(1, heuristic)


def _normalize_provider_usage(raw_usage: Any) -> dict[str, Any]:
    usage = _coerce_usage_mapping(raw_usage)
    if not usage:
        return {"raw_usage": {}}

    prompt_tokens = _first_int(
        usage,
        "prompt_tokens",
        "input_tokens",
        "promptTokenCount",
        "inputTokenCount",
        "prompt_eval_count",
    )
    completion_tokens = _first_int(
        usage,
        "completion_tokens",
        "output_tokens",
        "completionTokenCount",
        "candidatesTokenCount",
        "outputTokenCount",
        "eval_count",
    )
    total_tokens = _first_int(
        usage,
        "total_tokens",
        "totalTokenCount",
        "total_token_count",
        "total_duration_tokens",
    )
    cached_tokens = _first_int(
        usage,
        "cached_tokens",
        "cache_creation_input_tokens",
        "cache_read_input_tokens",
        "cachedContentTokenCount",
    ) or 0

    if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
        total_tokens = prompt_tokens + completion_tokens

    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "cached_tokens": cached_tokens,
        "raw_usage": usage,
    }


def _coerce_usage_mapping(raw_usage: Any) -> dict[str, Any]:
    if raw_usage is None:
        return {}
    if isinstance(raw_usage, Mapping):
        return dict(raw_usage)
    if hasattr(raw_usage, "model_dump"):
        dumped = raw_usage.model_dump()
        if isinstance(dumped, Mapping):
            return dict(dumped)
    if hasattr(raw_usage, "to_dict"):
        dumped = raw_usage.to_dict()
        if isinstance(dumped, Mapping):
            return dict(dumped)
    if hasattr(raw_usage, "__dict__"):
        return {
            key: value
            for key, value in vars(raw_usage).items()
            if not key.startswith("_")
        }
    return {}


def _first_int(usage: Mapping[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = usage.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


@lru_cache(maxsize=16)
def _get_tiktoken_encoder(model: str, provider: str):
    try:
        import tiktoken
    except ImportError:
        return None

    candidate = (model or "").strip()
    provider_name = (provider or "").strip().lower()
    try:
        if candidate:
            return tiktoken.encoding_for_model(candidate)
    except KeyError:
        pass

    if provider_name in {"openai", "openrouter", "llamacpp"} or candidate.startswith(("gpt-", "o")):
        return tiktoken.get_encoding("o200k_base")
    return None


def _estimate_with_tiktoken(text: str, *, model: str, provider: str) -> int | None:
    encoder = _get_tiktoken_encoder(model, provider)
    if encoder is None:
        return None
    try:
        return len(encoder.encode(text))
    except Exception:
        return None
