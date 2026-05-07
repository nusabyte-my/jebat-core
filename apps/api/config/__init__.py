"""
JEBAT Configuration

Centralized settings loaded from environment variables and config.yaml.
Environment variables take precedence over YAML values.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv

    # Search upward for .env file
    _env_candidates = [
        Path(__file__).resolve().parents[3] / ".env",  # repo root
        Path(__file__).resolve().parents[1] / ".env",  # apps/api/.env
        Path.cwd() / ".env",
    ]
    for _env_path in _env_candidates:
        if _env_path.exists():
            load_dotenv(_env_path)
            break
except ImportError:
    pass


def _env(key: str, default: str = "") -> str:
    """Get environment variable with default."""
    return os.getenv(key, default).strip()


def _env_bool(key: str, default: bool = False) -> bool:
    """Get boolean environment variable."""
    val = os.getenv(key, "").strip().lower()
    if not val:
        return default
    return val in ("true", "1", "yes")


def _env_int(key: str, default: int = 0) -> int:
    """Get integer environment variable."""
    val = os.getenv(key, "").strip()
    if not val:
        return default
    try:
        return int(val)
    except ValueError:
        return default


def _env_float(key: str, default: float = 0.0) -> float:
    """Get float environment variable."""
    val = os.getenv(key, "").strip()
    if not val:
        return default
    try:
        return float(val)
    except ValueError:
        return default


@dataclass(frozen=True)
class DatabaseSettings:
    enabled: bool = field(default_factory=lambda: _env_bool("JEBAT_DATABASE_ENABLED", False))
    url: str = field(default_factory=lambda: _env("JEBAT_DATABASE_URL", "sqlite+aiosqlite:///jebat.db"))
    pool_size: int = field(default_factory=lambda: _env_int("JEBAT_DATABASE_POOL_SIZE", 5))
    max_overflow: int = field(default_factory=lambda: _env_int("JEBAT_DATABASE_MAX_OVERFLOW", 10))


@dataclass(frozen=True)
class LLMSettings:
    provider: str = field(default_factory=lambda: _env("JEBAT_LLM_PROVIDER", "ollama"))
    model: str = field(default_factory=lambda: _env("JEBAT_LLM_MODEL", "llama3.2"))
    temperature: float = field(default_factory=lambda: _env_float("JEBAT_LLM_TEMPERATURE", 0.2))
    max_tokens: int = field(default_factory=lambda: _env_int("JEBAT_LLM_MAX_TOKENS", 1200))
    ollama_host: str = field(default_factory=lambda: _env("OLLAMA_HOST", "http://127.0.0.1:11434"))
    history_path: str = field(default_factory=lambda: _env("JEBAT_CHAT_HISTORY_PATH", ".jebat/chat_history.jsonl"))


@dataclass(frozen=True)
class APISettings:
    host: str = field(default_factory=lambda: _env("JEBAT_API_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: _env_int("JEBAT_API_PORT", 8080))


@dataclass(frozen=True)
class WebUISettings:
    host: str = field(default_factory=lambda: _env("JEBAT_WEBUI_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: _env_int("JEBAT_WEBUI_PORT", 8787))


@dataclass(frozen=True)
class Settings:
    """Root settings object. All values sourced from environment variables."""

    debug: bool = field(default_factory=lambda: _env_bool("JEBAT_DEBUG", False))
    log_level: str = field(default_factory=lambda: _env("JEBAT_LOG_LEVEL", "INFO"))
    version: str = "2.0.0"

    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    llm: LLMSettings = field(default_factory=LLMSettings)
    api: APISettings = field(default_factory=APISettings)
    webui: WebUISettings = field(default_factory=WebUISettings)


# Singleton instance
settings = Settings()

__all__ = ["settings", "Settings", "DatabaseSettings", "LLMSettings", "APISettings", "WebUISettings"]
