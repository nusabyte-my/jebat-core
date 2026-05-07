"""
JEBAT Ultra-Think

Deep reasoning and analysis system.
"""

from .ultra_think import (
    ThinkingMode,
    ThinkingPhase,
    ThinkingResult,
    ThinkingTrace,
    ThoughtNode,
    UltraThink,
    create_ultra_think,
)

try:
    from .database_repository import UltraThinkRepository
except ImportError:
    UltraThinkRepository = None

__all__ = [
    "UltraThink",
    "ThinkingMode",
    "ThinkingPhase",
    "ThoughtNode",
    "ThinkingTrace",
    "ThinkingResult",
    "create_ultra_think",
    "UltraThinkRepository",
]
