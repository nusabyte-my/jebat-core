"""
JEBAT LLM integration layer.
"""

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


def __getattr__(name: str):
    if name in {"ProviderAuthStatus", "get_provider_secret", "list_provider_auth_status", "select_best_provider"}:
        from .auth import (
            ProviderAuthStatus,
            get_provider_secret,
            list_provider_auth_status,
            select_best_provider,
        )

        return {
            "ProviderAuthStatus": ProviderAuthStatus,
            "get_provider_secret": get_provider_secret,
            "list_provider_auth_status": list_provider_auth_status,
            "select_best_provider": select_best_provider,
        }[name]
    if name in {"JebatLLMConfig", "load_llm_config"}:
        from .config import JebatLLMConfig, load_llm_config

        return {"JebatLLMConfig": JebatLLMConfig, "load_llm_config": load_llm_config}[name]
    if name == "ChatHistoryStore":
        from .history import ChatHistoryStore

        return ChatHistoryStore
    if name in {"ProjectContext", "build_project_context"}:
        from .project_context import ProjectContext, build_project_context

        return {"ProjectContext": ProjectContext, "build_project_context": build_project_context}[name]
    if name in {"build_provider", "generate_with_failover", "list_supported_providers"}:
        from .providers import build_provider, generate_with_failover, list_supported_providers

        return {
            "build_provider": build_provider,
            "generate_with_failover": generate_with_failover,
            "list_supported_providers": list_supported_providers,
        }[name]
    if name in {"build_skill_prompt", "build_skill_registry", "default_skills_path", "select_relevant_skills"}:
        from .skills import build_skill_prompt, build_skill_registry, default_skills_path, select_relevant_skills

        return {
            "build_skill_prompt": build_skill_prompt,
            "build_skill_registry": build_skill_registry,
            "default_skills_path": default_skills_path,
            "select_relevant_skills": select_relevant_skills,
        }[name]
    raise AttributeError(name)
