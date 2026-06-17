"""
REPL command — Interactive chat session with AgentLoop tool-calling.
"""

from __future__ import annotations

import asyncio
from typing import Any


def repl_command(args: Any) -> int:
    """Start an interactive REPL session with JEBAT."""
    from jebat.features.repl.repl import ReplLoop
    from jebat.core.agent_loop import SafetyMode

    repl = ReplLoop()

    # Override model/provider if specified
    if getattr(args, "model", None):
        repl._model_override = args.model
    if getattr(args, "provider", None):
        repl._provider_override = args.provider
    if getattr(args, "preset", None):
        repl._preset = args.preset

    # Safety mode
    safety_map = {"auto": SafetyMode.AUTO, "confirm": SafetyMode.CONFIRM, "dangerous": SafetyMode.DANGEROUS}
    repl.safety_mode = safety_map.get(getattr(args, "safety", "auto"), SafetyMode.AUTO)

    # YOLO mode
    if getattr(args, "yolo", False):
        repl.safety_mode = SafetyMode.DANGEROUS

    # Session resume
    if getattr(args, "session", None):
        # This would require ReplLoop to support resuming a specific session
        pass

    try:
        repl.run()
    except KeyboardInterrupt:
        pass
    except EOFError:
        pass
    return 0


__all__ = ["repl_command"]