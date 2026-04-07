"""
JEBAT LLM integration layer.
"""

from .auth import (
    ProviderAuthStatus,
    get_provider_secret,
    list_provider_auth_status,
    select_best_provider,
)
from .config import JebatLLMConfig, load_llm_config
from .history import ChatHistoryStore
from .project_context import ProjectContext, build_project_context
from .providers import build_provider, generate_with_failover, list_supported_providers
from .skills import build_skill_prompt, build_skill_registry, default_skills_path, select_relevant_skills

__all__ = [
    "ProviderAuthStatus",
    "get_provider_secret",
    "list_provider_auth_status",
    "select_best_provider",
    "JebatLLMConfig",
    "load_llm_config",
    "ChatHistoryStore",
    "ProjectContext",
    "build_project_context",
    "build_provider",
    "generate_with_failover",
    "list_supported_providers",
    "build_skill_registry",
    "default_skills_path",
    "select_relevant_skills",
    "build_skill_prompt",
]
