"""
JEBAT Skills System

Base skills and skill registry for extensible capabilities.
"""

try:
    from .base_skill import BaseSkill
except Exception:
    BaseSkill = None

try:
    from .built_in_skills import SkillRegistry
except Exception:
    SkillRegistry = None

from .web_fetch import WebFetchSkill, FetchResult
from .web_search import WebSearchSkill, SearchResult

__all__ = [
    "BaseSkill",
    "SkillRegistry",
    "WebFetchSkill",
    "FetchResult",
    "WebSearchSkill",
    "SearchResult",
]
