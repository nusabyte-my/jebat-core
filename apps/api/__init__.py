"""
🗡️ JEBAT - Unified AI Assistant Platform

JEBAT (named after the legendary Malay warrior Hang Jebat) is a personal AI assistant
with eternal memory, ultra-reasoning, and continuous learning capabilities.

Version: 2.0.0-refactored
Status: Production Ready
"""

__version__ = "2.0.0"
__author__ = "JEBAT Team"
__license__ = "MIT"

Sentinel = None
ChannelManager = None
WebhookSystem = None
APIGateway = None
MCPProtocolServer = None
webui_router = None
SkillRegistry = None
BaseSkill = None
DatabaseManager = None
RepositoryManager = None
get_db_models = None

try:
    from .core.agents import AgentFactory, AgentOrchestrator
    from .core.cache import CacheManager, SmartCache
    from .core.decision import DecisionEngine
    from .core.memory import Memory, MemoryLayer, MemoryManager
    from .features.ultra_loop import UltraLoop
    from .features.ultra_think import ThinkingMode, UltraThink
except Exception:
    # Lightweight import mode for partial environments.
    pass

try:
    from .database import DatabaseManager, RepositoryManager
    from .database.models import get_db_models
except Exception:
    pass

try:
    from .features.sentinel import Sentinel
except Exception:
    Sentinel = None

try:
    from .integrations.channels import ChannelManager
    from .integrations.webhooks import WebhookSystem
except Exception:
    pass

try:
    from .services.api import APIGateway
    from .services.mcp import MCPProtocolServer
    from .services.webui import webui_router
except Exception:
    pass

try:
    from .skills import BaseSkill, SkillRegistry
except Exception:
    pass

__all__ = [
    # Core
    "MemoryManager",
    "MemoryLayer",
    "Memory",
    "CacheManager",
    "SmartCache",
    "DecisionEngine",
    "AgentOrchestrator",
    "AgentFactory",
    # Features
    "UltraLoop",
    "UltraThink",
    "ThinkingMode",
    "Sentinel",
    # Services
    "APIGateway",
    "MCPProtocolServer",
    "webui_router",
    # Integrations
    "ChannelManager",
    "WebhookSystem",
    # Database
    "DatabaseManager",
    "RepositoryManager",
    # Skills
    "SkillRegistry",
    "BaseSkill",
]
