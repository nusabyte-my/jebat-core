"""JEBAT Undo/Rollback — File backup before destructive operations.

Every file write/patch creates a .bak snapshot first:
  - Automatic backup before write, patch, or delete
  - Rollback to any previous version
  - Diff between current and backup
  - Backup rotation (keep last N versions)

This is the TukangRestore — the safety net for the agent's actions.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any


# ── Backup Storage ────────────────────────────────────────────────────────

BACKUP_DIR = os.path.expanduser("~/.jebat/backups")
MAX_BACKUPS_PER_FILE = 10  # Keep last 10 versions


@dataclass(slots=True)
class FileSnapshot:
    """A snapshot of a file at a point in time."""
    path: str
    content: str = ""
    timestamp: str = ""
    checksum: str = ""
    size: int = 0
    operation: str = ""  # write, patch, delete


@dataclass(slots=True)
class UndoResult:
    """Result of an undo/rollback operation."""
    success: bool = False
    restored_path: str = ""
    backup_path: str = ""
    diff: str = ""
    message: str = ""


def _backup_dir_for(path: str) -> str:
    """Get the backup directory for a given file path."""
    # Create a safe directory name from the file path
    safe_name = path.replace(os.sep, "_").replace("/", "_").replace(":", "_")
    return os.path.join(BACKUP_DIR, safe_name)


def _checksum(content: str) -> str:
    """Calculate SHA256 checksum of content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def auto_backup(path: str, operation: str = "write") -> FileSnapshot | None:
    """Create an automatic backup of a file before modification.

    Args:
        path: File path to backup
        operation: Type of operation that triggered the backup

    Returns:
        FileSnapshot if file exists, None if file doesn't exist yet
    """
    if not os.path.exists(path):
        return None

    # Read current content
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return None

    snapshot = FileSnapshot(
        path=path,
        content=content,
        timestamp=datetime.now().isoformat(),
        checksum=_checksum(content),
        size=len(content),
        operation=operation,
    )

    # Save backup
    backup_dir = _backup_dir_for(path)
    os.makedirs(backup_dir, exist_ok=True)

    # Rotate old backups — keep only MAX_BACKUPS_PER_FILE
    existing = sorted(
        [f for f in os.listdir(backup_dir) if f.endswith(".bak")],
        key=lambda f: f,
    )
    if len(existing) >= MAX_BACKUPS_PER_FILE:
        for old in existing[:len(existing) - MAX_BACKUPS_PER_FILE + 1]:
            os.remove(os.path.join(backup_dir, old))

    # Write backup file
    timestamp_safe = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{timestamp_safe}_{operation}_{snapshot.checksum}.bak"
    backup_path = os.path.join(backup_dir, backup_name)

    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Save metadata
    meta_path = os.path.join(backup_dir, backup_name + ".meta")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({
            "path": path,
            "timestamp": snapshot.timestamp,
            "checksum": snapshot.checksum,
            "size": snapshot.size,
            "operation": operation,
        }, f, indent=2)

    return snapshot


def undo(path: str, version: int = -1) -> UndoResult:
    """Undo the last change to a file (rollback to previous version).

    Args:
        path: File path to rollback
        version: Version to restore (-1 = latest backup, -2 = second latest, etc.)

    Returns:
        UndoResult with success status and diff
    """
    backup_dir = _backup_dir_for(path)

    if not os.path.exists(backup_dir):
        return UndoResult(message=f"No backups found for {path}")

    # Get sorted backup files (newest first)
    backups = sorted(
        [f for f in os.listdir(backup_dir) if f.endswith(".bak")],
        key=lambda f: f,
        reverse=True,
    )

    if not backups:
        return UndoResult(message=f"No backup files in {backup_dir}")

    # Select version
    idx = abs(version) - 1  # -1 → 0 (latest), -2 → 1 (second latest)
    if idx >= len(backups):
        return UndoResult(message=f"Only {len(backups)} versions available, requested version {version}")

    backup_name = backups[idx]
    backup_path = os.path.join(backup_dir, backup_name)

    # Read backup content
    try:
        with open(backup_path, "r", encoding="utf-8") as f:
            backup_content = f.read()
    except OSError as e:
        return UndoResult(message=f"Failed to read backup: {e}")

    # Read current content (if exists) for diff
    current_content = ""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                current_content = f.read()
        except OSError:
            pass

    # Create diff
    diff_lines = list(difflib.unified_diff(
        current_content.splitlines(keepends=True),
        backup_content.splitlines(keepends=True),
        fromfile=f"current ({path})",
        tofile=f"backup ({backup_name})",
    ))
    diff_text = "".join(diff_lines) if diff_lines else "No differences"

    # Backup current version before restoring (so we can undo the undo)
    auto_backup(path, operation="undo")

    # Restore backup
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(backup_content)
    except OSError as e:
        return UndoResult(message=f"Failed to restore: {e}")

    return UndoResult(
        success=True,
        restored_path=path,
        backup_path=backup_path,
        diff=diff_text,
        message=f"Restored {path} from {backup_name}",
    )


def list_backups(path: str) -> list[dict[str, Any]]:
    """List all available backups for a file.

    Args:
        path: File path to check backups for

    Returns:
        List of backup metadata dicts (newest first)
    """
    backup_dir = _backup_dir_for(path)

    if not os.path.exists(backup_dir):
        return []

    backups = []
    for f in sorted(os.listdir(backup_dir), reverse=True):
        if f.endswith(".bak.meta"):
            meta_path = os.path.join(backup_dir, f)
            try:
                with open(meta_path, "r", encoding="utf-8") as fh:
                    meta = json.load(fh)
                    meta["backup_file"] = f.replace(".meta", "")
                    backups.append(meta)
            except (OSError, json.JSONDecodeError):
                continue

    return backups


def diff_backup(path: str, version: int = -1) -> str:
    """Show diff between current file and a backup version.

    Args:
        path: File path
        version: Backup version to compare against (-1 = latest backup)

    Returns:
        Unified diff string
    """
    backup_dir = _backup_dir_for(path)

    if not os.path.exists(backup_dir):
        return f"No backups found for {path}"

    backups = sorted(
        [f for f in os.listdir(backup_dir) if f.endswith(".bak")],
        key=lambda f: f,
        reverse=True,
    )

    idx = abs(version) - 1
    if idx >= len(backups):
        return f"Only {len(backups)} versions available"

    backup_path = os.path.join(backup_dir, backups[idx])

    with open(backup_path, "r", encoding="utf-8") as f:
        backup_content = f.read()

    current_content = ""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            current_content = f.read()

    diff_lines = list(difflib.unified_diff(
        current_content.splitlines(keepends=True),
        backup_content.splitlines(keepends=True),
        fromfile="current",
        tofile=f"backup v{version}",
    ))

    return "".join(diff_lines) if diff_lines else "No differences"


def purge_backups(path: str | None = None) -> dict[str, int]:
    """Purge backup files.

    Args:
        path: Specific file path to purge, or None to purge all

    Returns:
        Dict with count of purged files
    """
    count = 0

    if path:
        backup_dir = _backup_dir_for(path)
        if os.path.exists(backup_dir):
            for f in os.listdir(backup_dir):
                os.remove(os.path.join(backup_dir, f))
                count += 1
    else:
        if os.path.exists(BACKUP_DIR):
            for dir_name in os.listdir(BACKUP_DIR):
                sub_dir = os.path.join(BACKUP_DIR, dir_name)
                if os.path.isdir(sub_dir):
                    for f in os.listdir(sub_dir):
                        os.remove(os.path.join(sub_dir, f))
                        count += 1

    return {"purged": count}


# ── Undo Tools Registry ──────────────────────────────────────────────────

UNDO_TOOLS: dict[str, dict[str, Any]] = {
    "auto_backup": {
        "description": "Create automatic backup of a file before modification",
        "safety": "auto",
        "handler": auto_backup,
        "parameters": {
            "path": {"type": "string", "description": "File path to backup"},
            "operation": {"type": "string", "description": "Operation type (write/patch/delete)"},
        },
    },
    "undo": {
        "description": "Undo last change to a file (rollback to previous version)",
        "safety": "auto",
        "handler": undo,
        "parameters": {
            "path": {"type": "string", "description": "File path to rollback"},
            "version": {"type": "integer", "description": "Version (-1=latest, -2=2nd latest)"},
        },
    },
    "list_backups": {
        "description": "List all available backups for a file",
        "safety": "auto",
        "handler": list_backups,
        "parameters": {"path": {"type": "string", "description": "File path"}},
    },
    "diff_backup": {
        "description": "Show diff between current file and backup version",
        "safety": "auto",
        "handler": diff_backup,
        "parameters": {
            "path": {"type": "string"},
            "version": {"type": "integer", "default": -1},
        },
    },
    "purge_backups": {
        "description": "Purge backup files (specific path or all)",
        "safety": "confirm",
        "handler": purge_backups,
        "parameters": {"path": {"type": "string", "description": "Path or empty for all"}},
    },
}


def list_undo_tools() -> list[dict[str, str]]:
    """List all undo/rollback tools."""
    return [
        {"name": name, "description": info["description"], "safety": info["safety"]}
        for name, info in UNDO_TOOLS.items()
    ]

# ── Register with JEBAT tool system ────────────────────────────────────────
from jebat.tools import register_tool  # noqa: E402
register_tool(
    "undo_backup",
    handler=auto_backup,
    description="Create backup of a file before modification. Call before write/patch/delete.",
    schema={"path": {"type": "string"}, "operation": {"type": "string"}},
)
register_tool(
    "undo_rollback",
    handler=undo,
    description="Undo the last change to a file — restore from latest backup.",
    schema={"path": {"type": "string"}, "version": {"type": "integer", "default": -1}},
)
register_tool(
    "undo_list",
    handler=list_backups,
    description="List all available backups for a file (newest first).",
    schema={"path": {"type": "string"}},
)
register_tool(
    "undo_diff",
    handler=diff_backup,
    description="Show diff between current file and a backup version.",
    schema={"path": {"type": "string"}, "version": {"type": "integer", "default": -1}},
)
register_tool(
    "undo_purge",
    handler=purge_backups,
    description="Delete backup files — specific path or all.",
    schema={"path": {"type": "string", "description": "Specific file path, or omit to purge all"}},
)
