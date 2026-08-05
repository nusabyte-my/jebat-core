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


@dataclass(slots=True)
class BudgetedInput:
    prompt: str
    system_prompt: str
    input_budget: int
    input_tokens: int
    truncated: bool


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


def input_token_budget(context_window: int, max_output_tokens: int) -> int:
    """Return the input capacity after reserving the requested completion."""
    return max(0, int(context_window) - max(0, int(max_output_tokens)))


def budget_input(
    prompt: str,
    system_prompt: str | None = None,
    *,
    context_window: int,
    max_output_tokens: int,
    model: str = "",
    provider: str = "",
) -> BudgetedInput:
    """Fit an LLM request into its context window, keeping system instructions first."""
    budget = input_token_budget(context_window, max_output_tokens)
    system = system_prompt or ""
    original_input = _join_input(system, prompt)
    if estimate_tokens(original_input, model=model, provider=provider) <= budget:
        return BudgetedInput(prompt, system, budget, estimate_tokens(original_input, model=model, provider=provider), False)

    system = truncate_to_token_budget(system, budget, model=model, provider=provider)
    remaining = max(0, budget - estimate_tokens(system, model=model, provider=provider))
    prompt = truncate_to_token_budget(prompt, remaining, model=model, provider=provider)
    # Separators can consume tokens, so make a final prompt-only pass against the complete input.
    total = estimate_tokens(_join_input(system, prompt), model=model, provider=provider)
    if total > budget:
        prompt = truncate_to_token_budget(prompt, max(0, remaining - (total - budget)), model=model, provider=provider)
        total = estimate_tokens(_join_input(system, prompt), model=model, provider=provider)
    return BudgetedInput(prompt, system, budget, total, True)


def truncate_to_token_budget(text: str, budget: int, *, model: str = "", provider: str = "") -> str:
    """Truncate text by tokenizer estimate, preserving the beginning and latest context."""
    if budget <= 0:
        return ""
    if estimate_tokens(text, model=model, provider=provider) <= budget:
        return text

    marker = "\n[...truncated for token budget...]\n"
    marker_tokens = estimate_tokens(marker, model=model, provider=provider)
    if budget <= marker_tokens:
        return ""
    available = budget - marker_tokens
    left = available * 2 // 3
    right = available - left
    start = _prefix_for_budget(text, left, model=model, provider=provider)
    end = _suffix_for_budget(text, right, model=model, provider=provider)
    result = start.rstrip() + marker + end.lstrip()
    while result and estimate_tokens(result, model=model, provider=provider) > budget:
        result = result[:-1]
    return result


def _join_input(system_prompt: str, prompt: str) -> str:
    return "\n\n".join(part for part in (system_prompt, prompt) if part)


def _prefix_for_budget(text: str, budget: int, *, model: str, provider: str) -> str:
    low, high = 0, len(text)
    while low < high:
        middle = (low + high + 1) // 2
        if estimate_tokens(text[:middle], model=model, provider=provider) <= budget:
            low = middle
        else:
            high = middle - 1
    return text[:low]


def _suffix_for_budget(text: str, budget: int, *, model: str, provider: str) -> str:
    low, high = 0, len(text)
    while low < high:
        middle = (low + high + 1) // 2
        if estimate_tokens(text[len(text) - middle :], model=model, provider=provider) <= budget:
            low = middle
        else:
            high = middle - 1
    return text[len(text) - low :]


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
