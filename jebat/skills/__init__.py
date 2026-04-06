"""
JEBAT Skills System

Base skills and skill registry for extensible capabilities.
"""

from .base_skill import BaseSkill
from .built_in_skills import SkillRegistry

__all__ = ["BaseSkill", "SkillRegistry"]
