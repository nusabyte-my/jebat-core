"""
JEBAT Built-in Skills

Skill registry and built-in skill implementations.
"""

from typing import Dict, List, Optional

from .base_skill import BaseSkill


class SkillRegistry:
    """
    Skill registry for managing available skills.

    This is a minimal implementation for now.
    """

    def __init__(self):
        """Initialize the skill registry."""
        self._skills: Dict[str, BaseSkill] = {}
        self._enabled: List[str] = []

    def register(self, skill: BaseSkill):
        """Register a skill."""
        self._skills[skill.name] = skill
        self._enabled.append(skill.name)

    def get(self, name: str) -> Optional[BaseSkill]:
        """Get a skill by name."""
        return self._skills.get(name)

    def list_skills(self) -> List[str]:
        """List all registered skills."""
        return list(self._skills.keys())

    def enable(self, name: str):
        """Enable a skill."""
        if name in self._skills:
            self._enabled.append(name)

    def disable(self, name: str):
        """Disable a skill."""
        if name in self._enabled:
            self._enabled.remove(name)


__all__ = ["SkillRegistry"]
