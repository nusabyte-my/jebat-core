"""
JEBAT Ultra-Loop

Continuous processing and learning system.
"""

from .ultra_loop import (
    LoopContext,
    LoopMetrics,
    LoopPhase,
    UltraLoop,
    create_ultra_loop,
)

try:
    from .database_repository import UltraLoopRepository
except ImportError:
    UltraLoopRepository = None

__all__ = [
    "UltraLoop",
    "LoopPhase",
    "LoopContext",
    "LoopMetrics",
    "create_ultra_loop",
    "UltraLoopRepository",
]
