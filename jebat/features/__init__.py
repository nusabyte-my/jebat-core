"""
JEBAT Features Package

Advanced capabilities and features.
Modules are imported lazily to avoid pulling in
heavy dependencies (SQLAlchemy, Redis, etc.) at
package import time.
"""

from .ultra_think import ThinkingMode, UltraThink

__all__ = ["UltraLoop", "UltraThink", "ThinkingMode"]

def UltraLoop(*args, **kwargs):
    from .ultra_loop import UltraLoop as _UltraLoop
    return _UltraLoop(*args, **kwargs)
