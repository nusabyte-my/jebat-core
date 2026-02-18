"""
Multi-Agent Automation System
A comprehensive framework for creating, managing, and orchestrating multiple intelligent agents.

This package provides:
- Base agent and skill frameworks
- Specialized agents (DataAgent, WebAgent)
- Reusable skills (FileProcessing, APICommunication)
- Agent management and orchestration
- Configuration management
- Examples and utilities

Usage:
    from agents.data_agent import DataAgent
    from skills.file_processing_skill import FileProcessingSkill
    from automation.agent_manager import AgentManager

    # Create and configure agents
    agent = DataAgent("agent_001", "My Data Agent")
    skill = FileProcessingSkill()
    agent.add_skill("file_ops", skill)

    # Use agent manager for coordination
    manager = AgentManager()
    manager.register_agent(agent)
"""

__version__ = "1.0.0"
__author__ = "Multi-Agent System Developer"
__email__ = "developer@example.com"
__description__ = "Multi-Agent Automation System Framework"

# Import main components for easy access
try:
    from .agents.base_agent import AgentMessage, AgentResult, AgentStatus, BaseAgent

    # Import concrete implementations
    from .agents.data_agent import DataAgent
    from .agents.web_agent import WebAgent
    from .automation.agent_manager import AgentManager, TaskQueue
    from .config.config_manager import ConfigFormat, ConfigManager, ConfigScope
    from .skills.api_communication_skill import APICommunicationSkill
    from .skills.base_skill import BaseSkill, SkillParameter, SkillResult, SkillType
    from .skills.file_processing_skill import FileProcessingSkill

    __all__ = [
        # Base classes
        "BaseAgent",
        "BaseSkill",
        "AgentManager",
        "ConfigManager",
        # Enums and data classes
        "AgentResult",
        "AgentStatus",
        "AgentMessage",
        "SkillResult",
        "SkillType",
        "SkillParameter",
        "ConfigFormat",
        "ConfigScope",
        "TaskQueue",
        # Concrete implementations
        "DataAgent",
        "WebAgent",
        "FileProcessingSkill",
        "APICommunicationSkill",
    ]

except ImportError as e:
    # Handle import errors gracefully during development
    import warnings

    warnings.warn(f"Some components could not be imported: {e}", ImportWarning)
    __all__ = []

# Package metadata
__package_info__ = {
    "name": "multi-agent-system",
    "version": __version__,
    "description": __description__,
    "author": __author__,
    "python_requires": ">=3.8",
    "keywords": ["automation", "agents", "multi-agent", "tasks", "orchestration"],
    "classifiers": [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
        "Topic :: Office/Business :: Scheduling",
    ],
}


def get_version():
    """Return the current version of the package."""
    return __version__


def get_package_info():
    """Return package metadata information."""
    return __package_info__.copy()
