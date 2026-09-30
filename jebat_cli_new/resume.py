"""`/resume` — session picker (codex/claude-code style).

Lists recent sessions from ~/.jebat/sessions/session_*.json with previews and
restores the chosen conversation into the live REPL.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SESSIONS_DIR = Path.home() / ".jebat" / "sessions"


def _sessions() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for f in sorted(SESSIONS_DIR.glob("session_*.json"), reverse=True)[:10]:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, list):
            continue
        first_user = next(
            (m.get("content", "") for m in data if isinstance(m, dict) and m.get("role") == "user"),
            "",
        )
        preview = " ".join(str(first_user).split())[:64] or "(no user turns)"
        out.append(
            {
                "file": f,
                "name": f.stem,
                "age_s": time.time() - f.stat().st_mtime,
                "turns": len(data),
                "preview": preview,
            }
        )
    return out


def _age_label(seconds: float) -> str:
    if seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h ago"
    return f"{int(seconds // 86400)}d ago"


def pick() -> Optional[Tuple[Path, List[Dict[str, str]]]]:
    """Render the picker; returns (path, messages) or None."""
    sessions = _sessions()
    if not sessions:
        print("  No saved sessions found.")
        return None
    print("  Recent sessions:")
    for i, s in enumerate(sessions, 1):
        print(f"   {i:>2}. [{_age_label(s['age_s']):>7}] {s['turns']:>3} turns · {s['preview']}")
    try:
        raw = input("  resume # (blank = cancel): ").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        return None
    if not raw.isdigit() or not (1 <= int(raw) <= len(sessions)):
        print("  Cancelled.")
        return None
    chosen = sessions[int(raw) - 1]
    try:
        data = json.loads(chosen["file"].read_text(encoding="utf-8"))
        return chosen["file"], [m for m in data if isinstance(m, dict) and "role" in m]
    except Exception as exc:
        print(f"  Failed to load session: {exc}")
        return None


def load_by_id(session_id: str) -> Optional[Tuple[Path, List[Dict[str, str]]]]:
    """Partial-match load without the interactive picker."""
    for f in sorted(SESSIONS_DIR.glob("session_*.json"), reverse=True):
        if session_id in f.name or session_id in f.stem:
            data = json.loads(f.read_text(encoding="utf-8"))
            return f, [m for m in data if isinstance(m, dict) and "role" in m]
    return None
