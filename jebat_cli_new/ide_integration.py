#!/usr/bin/env python3
"""Detect installed IDEs and safely merge JEBAT's local MCP registration."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


IDE_PATHS = {
    "kiro": (".kiro/settings/mcp.json",),
    "cursor": (".cursor/mcp.json",),
    "vscode": (".vscode/mcp.json",),
    "windsurf": (".windsurf/mcp.json",),
}


def installed_ides(home: Path | None = None) -> list[str]:
    """Detect from user configuration, never by probing or launching IDEs."""
    home = home or Path.home()
    return [name for name, paths in IDE_PATHS.items() if any((home / p).parent.is_dir() for p in paths)]


def merge_server(path: Path, command: str, args: list[str]) -> str:
    """Merge only mcpServers.jebat; preserve all unrelated configuration."""
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid existing JSON: {path}: {exc}") from exc
        if not isinstance(data, dict) or not isinstance(data.get("mcpServers", {}), dict):
            raise ValueError(f"expected a JSON object with mcpServers: {path}")
        backup = path.with_name(f"{path.name}.bak-jebat-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}")
        shutil.copy2(path, backup)
    else:
        data = {}
        backup = None
    servers = data.setdefault("mcpServers", {})
    previous = servers.get("jebat")
    entry = {"command": command, "args": args, "disabled": False}
    if previous == entry:
        return "unchanged"
    if isinstance(previous, dict):
        entry = previous | entry
    servers["jebat"] = entry
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return "updated" if backup else "created"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", required=True)
    parser.add_argument("--arg", action="append", default=[])
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--ide", action="append", choices=[*IDE_PATHS, "auto"], default=[])
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    home = args.home.expanduser().resolve()
    detected = installed_ides(home)
    if args.list:
        print(json.dumps({"detected": detected}, indent=2))
        return 0
    selected = detected if not args.ide or "auto" in args.ide else sorted(set(args.ide))
    if not selected:
        print("No supported IDE configuration directories detected; no files changed.")
        return 0
    failures = 0
    for name in selected:
        path = home / IDE_PATHS[name][0]
        try:
            status = merge_server(path, args.command, args.arg)
            print(f"{name}: {status} {path}")
        except (OSError, ValueError) as exc:
            failures += 1
            print(f"{name}: ERROR: {exc}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
