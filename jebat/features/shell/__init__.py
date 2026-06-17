"""JEBAT Shell/File/Code Tools — TukangKod (Code Builder).

Core tools the AgentLoop calls to actually DO work:
  - Terminal command execution
  - File read/write/patch/search
  - Code execution (Python/Bash/JS)
  - Process management
"""

from jebat.features.shell.shell_tools import (
    TerminalResult,
    terminal_exec,
    CodeResult,
    code_exec,
    file_read,
    file_write,
    file_patch,
    file_search,
    SHELL_TOOLS,
    list_shell_tools,
)

__all__ = [
    "TerminalResult", "terminal_exec",
    "CodeResult", "code_exec",
    "file_read", "file_write", "file_patch", "file_search",
    "SHELL_TOOLS", "list_shell_tools",
]