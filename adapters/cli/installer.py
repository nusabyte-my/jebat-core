"""
Core installer logic for JEBAT adapters.
"""

import shutil
from pathlib import Path
from typing import Optional

# Resolve adapter source root (two levels up from cli/)
ADAPTER_ROOT = Path(__file__).parent.parent


def get_src(relative: str) -> Path:
    return ADAPTER_ROOT / relative


def install_to_project(ide_info, target: Path) -> list[str]:
    """Install adapter files into a project directory. Returns list of installed paths."""
    installed = []
    for mapping in ide_info.project_files:
        src = get_src(mapping["src"])
        dest = target / mapping["dest"]
        if not src.exists():
            raise FileNotFoundError(f"Adapter source not found: {src}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        installed.append(str(dest))
    return installed


def install_global(ide_info, override_path: Optional[Path] = None) -> Optional[list[str]]:
    """
    Install to IDE's global config location where supported.
    Returns list of installed paths, or None if not supported.
    """
    cfg = override_path or ide_info.global_config_path
    if not cfg:
        return None

    installed = []
    for mapping in ide_info.project_files:
        src = get_src(mapping["src"])
        dest = cfg / Path(mapping["dest"]).name
        if not src.exists():
            raise FileNotFoundError(f"Adapter source not found: {src}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        installed.append(str(dest))
    return installed


def read_universal_prompt() -> str:
    p = ADAPTER_ROOT / "jebat-universal-prompt.md"
    return p.read_text(encoding="utf-8")
