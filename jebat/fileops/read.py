"""File read with line numbers and pagination."""

from pathlib import Path
from typing import Any


MAX_FILE_READ = 100_000  # chars


def read_file(path: str, offset: int = 1, limit: int = 500) -> dict[str, Any]:
    """Read a text file with line numbers. Lines are 1-indexed.

    Returns:
        {"content": "1|line1\\n2|line2\\n...", "total_lines": N}
        or {"error": "..."}
    """
    p = Path(path)
    if not p.is_file():
        return {"error": f"File not found: {path}"}
    if not p.suffix or p.suffix in (".exe", ".dll", ".bin", ".png", ".jpg", ".mp4"):
        return {"error": f"Cannot read binary file: {path}"}

    try:
        with p.open("r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        return {"error": f"Read failed: {e}"}

    total_lines = len(lines)
    if offset < 1:
        offset = 1
    if offset > total_lines:
        return {"content": "", "total_lines": total_lines}

    end = min(offset + limit - 1, total_lines)
    selected = lines[offset - 1 : end]

    numbered_lines = []
    total_chars = 0
    for i, line in enumerate(selected, start=offset):
        numbered_line = f"{i}|{line}"
        if total_chars + len(numbered_line) > MAX_FILE_READ:
            numbered_lines.append(f"{i}|... [truncated, {MAX_FILE_READ} char limit]")
            break
        numbered_lines.append(numbered_line)
        total_chars += len(numbered_line)

    return {"content": "".join(numbered_lines).rstrip("\n"), "total_lines": total_lines}