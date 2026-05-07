"""
JEBAT MCP (Model Context Protocol)

Skill registry and adapter for MCP-based tool serving.
"""

from .skill_registry import Skill, SkillConfig, SkillRegistry

__all__ = ["Skill", "SkillConfig", "SkillRegistry"]
