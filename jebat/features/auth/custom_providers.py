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
    "omp": CustomProvider(
        id="omp",
        label="OMP",
        description="OMP model gateway (OpenAI-compatible).",
        api_key_env="OMP_API_KEY",
        base_url_env="OMP_BASE_URL",
        default_base_url="",
        auth_url_env="OMP_AUTH_URL",
        default_auth_url="",
        models_path="/v1/models",
        # Placeholder catalog — override via live /v1/models fetch or edit here.
        default_models=("omp/default", "omp/pro"),
    ),
    "rootsys_cloud": CustomProvider(
        id="rootsys_cloud",
        label="rootsys cloud",
        description="rootsys cloud model gateway (OpenAI-compatible).",
        api_key_env="ROOTSYS_CLOUD_API_KEY",
        base_url_env="ROOTSYS_CLOUD_BASE_URL",
        default_base_url="https://rootsys.cloud/v1",
        auth_url_env="ROOTSYS_CLOUD_AUTH_URL",
        default_auth_url="",
        models_path="/v1/models",
        # rootsys.cloud gateway catalog (live /v1/models, 28 ids). Only the
        # hy4free pair is free-tier; the rest ride a flat subscription.
        default_models=(
            "glm-5.2",
            "glm-5.2-mod",
            "glm-5.3",
            "glm-5.3-mod",
            "glm-5.3-flash",
            "glm-5.3-flash-mod",
            "glm-5.3-flashx",
            "kimi-k2.7",
            "kimi-k3",
            "kimi-k3.1-pro",
            "deepseek-v4-flash",
            "deepseek-v4-pro",
            "deepseek-v4-pro-mod",
            "deepseek-v4.1-flash",
            "deepseek-v4.1-flash-mod",
            "minimax-m3",
            "minimax-m3.1-flash",
            "minimax-m3.1-flash-mod",
            "mimo-v2.6-pro",
            "mimo-v2.6-pro-mod",
            "hy3-tencent",
            "hy4-preview",
            "hy4free",
            "hy4free-mod",
            "step-5-preview",
            "step-5-preview-mod",
            "space-bunny",
            "space-bunny-mod",
        ),
    ),
    "osiris": CustomProvider(
        id="osiris",
        label="Osiris Code",
        description="Osiris-code model marketplace (OpenAI-compatible). All models FREE.",
        api_key_env="OSIRIS_CODE_API_KEY",
        base_url_env="OSIRIS_CODE_BASE_URL",
        default_base_url="https://ai.osiris-code.com/v1",
        auth_url_env="OSIRIS_CODE_AUTH_URL",
        default_auth_url="",
        models_path="/v1/models",
        # Mirror of the osiris-code marketplace catalog — every model is set to
        # FREE (0 cost) with a "free" tag.
        default_models=(
            "claude-sonnet-4.6",
            "claude-opus-4.6",
            "claude-opus-4.7",
            "claude-opus-4.7-1m",
            "gpt-6-astra",
            "gpt-5.5",
            "gpt-5.6-sol",
            "gpt-5.4",
            "gpt-5-3-codex",
            "gpt-5.6-terra",
            "gpt-6-sol",
            "gpt-6.1-sol",
            "gpt-5.6-luna",
            "gpt-6-luna",
            "gemini-3-1-pro",
            "gemini-3.8-flash-high",
            "glm-5.3-flash",
            "glm-5.3-flashx",
            "glm-5.2",
            "glm-5.3",
            "glm-5.1",
            "glm-5.0-turbo",
            "glm-5v-turbo",
            "deepseek-v4.1-flash",
            "deepseek-v4-pro",
            "deepseek-v4-flash",
            "qwen3.8-27b",
            "qwen3.8-flash",
            "qwen3.8-max",
            "qwen3.8-max-0902",
            "qwen3.8-omni-flash",
            "kimi-k3",
            "kimi-for-coding-highspeed",
            "kimi-for-coding",
            "kimi-k2.6",
            "kimi-k2.7",
            "kimi-k2.5",
            "kimi-k2.8-preview",
            "grok-4.6",
            "grok-4.7",
            "grok-4.5",
            "minimax-m2.7",
            "hy3",
            "hy3-preview",
            "hy3-preview-agent",
            "hunyuan-2.0-instruct",
            "hunyuan-chat",
            "hy4-preview",
            "mimo-v2.5",
            "mimo-v2.5-pro",
            "mimo-v2.6-flash",
            "mimo-v2.6-pro",
            "k3",
            "k3-256k",
            "claude-opus-4.6-thinking",
            "claude-opus-5.5",
            "claude-sonnet-5.5",
            "claude-haiku-5.5",
            "gemini-4-argon",
            "kimi-k3.1-pro",
            "minimax-m3",
            "muse-spark-1.3",
        ),
    ),
}

CUSTOM_PROVIDER_IDS: tuple[str, ...] = tuple(CUSTOM_PROVIDERS)


def is_custom_provider(name: str) -> bool:
    return str(name).strip().lower() in CUSTOM_PROVIDERS


def get_custom_provider(name: str) -> CustomProvider | None:
    return CUSTOM_PROVIDERS.get(str(name).strip().lower())
