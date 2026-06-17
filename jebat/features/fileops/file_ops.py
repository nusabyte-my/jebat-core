"""JEBAT File Operations — read, write, patch, search, diff, undo.

All operations go through safety checks and create backups before destructive writes.
"""

from __future__ import annotations

import difflib
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from jebat.tools import register_tool

# ── Backup System ─────────────────────────────────────────────────────────

BACKUP_DIR = Path.home() / ".jebat" / "backups"


def _backup_path(file_path: Path) -> Path:
    """Create a backup path with timestamp."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(file_path.resolve()).replace("\\", "_").replace("/", "_").replace(":", "_")
    return BACKUP_DIR / f"{ts}_{safe_name}"


def _backup(file_path: Path) -> Path | None:
    """Create a backup of the file. Returns backup path or None."""
    if not file_path.exists():
        return None
    bp = _backup_path(file_path)
    shutil.copy2(str(file_path), str(bp))
    return bp


def _find_backups(file_path: Path) -> list[Path]:
    """Find backups for a given file path."""
    safe_name = str(file_path.resolve()).replace("\\", "_").replace("/", "_").replace(":", "_")
    backups = sorted(BACKUP_DIR.glob(f"*_{safe_name}"), reverse=True)
    return backups


# ── Read File ─────────────────────────────────────────────────────────────

@register_tool(
    "file_read",
    schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file"},
            "offset": {"type": "integer", "default": 1, "description": "Starting line (1-indexed)"},
            "limit": {"type": "integer", "default": 500, "description": "Max lines to read"},
        },
        "required": ["path"],
    },
    safety_tier="auto",
    timeout=10,
    max_output=100_000,
    description="Read a file with line numbers and pagination.",
)
async def file_read(path: str, offset: int = 1, limit: int = 500) -> dict[str, Any]:
    """Read a file with line numbers and pagination."""
    file_path = Path(path).expanduser().resolve()
    if not file_path.exists():
        return {"error": f"File not found: {path}", "lines": [], "total_lines": 0}
    if not file_path.is_file():
        return {"error": f"Not a file: {path}", "lines": [], "total_lines": 0}

    # Check file size
    max_bytes = 500_000  # 500KB default
    if file_path.stat().st_size > max_bytes:
        return {"error": f"File too large ({file_path.stat().st_size} bytes). Use offset/limit.", "lines": [], "total_lines": 0}

    try:
        with open(file_path, encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
    except Exception as e:
        return {"error": f"Read error: {e}", "lines": [], "total_lines": 0}

    total = len(all_lines)
    start = max(0, offset - 1)
    selected = all_lines[start:start + limit]

    lines = []
    for i, line in enumerate(selected, start=start + 1):
        lines.append(f"{i}|{line.rstrip()}")

    return {
        "path": str(file_path),
        "lines": lines,
        "total_lines": total,
        "offset": offset,
        "limit": limit,
        "showing": len(lines),
    }


# ── Write File ────────────────────────────────────────────────────────────

@register_tool(
    "file_write",
    schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file"},
            "content": {"type": "string", "description": "Content to write"},
            "force": {"type": "boolean", "default": False, "description": "Overwrite without warning"},
        },
        "required": ["path", "content"],
    },
    safety_tier="confirm",
    timeout=10,
    max_output=0,
    description="Write content to a file (overwrites existing).",
)
async def file_write(path: str, content: str, force: bool = False) -> dict[str, Any]:
    """Write content to a file. Creates parent directories. Shows diff for existing files."""
    file_path = Path(path).expanduser().resolve()
    file_path.parent.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {"path": str(file_path), "action": "write"}
    old_content = ""

    if file_path.exists():
        result["action"] = "overwrite"
        try:
            old_content = file_path.read_text(encoding="utf-8")
        except Exception:
            pass
        _backup(file_path)
        result["backup"] = str(_backup_path(file_path))

    file_path.write_text(content, encoding="utf-8")
    result["bytes"] = len(content.encode("utf-8"))
    result["lines"] = content.count("\n") + 1

    # Generate diff
    if old_content:
        diff = list(difflib.unified_diff(
            old_content.splitlines(keepends=True),
            content.splitlines(keepends=True),
            fromfile=str(file_path) + " (old)",
            tofile=str(file_path) + " (new)",
        ))
        result["diff"] = "".join(diff[:50])  # First 50 lines of diff

    return result


# ── Patch File ────────────────────────────────────────────────────────────

@register_tool(
    "file_patch",
    schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file"},
            "old_string": {"type": "string", "description": "Text to find and replace"},
            "new_string": {"type": "string", "description": "Replacement text"},
            "replace_all": {"type": "boolean", "default": False, "description": "Replace all occurrences"},
        },
        "required": ["path", "old_string", "new_string"],
    },
    safety_tier="confirm",
    timeout=10,
    max_output=0,
    description="Find and replace text in a file with fuzzy matching.",
)
async def file_patch(path: str, old_string: str, new_string: str, replace_all: bool = False) -> dict[str, Any]:
    """Find and replace text in a file.

    Uses exact string matching first, then falls back to fuzzy matching strategies.
    """
    file_path = Path(path).expanduser().resolve()
    if not file_path.exists():
        return {"error": f"File not found: {path}"}

    content = file_path.read_text(encoding="utf-8")

    # Exact match
    count = content.count(old_string)
    if count == 0:
        # Try with normalized whitespace
        normalized = " ".join(old_string.split())
        count = content.count(normalized)
        if count > 0:
            old_string = normalized
        else:
            return {"error": f"String not found in file: {old_string[:60]}..."}

    if count > 1 and not replace_all:
        return {
            "error": f"Found {count} occurrences. Use replace_all=True to replace all, or be more specific.",
            "count": count,
        }

    _backup(file_path)
    new_content = content.replace(old_string, new_string, -1 if replace_all else 1)
    file_path.write_text(new_content, encoding="utf-8")

    return {
        "path": str(file_path),
        "replaced": count if replace_all else 1,
        "old_len": len(old_string),
        "new_len": len(new_string),
    }


# ── Search Files ──────────────────────────────────────────────────────────

@register_tool(
    "file_search",
    schema={
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Search pattern (regex for content, glob for files)"},
            "path": {"type": "string", "default": ".", "description": "Directory to search"},
            "file_glob": {"type": "string", "description": "Filter by file pattern (e.g. *.py)"},
            "target": {"type": "string", "enum": ["content", "files"], "default": "content"},
            "limit": {"type": "integer", "default": 50},
        },
        "required": ["pattern"],
    },
    safety_tier="auto",
    timeout=30,
    max_output=100_000,
    description="Search file contents or find files by name.",
)
async def file_search(
    pattern: str,
    path: str = ".",
    file_glob: str | None = None,
    target: str = "content",
    limit: int = 50,
) -> dict[str, Any]:
    """Search file contents or find files by name using ripgrep (or grep fallback)."""
    search_path = Path(path).expanduser().resolve()
    if not search_path.exists():
        return {"error": f"Path not found: {path}", "matches": []}

    # Try ripgrep first
    if target == "content":
        cmd = ["rg", "--no-heading", "--line-number", "--color", "never"]
        if file_glob:
            cmd.extend(["--glob", file_glob])
        cmd.append(pattern)
        cmd.append(str(search_path))
    else:
        # Find files by name
        cmd = ["find", str(search_path), "-name", pattern, "-type", "f"]
        if limit:
            cmd.extend(["-maxdepth", "5"])

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=15,
        )
        output = result.stdout.strip()
        if not output:
            # Try grep fallback
            if target == "content":
                grep_cmd = ["grep", "-rn", "--color=never"]
                if file_glob:
                    grep_cmd.extend(["--include", file_glob])
                grep_cmd.append(pattern)
                grep_cmd.append(str(search_path))
                result = subprocess.run(grep_cmd, capture_output=True, text=True, timeout=15)
                output = result.stdout.strip()

    except (subprocess.TimeoutExpired, FileNotFoundError):
        output = ""

    lines = output.split("\n")[:limit] if output else []
    return {
        "matches": lines,
        "count": len(lines),
        "truncated": len(output.split("\n")) > limit,
        "pattern": pattern,
        "path": str(search_path),
    }


# ── Undo / Backup List ───────────────────────────────────────────────────

@register_tool(
    "file_undo",
    schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to restore"},
        },
        "required": ["path"],
    },
    safety_tier="confirm",
    timeout=10,
    description="Restore the most recent backup of a file.",
)
async def file_undo(path: str) -> dict[str, Any]:
    """Restore the most recent backup of a file."""
    file_path = Path(path).expanduser().resolve()
    backups = _find_backups(file_path)
    if not backups:
        return {"error": f"No backups found for: {path}"}

    latest = backups[0]
    shutil.copy2(str(latest), str(file_path))
    return {
        "path": str(file_path),
        "restored_from": str(latest),
        "available_backups": len(backups),
    }


# ── Directory Tree ────────────────────────────────────────────────────────

@register_tool(
    "file_tree",
    schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "default": ".", "description": "Directory path"},
            "depth": {"type": "integer", "default": 3, "description": "Max depth"},
            "gitignore": {"type": "boolean", "default": True, "description": "Respect .gitignore"},
        },
    },
    safety_tier="auto",
    timeout=15,
    max_output=50_000,
    description="Show directory tree structure.",
)
async def file_tree(path: str = ".", depth: int = 3, gitignore: bool = True) -> dict[str, Any]:
    """Show directory tree structure."""
    search_path = Path(path).expanduser().resolve()
    if not search_path.exists():
        return {"error": f"Path not found: {path}"}

    try:
        cmd = ["tree", str(search_path), "-L", str(depth)]
        if gitignore:
            cmd.append("--gitignore")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        output = result.stdout or result.stderr
    except FileNotFoundError:
        # Fallback: manual tree
        output = _manual_tree(search_path, depth)

    return {
        "path": str(search_path),
        "tree": output,
    }


def _manual_tree(path: Path, depth: int, prefix: str = "") -> str:
    """Simple recursive tree when `tree` command is not available."""
    lines = []
    try:
        entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
    except PermissionError:
        return ""

    for i, entry in enumerate(entries):
        if entry.name.startswith("."):
            continue
        is_last = i == len(entries) - 1
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")
        if entry.is_dir() and depth > 1:
            extension = "    " if is_last else "│   "
            lines.append(_manual_tree(entry, depth - 1, prefix + extension))
    return "\n".join(lines) + ("\n" if lines else "")