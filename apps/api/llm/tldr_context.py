from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def build_tldr_summary(project_path: str | Path, symbol: str = "main") -> str | None:
    root = Path(project_path).resolve()
    tldr_bin = _resolve_tldr_binary(root)
    if tldr_bin is None:
        return None
    try:
        result = subprocess.run(
            [str(tldr_bin), "context", symbol, "--project", str(root)],
            capture_output=True,
            text=True,
            timeout=20,
            cwd=root,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    summary = (result.stdout or "").strip()
    if not summary:
        return None
    return (
        f"Project root: {root}\n"
        "Context source: llm-tldr\n"
        f"{summary}"
    )


def _resolve_tldr_binary(root: Path) -> Path | None:
    candidates = [
        root / ".venv-tldr" / "bin" / "tldr",
        root.parent / ".venv-tldr" / "bin" / "tldr",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    discovered = shutil.which("tldr")
    return Path(discovered) if discovered else None
