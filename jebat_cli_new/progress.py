"""Cross-layer progress reporting (ContextVar-based).

The MCP server sets a reporter callback around long-running tool calls
(agent_execute, ghost_sql, ...); inner loops (the ReAct agent's iteration
loop) report fractional progress without knowing about JSON-RPC. Everything
degrades to a no-op when no reporter is active (CLI, tests, direct calls).
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Callable, Optional

Reporter = Callable[[float, str], None]

PROGRESS_REPORTER: ContextVar[Optional[Reporter]] = ContextVar(
    "jebat_progress_reporter", default=None
)


def report(progress: float, message: str = "") -> bool:
    """Report fractional progress (0.0-1.0). Returns True if delivered."""
    cb = PROGRESS_REPORTER.get()
    if cb is None:
        return False
    try:
        cb(min(max(float(progress), 0.0), 1.0), message)
        return True
    except Exception:
        return False
