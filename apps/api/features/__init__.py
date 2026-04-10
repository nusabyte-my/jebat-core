"""
JEBAT Features Package

Advanced capabilities and features.
"""

__all__ = ["UltraLoop", "UltraThink", "ThinkingMode"]


def __getattr__(name: str):
    if name == "UltraLoop":
        from .ultra_loop import UltraLoop

        return UltraLoop
    if name in {"UltraThink", "ThinkingMode"}:
        from .ultra_think import ThinkingMode, UltraThink

        return {"UltraThink": UltraThink, "ThinkingMode": ThinkingMode}[name]
    raise AttributeError(name)
