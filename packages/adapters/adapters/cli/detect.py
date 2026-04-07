"""
IDE detection for JEBAT installer.
Checks common install paths on Windows, macOS, Linux.
"""

import os
import sys
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

HOME = Path.home()
APPDATA = Path(os.environ.get("APPDATA", HOME / "AppData" / "Roaming"))
LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", HOME / "AppData" / "Local"))
IS_WINDOWS = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"


@dataclass
class IDEInfo:
    key: str
    name: str
    detected: bool
    install_path: Optional[Path]
    global_config_path: Optional[Path]
    project_files: list[dict] = field(default_factory=list)
    global_note: str = ""


def _exists_any(*paths) -> Optional[Path]:
    for p in paths:
        if p is None:
            continue
        p = Path(p)
        if p.exists():
            return p
    return None


def detect_cursor() -> IDEInfo:
    paths = [
        LOCALAPPDATA / "Programs" / "cursor",
        LOCALAPPDATA / "cursor",
        Path("/Applications/Cursor.app"),
        Path("/usr/bin/cursor"),
        shutil.which("cursor"),
    ]
    install = _exists_any(*[p for p in paths if p])
    detected = install is not None or shutil.which("cursor") is not None

    # Cursor global rules: %APPDATA%\Cursor\User\settings.json
    global_cfg = _exists_any(
        APPDATA / "Cursor" / "User",
        HOME / ".config" / "Cursor" / "User",
        HOME / "Library" / "Application Support" / "Cursor" / "User",
    )

    return IDEInfo(
        key="cursor",
        name="Cursor",
        detected=detected,
        install_path=install,
        global_config_path=global_cfg,
        project_files=[
            {"src": "cursor/.cursorrules", "dest": ".cursorrules"},
        ],
        global_note="Cursor global rules are set via Settings → AI → Rules for AI (manual paste).",
    )


def detect_vscode() -> IDEInfo:
    paths = [
        LOCALAPPDATA / "Programs" / "Microsoft VS Code",
        Path("/Applications/Visual Studio Code.app"),
        Path("/usr/bin/code"),
        shutil.which("code"),
    ]
    install = _exists_any(*[p for p in paths if p])
    detected = install is not None or shutil.which("code") is not None

    global_cfg = _exists_any(
        APPDATA / "Code" / "User",
        HOME / ".config" / "Code" / "User",
        HOME / "Library" / "Application Support" / "Code" / "User",
    )

    return IDEInfo(
        key="vscode",
        name="VS Code (Copilot)",
        detected=detected,
        install_path=install,
        global_config_path=global_cfg,
        project_files=[
            {"src": "vscode/copilot-instructions.md", "dest": ".github/copilot-instructions.md"},
        ],
        global_note="VS Code Copilot instructions are project-scoped only (.github/copilot-instructions.md).",
    )


def detect_zed() -> IDEInfo:
    paths = [
        LOCALAPPDATA / "Zed",
        Path("/Applications/Zed.app"),
        Path("/usr/bin/zed"),
        shutil.which("zed"),
    ]
    install = _exists_any(*[p for p in paths if p])
    detected = install is not None or shutil.which("zed") is not None

    global_cfg = _exists_any(
        HOME / ".config" / "zed",
        HOME / "AppData" / "Roaming" / "Zed",
        HOME / "Library" / "Application Support" / "Zed",
    )

    return IDEInfo(
        key="zed",
        name="Zed",
        detected=detected,
        install_path=install,
        global_config_path=global_cfg,
        project_files=[
            {"src": "zed/system-prompt.md", "dest": ".zed/jebat-system-prompt.md"},
        ],
        global_note="Zed global prompt: paste into ~/.config/zed/settings.json → assistant.default_context_server_params or system_prompt.",
    )


def detect_trae() -> IDEInfo:
    paths = [
        LOCALAPPDATA / "Programs" / "trae",
        LOCALAPPDATA / "trae",
        Path("/Applications/Trae.app"),
        shutil.which("trae"),
    ]
    install = _exists_any(*[p for p in paths if p])
    detected = install is not None or shutil.which("trae") is not None

    return IDEInfo(
        key="trae",
        name="Trae",
        detected=detected,
        install_path=install,
        global_config_path=None,
        project_files=[
            {"src": "generic/JEBAT.md", "dest": ".trae/jebat-context.md"},
        ],
        global_note="Trae: paste SYSTEM PROMPT block into Trae's custom instructions field.",
    )


def detect_antigravity() -> IDEInfo:
    paths = [
        LOCALAPPDATA / "Programs" / "antigravity",
        Path("/Applications/Antigravity.app"),
        shutil.which("antigravity"),
    ]
    install = _exists_any(*[p for p in paths if p])
    detected = install is not None or shutil.which("antigravity") is not None

    return IDEInfo(
        key="antigravity",
        name="Antigravity",
        detected=detected,
        install_path=install,
        global_config_path=None,
        project_files=[
            {"src": "generic/JEBAT.md", "dest": ".antigravity/jebat-context.md"},
        ],
        global_note="Antigravity: paste SYSTEM PROMPT block into AI context field.",
    )


def detect_all() -> dict[str, IDEInfo]:
    detectors = [
        detect_cursor,
        detect_vscode,
        detect_zed,
        detect_trae,
        detect_antigravity,
    ]
    return {fn().key: fn() for fn in detectors}
