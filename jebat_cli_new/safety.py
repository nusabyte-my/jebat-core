"""
JEBAT — safety module for dangerous operations.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple


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


# ── Staged command approval (claude-code style) ─────────────────────────────
# Read-only commands run without prompting; state-changing commands prompt once
# per stage per session. A stage remember-list lives in memory only — a new
# session starts the staging cycle over.

STAGE_PATTERNS: List[Tuple[str, str]] = [
    # stage 3 — execute/network (highest friction): one prompt per session
    (r"^\s*(curl|wget)\b", "execute"),
    (r"(^|;|\||&&)\s*(curl|wget)\b", "execute"),
    (r"^\s*(pip|pip3|npm|pnpm|yarn|uv|cargo)\s+(install|add|i)\b", "execute"),
    (r"(git\s+)?push\b", "execute"),
    # stage 2 — write: git commit, package run, docker
    (r"\bgit\s+commit\b", "write"),
    (r"\bgit\s+(merge|rebase|reset|revert|tag)\b", "write"),
    (r"^\s*(npm|pnpm|yarn)\s+run\b", "write"),
    (r"^\s*docker\b", "write"),
    # stage 1 — read-only: no prompt at all
    (r"^\s*(ls|cat|head|tail|grep|rg|find|fd|which|whoami|pwd|echo|date)\b", "read"),
    (r"^\s*git\s+(status|log|diff|show|branch)\b", "read"),
    (r"^\s*(python|python3|node|pytest|uv)\s", "read"),  # running code is read-ish by default
]

_STAGE_WHERE = {"read": 0, "write": 1, "execute": 2}
_STAGE_APPROVED: set = set()


def classify_command_action(command: str) -> str:
    """Classify a shell command into 'read' | 'write' | 'execute'.

    Unrecognized commands classify conservatively as 'write' (one prompt per
    session). Read-only commands never prompt; each higher stage prompts once
    per session before its first command runs.
    """
    for pattern, stage in STAGE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return stage
    return "write"


def _stage_approved(stage: str) -> bool:
    return stage in _STAGE_APPROVED or _STAGE_WHERE.get(stage, 1) == 0


def _remember_stage(stage: str, command: str) -> None:
    if stage and stage != "read":
        _STAGE_APPROVED.add(stage)
