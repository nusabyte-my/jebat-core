from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace

from .config import JebatLLMConfig, load_llm_config
from .conversation import PreparedPrompt, prepare_chat_prompt
from .providers import ProviderGeneration, generate_with_failover


CHAT_PRESETS: dict[str, dict[str, object]] = {
    "default": {
        "label": "Standard",
        "description": "Balanced JEBAT operator voice.",
        "temperature": 0.85,
        "top_p": 0.95,
        "top_k": 64,
        "system_prompt": (
            "You are JEBAT, a pragmatic repo-aware engineering assistant. "
            "Be direct, useful, and execution-focused. Avoid fluff, stay concrete, "
            "and answer like an operator who wants the task finished correctly."
        ),
    },
    "coding": {
        "label": "Coding",
        "description": "Sharper engineering, debugging, and implementation posture.",
        "temperature": 0.8,
        "top_p": 0.9,
        "top_k": 40,
        "system_prompt": (
            "You are JEBAT in coding mode. Prioritize debugging, implementation, "
            "architecture tradeoffs, and precise technical answers. Give code-first, "
            "repo-aware guidance and avoid vague advice."
        ),
    },
    "roleplay": {
        "label": "Roleplay",
        "description": "Immersive character voice with stronger creative flair.",
        "temperature": 0.95,
        "top_p": 0.95,
        "top_k": 64,
        "system_prompt": (
            "You are JEBAT in roleplay mode. Stay immersive, vivid, and committed "
            "to the requested tone or scene while remaining coherent and responsive "
            "to explicit user constraints."
        ),
    },
    "uncensored": {
        "label": "Uncensored",
        "description": "Blunt, direct, and less sanitized phrasing.",
        "temperature": 0.9,
        "top_p": 0.95,
        "top_k": 64,
        "system_prompt": (
            "You are JEBAT in uncensored mode. Be blunt, direct, and unfiltered in "
            "style. Do not moralize or pad the answer with generic disclaimers. "
            "Stay actionable and answer the request head-on."
        ),
    },
}


@dataclass(slots=True)
class ChatGenerationMetadata:
    prompt_profile: str
    prompt_tokens_estimate: int
    history_summary_turns: int
    recent_turns: int
    usage: dict[str, int]


def resolve_llm_config(
    provider_override: str | None = None,
    model_override: str | None = None,
) -> JebatLLMConfig:
    config = load_llm_config()
    provider = (provider_override or "").strip().lower()
    model = (model_override or "").strip()
    return replace(
        config,
        provider=provider or config.provider,
        model=model or config.model,
    )


def normalize_chat_preset(preset: str | None = None) -> str:
    candidate = (preset or "default").strip().lower()
    return candidate if candidate in CHAT_PRESETS else "default"


def list_chat_presets() -> list[dict[str, str]]:
    return [
        {
            "id": preset_id,
            "label": str(meta["label"]),
            "description": str(meta["description"]),
        }
        for preset_id, meta in CHAT_PRESETS.items()
    ]


def build_chat_system_prompt(mode: str | None = None, preset: str | None = None) -> str:
    normalized = (mode or "deliberate").strip().lower()
    preset_meta = CHAT_PRESETS[normalize_chat_preset(preset)]
    directives = {
        "fast": "Reply briefly and directly.",
        "deliberate": "Reason carefully and keep the reply concise but useful.",
        "deep": "Reason thoroughly, surface tradeoffs, and stay grounded in the request.",
        "strategic": "Think in terms of sequencing, constraints, and practical outcomes.",
        "creative": "Offer original ideas, but keep them executable.",
        "critical": "Stress-test assumptions, risks, and failure modes before concluding.",
    }
    guidance = directives.get(normalized, directives["deliberate"])
    return f'{preset_meta["system_prompt"]} {guidance}'


def apply_chat_preset(config: JebatLLMConfig, preset: str | None = None) -> JebatLLMConfig:
    preset_meta = CHAT_PRESETS[normalize_chat_preset(preset)]
    return replace(
        config,
        temperature=float(preset_meta["temperature"]),
        top_p=float(preset_meta["top_p"]),
        top_k=int(preset_meta["top_k"]),
    )


def apply_runtime_overrides(
    config: JebatLLMConfig,
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> JebatLLMConfig:
    updated = config
    if temperature is not None:
        updated = replace(updated, temperature=max(0.0, min(float(temperature), 2.0)))
    if max_tokens is not None:
        updated = replace(updated, max_tokens=max(1, int(max_tokens)))
    return updated


async def generate_chat_reply(
    prompt: str,
    mode: str | None = None,
    preset: str | None = None,
    provider_override: str | None = None,
    model_override: str | None = None,
    temperature_override: float | None = None,
    max_tokens_override: int | None = None,
    conversation_messages: list[dict[str, str]] | None = None,
    return_metadata: bool = False,
    system_prompt_override: str | None = None,
) -> tuple[str, str, JebatLLMConfig] | tuple[str, str, JebatLLMConfig, ChatGenerationMetadata]:
    config = apply_chat_preset(
        resolve_llm_config(
            provider_override=provider_override,
            model_override=model_override,
        ),
        preset=preset,
    )
    config = apply_runtime_overrides(
        config,
        temperature=temperature_override,
        max_tokens=max_tokens_override,
    )
    prepared: PreparedPrompt = prepare_chat_prompt(
        prompt,
        mode=mode,
        model=config.model,
        provider=config.provider,
        conversation_messages=conversation_messages,
    )
    # Use custom system prompt if provided, otherwise build default
    if system_prompt_override:
        system_prompt = system_prompt_override
    else:
        system_prompt = build_chat_system_prompt(mode, preset=preset)
    response, used_provider = await generate_with_failover(
        config=config,
        prompt=prepared.prompt,
        system_prompt=system_prompt,
        return_metadata=return_metadata,
    )
    if not return_metadata:
        return str(response), used_provider, config

    assert isinstance(response, ProviderGeneration)
    metadata = ChatGenerationMetadata(
        prompt_profile=prepared.profile,
        prompt_tokens_estimate=int(prepared.metadata.get("estimated_prompt_tokens", 0)),
        history_summary_turns=int(prepared.metadata.get("history_summary_turns", 0)),
        recent_turns=int(prepared.metadata.get("recent_turns", 0)),
        usage={
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        },
    )
    return response.text, used_provider, config, metadata
