"""
JEBAT Skills System

Base skills and skill registry for extensible capabilities.
"""

from .base_skill import BaseSkill
from .built_in_skills import SkillRegistry

# Sentinel Security alpha — wire the threat/anomaly analysis skill into the
# global registry so it is discoverable by the agent loop and skill tools.
try:  # noqa: E402
    from jebat.features.sentinel.sentinel import SecurityAnalyzeSkill  # noqa: F401
except Exception:  # pragma: no cover - optional heavy dependency (sklearn)
    pass

__all__ = ["BaseSkill", "SkillRegistry"]
