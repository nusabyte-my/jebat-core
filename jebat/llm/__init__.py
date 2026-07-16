"""
JEBAT LLM integration layer.
"""

from .auth import (
    ProviderAuthStatus,
    get_provider_secret,
    list_provider_auth_status,
    select_best_provider,
)
from .chat_runtime import (
    ChatGenerationMetadata,
    apply_chat_preset,
    build_chat_system_prompt,
    generate_chat_reply,
    list_chat_presets,
    normalize_chat_preset,
    resolve_llm_config,
)
from .conversation import PreparedPrompt, prepare_chat_prompt, select_prompt_profile, summarize_history
from .config import JebatLLMConfig, load_llm_config
from .history import ChatHistoryStore
from .project_context import ProjectContext, build_project_context
from .providers import ProviderGeneration, build_provider, generate_with_failover, list_supported_providers
from .ninerouter_provider import NineRouterProvider, build_ninerouter_provider, print_ninerouter_setup, list_free_models, FREE_MODELS
from .skills import build_skill_prompt, build_skill_registry, default_skills_path, select_relevant_skills
from .token_usage import BudgetedInput, TokenUsage, budget_input, estimate_tokens, input_token_budget, usage_from_texts

__all__ = [
    "ProviderAuthStatus",
    "get_provider_secret",
    "list_provider_auth_status",
    "select_best_provider",
    "PreparedPrompt",
    "prepare_chat_prompt",
    "select_prompt_profile",
    "summarize_history",
    "resolve_llm_config",
    "normalize_chat_preset",
    "list_chat_presets",
    "apply_chat_preset",
    "build_chat_system_prompt",
    "generate_chat_reply",
    "ChatGenerationMetadata",
    "JebatLLMConfig",
    "load_llm_config",
    "ChatHistoryStore",
    "ProjectContext",
    "build_project_context",
    "ProviderGeneration",
    "build_provider",
    "generate_with_failover",
    "list_supported_providers",
    "TokenUsage",
    "BudgetedInput",
    "budget_input",
    "estimate_tokens",
    "input_token_budget",
    "usage_from_texts",
    "build_skill_registry",
    "default_skills_path",
    "select_relevant_skills",
    "build_skill_prompt",
]
