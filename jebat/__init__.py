"""
JEBAT - Unified AI Assistant Platform

JEBAT (named after the legendary Malay warrior Hang Jebat) is a personal AI
assistant with eternal memory, ultra-reasoning, and continuous learning.

Version: 2.0.0-refactored
Status: Production Ready
"""

__version__ = "3.0.1"
__author__ = "JEBAT Team"
__license__ = "MIT"

# Lazy imports — heavy modules only load when accessed, not on startup.
# This cuts import time from ~2.6s to <0.1s.

def __getattr__(name):
    """Lazy-load heavy modules only when first accessed."""
    _lazy = {
        # Core
        "AgentFactory": "jebat.core.agents:AgentFactory",
        "AgentOrchestrator": "jebat.core.agents:AgentOrchestrator",
        "CacheManager": "jebat.core.cache:CacheManager",
        "SmartCache": "jebat.core.cache:SmartCache",
        "DecisionEngine": "jebat.core.decision:DecisionEngine",
        "Memory": "jebat.core.memory:Memory",
        "MemoryLayer": "jebat.core.memory:MemoryLayer",
        "MemoryManager": "jebat.core.memory:MemoryManager",
        # Features
        "UltraLoop": "jebat.features.ultra_loop:UltraLoop",
        "UltraThink": "jebat.features.ultra_think:UltraThink",
        "ThinkingMode": "jebat.features.ultra_think:ThinkingMode",
        "Sentinel": "jebat.features.sentinel:Sentinel",
        # Services
        "APIGateway": "jebat.services.api:APIGateway",
        "MCPProtocolServer": "jebat.services.mcp:MCPProtocolServer",
        "webui_router": "jebat.services.webui:webui_router",
        # Integrations
        "ChannelManager": "jebat.integrations.channels:ChannelManager",
        "WebhookSystem": "jebat.integrations.webhooks:WebhookSystem",
        # Database
        "DatabaseManager": "jebat.database:DatabaseManager",
        "RepositoryManager": "jebat.database:RepositoryManager",
        "get_db_models": "jebat.database.models:get_db_models",
        # Skills
        "SkillRegistry": "jebat.skills:SkillRegistry",
        "BaseSkill": "jebat.skills:BaseSkill",
    }
    if name in _lazy:
        module_path, attr = _lazy[name].rsplit(":", 1)
        import importlib
        mod = importlib.import_module(module_path)
        obj = getattr(mod, attr)
        globals()[name] = obj  # cache for next access
        return obj
    raise AttributeError(f"module 'jebat' has no attribute '{name}'")

__all__ = [
    "MemoryManager", "MemoryLayer", "Memory",
    "CacheManager", "SmartCache", "DecisionEngine",
    "AgentOrchestrator", "AgentFactory",
    "UltraLoop", "UltraThink", "ThinkingMode", "Sentinel",
    "APIGateway", "MCPProtocolServer", "webui_router",
    "ChannelManager", "WebhookSystem",
    "DatabaseManager", "RepositoryManager", "get_db_models",
    "SkillRegistry", "BaseSkill",
]