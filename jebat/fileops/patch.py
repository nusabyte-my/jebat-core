"""Targeted find-and-replace edits with backup."""

from pathlib import Path
from typing import Any

from .safety import BackupManager


def patch_file(
    path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
) -> dict[str, Any]:
    """Replace old_string with new_string in a file.

    Args:
        path: File path.
        old_string: Text to find (must be unique unless replace_all=True).
        new_string: Replacement text.
        replace_all: Replace all occurrences instead of requiring a unique match.

    Returns:
        {"patched": True, "path": "...", "matches": N, "backup": "..." or None}
        or {"error": "..."}
    """
    p = Path(path).resolve()
    if not p.is_file():
        return {"error": f"File not found: {path}"}

    try:
        with p.open("r", encoding="utf-8") as f:
            original = f.read()
    except Exception as e:
        return {"error": f"Read failed: {e}"}

    if old_string not in original:
        return {"error": "old_string not found in file"}

    count = original.count(old_string)
    if count > 1 and not replace_all:
        return {
            "error": (
                f"old_string matches {count} lines. "
                "Provide more context to make it unique, or set replace_all=True."
            )
        }

    # Backup first
    bm = BackupManager()
    backup = bm.backup(str(p))

    patched = original.replace(old_string, new_string)
    try:
        with p.open("w", encoding="utf-8") as f:
            f.write(patched)
    except Exception as e:
        return {"error": f"Write failed: {e}"}

    return {
        "patched": True,
        "path": str(p),
        "matches": count,
        "backup": backup,
    }