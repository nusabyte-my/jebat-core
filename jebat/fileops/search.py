"""Regex-based file content search, or glob file-name search."""

import re
from pathlib import Path
from typing import Any


def search_files(
    pattern: str,
    target: str = "content",
    path: str = ".",
    file_glob: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Search file contents (target='content') or find files by glob (target='files').

    Returns:
        {"matches": [{"path": "...", "line": N, "content": "..."}, ...]}
        or {"error": "..."}
    """
    root = Path(path).resolve()
    if not root.exists():
        return {"error": f"Path not found: {path}"}

    if target == "files":
        # Glob search — find files by name
        matches = []
        for f in root.rglob(pattern):
            if f.is_file():
                matches.append({"path": str(f.resolve())})
                if len(matches) >= limit:
                    break
        return {"matches": matches}

    if target == "content":
        # Regex content search inside files
        try:
            regex = re.compile(pattern)
        except re.Error as e:
            return {"error": f"Invalid regex: {e}"}

        matches = []
        # Walk files, optionally filtered by file_glob
        walker = root.rglob("**/*") if file_glob is None else root.rglob(file_glob)
        for f in walker:
            if not f.is_file():
                continue
            # Skip known binary extensions
            if f.suffix in (
                ".exe", ".dll", ".bin", ".png", ".jpg", ".jpeg", ".gif",
                ".mp4", ".mp3", ".wav", ".zip", ".tar", ".gz",
            ):
                continue
            try:
                with f.open("r", encoding="utf-8", errors="replace") as fh:
                    for line_no, line in enumerate(fh, start=1):
                        if regex.search(line):
                            matches.append(
                                {
                                    "path": str(f.resolve()),
                                    "line": line_no,
                                    "content": line.rstrip("\n"),
                                }
                            )
                            if len(matches) >= limit:
                                return {"matches": matches}
            except (OSError, PermissionError):
                continue
        return {"matches": matches}

    return {"error": f"Unknown target: {target}"}