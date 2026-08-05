from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CustomProvider:
    """Declarative metadata for a non-standard (custom) LLM gateway.

    Base URLs and OAuth URLs are intentionally left empty by default so the
    user supplies them at init time; they can also be pinned via the
    corresponding ``*_BASE_URL`` / ``*_AUTH_URL`` environment variables.

    ``default_models`` is a PLACEHOLDER catalog shown only when the live
    ``/v1/models`` fetch is unreachable. Replace these with real model ids, or
    let the init wizard / webui pick from the live catalog.
    """

    id: str
    label: str
    description: str
    api_key_env: str
    base_url_env: str
    default_base_url: str
    auth_url_env: str
    default_auth_url: str
    models_path: str
    default_models: tuple[str, ...]


CUSTOM_PROVIDERS: dict[str, CustomProvider] = {
    "opencode_go": CustomProvider(
        id="opencode_go",
        label="OpenCode Go",
        description="OpenCode Go model gateway (OpenAI-compatible).",
        api_key_env="OPENCODE_GO_API_KEY",
        base_url_env="OPENCODE_GO_BASE_URL",
        default_base_url="",
        auth_url_env="OPENCODE_GO_AUTH_URL",
        default_auth_url="",
        models_path="/models",
        # Placeholder catalog — override via live /v1/models fetch or edit here.
        default_models=("opencode-go/default", "opencode-go/go-large"),
    ),
    "opencode_zen": CustomProvider(
        id="opencode_zen",
        label="OpenCode Zen",
        description="OpenCode Zen model gateway with SSO/OAuth support (OpenAI-compatible).",
        api_key_env="OPENCODE_ZEN_API_KEY",
        base_url_env="OPENCODE_ZEN_BASE_URL",
        default_base_url="",
        auth_url_env="OPENCODE_ZEN_AUTH_URL",
        default_auth_url="",
        models_path="/models",
        # Placeholder catalog — override via live /v1/models fetch or edit here.
        default_models=("opencode-zen/default", "opencode-zen/zen-pro"),
    ),
    "zenmux": CustomProvider(
        id="zenmux",
        label="ZenMux",
        description="ZenMux token-multiplexing router (OpenAI-compatible).",
        api_key_env="ZENMUX_API_KEY",
        base_url_env="ZENMUX_BASE_URL",
        default_base_url="",
        auth_url_env="ZENMUX_AUTH_URL",
        default_auth_url="",
        models_path="/models",
        # Placeholder catalog — override via live /v1/models fetch or edit here.
        default_models=("zenmux/default", "zenmux/mux-1"),
    ),
    "tokerrouter": CustomProvider(
        id="tokerrouter",
        label="TokerRouter",
        description="TokerRouter token-usage router (OpenAI-compatible).",
        api_key_env="TOKERROUTER_API_KEY",
        base_url_env="TOKERROUTER_BASE_URL",
        default_base_url="",
        auth_url_env="TOKERROUTER_AUTH_URL",
        default_auth_url="",
        models_path="/models",
        # Placeholder catalog — override via live /v1/models fetch or edit here.
        default_models=("tokerrouter/default", "tokerrouter/route-fast"),
    ),
    "agent_router": CustomProvider(
        id="agent_router",
        label="Agent Router",
        description="Agent Router orchestration gateway with SSO/OAuth support (OpenAI-compatible).",
        api_key_env="AGENT_ROUTER_API_KEY",
        base_url_env="AGENT_ROUTER_BASE_URL",
        default_base_url="",
        auth_url_env="AGENT_ROUTER_AUTH_URL",
        default_auth_url="",
        models_path="/models",
        # Placeholder catalog — override via live /v1/models fetch or edit here.
        default_models=("agent-router/default", "agent-router/orchestrator"),
    ),
}

CUSTOM_PROVIDER_IDS: tuple[str, ...] = tuple(CUSTOM_PROVIDERS)


def is_custom_provider(name: str) -> bool:
    return str(name).strip().lower() in CUSTOM_PROVIDERS


def get_custom_provider(name: str) -> CustomProvider | None:
    return CUSTOM_PROVIDERS.get(str(name).strip().lower())
