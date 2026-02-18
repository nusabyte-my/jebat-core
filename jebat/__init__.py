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

# Core components
from jebat.core.agents import AgentFactory, AgentOrchestrator
from jebat.core.cache import CacheManager, SmartCache
from jebat.core.decision import DecisionEngine
from jebat.core.memory import Memory, MemoryLayer, MemoryManager

# Database
from jebat.database import DatabaseManager, RepositoryManager
from jebat.database.models import get_db_models
from jebat.features.sentinel import Sentinel

# Features
from jebat.features.ultra_loop import UltraLoop
from jebat.features.ultra_think import ThinkingMode, UltraThink

# Integrations
from jebat.integrations.channels import ChannelManager
from jebat.integrations.webhooks import WebhookSystem
from jebat.services.api import APIGateway
from jebat.services.mcp import MCPProtocolServer

# Services
from jebat.services.webui import webui_router

# Skills
from jebat.skills import BaseSkill, SkillRegistry

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
