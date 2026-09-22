"""JEBAT Terminal Execution — shell commands, background processes, PTY mode.

Implementations live in :mod:`.terminal_exec` and self-register via
@register_tool at import time. The package must import that submodule or
`import jebat.features.terminal` registers nothing and the MCP server exposes
no shell/process tools at all.
"""

from __future__ import annotations

from .terminal_exec import (
    process_kill,
    process_list,
    process_log,
    process_write,
    terminal,
    terminal_bg,
)

__all__ = [
    "process_kill",
    "process_list",
    "process_log",
    "process_write",
    "terminal",
    "terminal_bg",
]
