from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True, slots=True)
class JebatLLMConfig:
    provider: str = "openai"
    model: str = "gpt-5.4"
    temperature: float = 0.2
    top_p: float = 0.95
    top_k: int = 64
    max_tokens: int = 1200
    ollama_host: str = "http://127.0.0.1:11434"
    ollama_keep_alive: str = ""  # e.g. "5m", "1h", "0" (0 unloads immediately); empty = server default
    llamacpp_host: str = "http://127.0.0.1:8080"
    fallback_providers: tuple[str, ...] = ("local",)
    history_path: str = ".jebat/chat_history.jsonl"
    # Custom OpenAI-compatible endpoint support
    custom_api_url: str = ""
    custom_api_key: str = "sk-dummy"


def load_llm_config(config_path: str | Path | None = None) -> JebatLLMConfig:
    raw = _load_yaml_config(config_path)

    provider = os.getenv("JEBAT_LLM_PROVIDER", raw.get("provider", "openai"))
    model = os.getenv("JEBAT_LLM_MODEL", raw.get("model", "gpt-5.4"))
    temperature = float(os.getenv("JEBAT_LLM_TEMPERATURE", raw.get("temperature", 0.2)))
    top_p = float(os.getenv("JEBAT_LLM_TOP_P", raw.get("top_p", 0.95)))
    top_k = int(os.getenv("JEBAT_LLM_TOP_K", raw.get("top_k", 64)))
    max_tokens = int(os.getenv("JEBAT_LLM_MAX_TOKENS", raw.get("max_tokens", 1200)))
    ollama_host = os.getenv("OLLAMA_HOST", raw.get("ollama_host", "http://127.0.0.1:11434"))
    llamacpp_host = os.getenv("LLAMA_CPP_HOST", raw.get("llamacpp_host", "http://127.0.0.1:8080"))
    ollama_keep_alive = os.getenv("OLLAMA_KEEP_ALIVE", raw.get("ollama_keep_alive", ""))
    fallback_raw = os.getenv("JEBAT_LLM_FALLBACKS", ",".join(raw.get("fallback_providers", ["local"])))
    history_path = os.getenv("JEBAT_CHAT_HISTORY_PATH", raw.get("history_path", ".jebat/chat_history.jsonl"))
    fallbacks = tuple(item.strip().lower() for item in str(fallback_raw).split(",") if item.strip())
    # Custom endpoint support
    custom_api_url = os.getenv("JEBAT_CUSTOM_API_URL", raw.get("custom_api_url", ""))
    custom_api_key = os.getenv("JEBAT_CUSTOM_API_KEY", raw.get("custom_api_key", "sk-dummy"))

    return JebatLLMConfig(
        provider=str(provider).strip().lower(),
        model=str(model).strip(),
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        max_tokens=max_tokens,
        ollama_host=str(ollama_host).strip(),
        llamacpp_host=str(llamacpp_host).strip(),
        ollama_keep_alive=str(ollama_keep_alive).strip(),
        fallback_providers=fallbacks,
        history_path=str(history_path).strip(),
        custom_api_url=str(custom_api_url).strip(),
        custom_api_key=str(custom_api_key).strip(),
    )


def _load_yaml_config(config_path: str | Path | None) -> dict[str, Any]:
    resolved = Path(config_path or Path(__file__).resolve().parents[1] / "config" / "config.yaml")
    if not resolved.exists():
        return {}
    data = yaml.safe_load(resolved.read_text(encoding="utf-8")) or {}
    llm = data.get("llm", {})
    return llm if isinstance(llm, dict) else {}
