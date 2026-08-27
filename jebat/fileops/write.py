"""File write with backup and undo support."""

from pathlib import Path
from typing import Any

from .safety import BackupManager


def write_file(path: str, content: str) -> dict[str, Any]:
    """Write content to a file, creating parent dirs and backing up existing content.

    Returns:
        {"written": True, "path": "...", "bytes": N, "backup": "..." or None}
        or {"error": "..."}
    """
    p = Path(path).resolve()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return {"error": f"Failed to create parent directories: {e}"}

    backup = None
    if p.is_file():
        bm = BackupManager()
        backup = bm.backup(str(p))

    try:
        with p.open("w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        return {"error": f"Write failed: {e}"}

    return {
        "written": True,
        "path": str(p),
        "bytes": len(content.encode("utf-8")),
        "backup": backup,
    }


def undo_write(file_path_or_backup: str) -> dict[str, Any]:
    """Restore the most recent backup for a file.

    Returns:
        {"restored": True, "path": "..."} or {"error": "..."}
    """
    bm = BackupManager()
    backups = bm.list_backups(file_path_or_backup)
    if not backups:
        return {"error": "No backups found for this file"}
    try:
        restored = bm.restore(backups[0]["path"])
        return {"restored": True, "path": restored}
    except Exception as e:
        return {"error": f"Undo failed: {e}"}