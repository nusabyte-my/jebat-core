"""
JEBAT — safety module for dangerous operations.
"""

from __future__ import annotations

import re
from typing import List, Tuple


# Dangerous command patterns
DANGEROUS_PATTERNS: List[Tuple[str, str]] = [
    (r"rm\s+(-rf?|--recursive)\s+/", "Recursive delete from root"),
    (r"rm\s+(-rf?|--recursive)\s+\*", "Recursive delete of all"),
    (r"mkfs\.", "Format disk"),
    (r"dd\s+if=.*of=/dev/", "Direct disk write"),
    (r"shutdown", "System shutdown"),
    (r"reboot", "System reboot"),
    (r"halt", "System halt"),
    (r"init\s+[06]", "System runlevel change"),
    (r"chmod\s+(-R\s+)?777\s+/", "World-writable root permissions"),
    (r"chown\s+(-R\s+)?\S+:\S+\s+/", "Ownership change on root"),
]

# Dangerous file patterns
DANGEROUS_FILES: List[Tuple[str, str]] = [
    (r"/etc/passwd", "System password file"),
    (r"/etc/shadow", "System shadow file"),
    (r"/etc/sudoers", "Sudo configuration"),
    (r"/boot/", "Boot directory"),
    (r"/sys/", "System directory"),
    (r"/proc/", "Process directory"),
]


def is_dangerous_command(command: str) -> Tuple[bool, str]:
    """Check if a command is dangerous. Returns (is_dangerous, reason)."""
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""


def is_dangerous_file(path: str) -> Tuple[bool, str]:
    """Check if a file path is dangerous to modify. Returns (is_dangerous, reason)."""
    for pattern, reason in DANGEROUS_FILES:
        if re.search(pattern, path, re.IGNORECASE):
            return True, reason
    return False, ""


def confirm_action(action: str, details: str = "") -> bool:
    """Prompt user for confirmation. Returns True if approved."""
    prompt = f"JEBAT: {action}"
    if details:
        prompt += f"\n  {details}"
    prompt += "\n  Proceed? [y/N]: "
    try:
        response = input(prompt).strip().lower()
        return response in {"y", "yes"}
    except (KeyboardInterrupt, EOFError):
        print()
        return False
