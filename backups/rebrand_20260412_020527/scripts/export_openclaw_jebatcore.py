#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = Path.home() / ".openclaw"
TARGET_ROOT = REPO_ROOT / "integrations" / "openclaw"
WORKSPACE_TARGET = TARGET_ROOT / "workspace"
WORKSPACE_FILES = [
    "IDENTITY.md",
    "BOOTSTRAP.md",
    "SOUL.md",
    "USER.md",
    "TOOLS.md",
    "AGENTS.md",
    "ORCHESTRA.md",
]


def replace_home(value: str) -> str:
    return value.replace(str(Path.home()), "~")


def sanitize_json(value):
    if isinstance(value, dict):
        return {k: sanitize_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_json(item) for item in value]
    if isinstance(value, str):
        return replace_home(value)
    return value


def export_config() -> None:
    source_path = SOURCE_ROOT / "openclaw.json"
    data = json.loads(source_path.read_text())
    exported = {
        "gateway": sanitize_json(data.get("gateway", {})),
        "env": sanitize_json(data.get("env", {})),
        "channels": sanitize_json(data.get("channels", {})),
        "plugins": {
            "installs": sanitize_json(data.get("plugins", {}).get("installs", {})),
        },
        "agents": {
            "defaults": sanitize_json(data.get("agents", {}).get("defaults", {})),
            "list": sanitize_json(data.get("agents", {}).get("list", [])),
        },
    }
    (TARGET_ROOT / "openclaw.template.json").write_text(json.dumps(exported, indent=2) + "\n")


def export_workspace() -> None:
    source_workspace = SOURCE_ROOT / "workspace"
    WORKSPACE_TARGET.mkdir(parents=True, exist_ok=True)
    for name in WORKSPACE_FILES:
        (WORKSPACE_TARGET / name).write_text((source_workspace / name).read_text())

    source_skill = source_workspace / "skills" / "hermes-agent" / "SKILL.md"
    target_skill = WORKSPACE_TARGET / "skills" / "hermes-agent"
    target_skill.mkdir(parents=True, exist_ok=True)
    (target_skill / "SKILL.md").write_text(source_skill.read_text())


def main() -> None:
    TARGET_ROOT.mkdir(parents=True, exist_ok=True)
    export_config()
    export_workspace()
    print(f"Exported JEBATCore OpenClaw bundle to {TARGET_ROOT}")


if __name__ == "__main__":
    main()
