"""`jebat config` subcommand — import configuration from other CLI tools.

Brings MCP server definitions from omp, opencode, or Claude Code into the
JEBAT runtime config (`~/.jebat/config.yaml`, `mcp.servers` list) so one
setup serves every surface.

Source adapters (all auto-detected from their default homes):
- omp        ~/.omp/agent/mcp.json     {mcpServers: {name: {type: stdio|http, command, args, env, url, headers, enabled, timeout(ms)}}}
- opencode   ~/.config/opencode/opencode.json   {mcp: {name: {type: local|remote, command: [..], environment, url, headers, enabled, timeout(ms)}}}
- claude     ~/.claude.json | ~/.claude/settings.json   {mcpServers: {name: {command, args, env}}}
- any path   file with either shape (auto-sniffed)

Normalizations applied:
- transport:  stdio/local -> "stdio", http/remote -> "http" (url presence decides when type is absent)
- command:    opencode's argv-array form becomes command + args
- env:        opencode's "environment" key -> env; "{env:VAR}" -> "${VAR}"
- timeout:    milliseconds -> seconds (values >1000 treated as ms)
- names:      collision with an existing server skips the entry unless --overwrite

The target config is backed up (config.yaml.bak-<timestamp>-import) before any
write; --dry-run prints the converted servers without touching disk.
"""

from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import yaml

from jebat_cli_new.theme import C, cprint


JEBAT_CONFIG_PATH = Path.home() / ".jebat" / "config.yaml"
MANIFEST_KEY = "mcp"

_SOURCE_DEFAULTS: Dict[str, List[Path]] = {
    "omp": [Path.home() / ".omp" / "agent" / "mcp.json", Path.home() / ".omp" / "mcp.json"],
    "opencode": [Path.home() / ".config" / "opencode" / "opencode.json"],
    "claude": [Path.home() / ".claude.json", Path.home() / ".claude" / "settings.json"],
}


# ── Source parsing ──────────────────────────────────────────────────────────


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_omp(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """omp mcp.json: {mcpServers: {name: cfg}}."""
    raw = data.get("mcpServers", {})
    return {name: dict(cfg) for name, cfg in raw.items() if isinstance(cfg, dict)}


def _parse_opencode(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """opencode.json: {mcp: {name: cfg}} with local/remote semantics."""
    raw = data.get("mcp", {})
    return {name: dict(cfg) for name, cfg in raw.items() if isinstance(cfg, dict)}


def _parse_claude(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """claude.json / settings.json: {mcpServers: {name: cfg}} (stdio-centric)."""
    raw = data.get("mcpServers", {})
    return {name: dict(cfg) for name, cfg in raw.items() if isinstance(cfg, dict)}


def _sniff_parse(data: Dict[str, Any]) -> Tuple[str, Dict[str, Dict[str, Any]]]:
    """Auto-detect which shape a JSON blob uses."""
    if "mcpServers" in data:
        return "claude/omp", _parse_claude(data)
    if "mcp" in data and isinstance(data["mcp"], dict):
        return "opencode", _parse_opencode(data)
    raise ValueError("unrecognized config shape: no 'mcpServers' or 'mcp' key")


def _load_source(source: str, path: Optional[str]) -> Tuple[str, Path, Dict[str, Dict[str, Any]]]:
    """Locate and parse the source config. Returns (kind, path, servers)."""
    if path:
        p = Path(path).expanduser()
        if not p.exists():
            raise FileNotFoundError(f"source config not found: {p}")
        data = _read_json(p)
        kind, servers = _sniff_parse(data)
        return kind, p, servers

    candidates = _SOURCE_DEFAULTS.get(source)
    if not candidates:
        raise ValueError(f"unknown source '{source}' (use omp | opencode | claude | --path)")
    for p in candidates:
        if p.exists():
            data = _read_json(p)
            if source == "opencode":
                return "opencode", p, _parse_opencode(data)
            if source == "omp":
                return "omp", p, _parse_omp(data)
            return "claude", p, _parse_claude(data)
    raise FileNotFoundError(
        f"no config found for source '{source}'; tried: "
        + ", ".join(str(c) for c in candidates)
    )


# ── Conversion to JEBAT schema ──────────────────────────────────────────────


def _normalize_timeout(value: Any) -> int:
    """omp/opencode use ms; JEBAT uses seconds. >1000 is treated as ms."""
    try:
        t = int(value)
    except (TypeError, ValueError):
        return 30
    if t > 1000:
        return max(1, t // 1000)
    return t if t > 0 else 30


def _normalize_env(env: Any) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for k, v in (env or {}).items():
        if not isinstance(v, str):
            v = str(v)
        # opencode template style "{env:VAR}" -> JEBAT "${VAR}"
        if v.startswith("{env:") and v.endswith("}"):
            v = "${" + v[5:-1] + "}"
        out[k] = v
    return out


def _convert(name: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Convert one source entry to a JEBAT mcp.servers entry."""
    kind = str(cfg.get("type", "")).lower()
    url = str(cfg.get("url", "") or "")
    command = cfg.get("command", "")
    args = list(cfg.get("args", []) or [])

    # opencode passes argv as an array
    if isinstance(command, list):
        argv = [str(c) for c in command if str(c).strip()]
        command, args = (argv[0], argv[1:]) if argv else ("", [])

    if url and kind in ("remote", "http", ""):
        transport = "http"
    else:
        transport = "stdio"

    server: Dict[str, Any] = {
        "name": name,
        "transport": transport,
        "enabled": bool(cfg.get("enabled", True)),
        "timeout": _normalize_timeout(cfg.get("timeout", 30)),
    }
    if transport == "http":
        server["url"] = url
        headers = cfg.get("headers") or {}
        if headers:
            server["headers"] = {str(k): str(v) for k, v in headers.items()}
    else:
        server["command"] = str(command)
        if args:
            server["args"] = args
    env = _normalize_env(cfg.get("env") or cfg.get("environment"))
    if env:
        server["env"] = env
    return server


# ── Merge into JEBAT config ─────────────────────────────────────────────────


def _existing_names(config_path: Path) -> Tuple[Dict[str, Any], List[str]]:
    if not config_path.exists():
        return {}, []
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    mcp = data.get(MANIFEST_KEY, {}) or {}
    servers = mcp.get("servers", []) or []
    names = []
    for s in servers:
        if isinstance(s, dict) and s.get("name"):
            names.append(str(s["name"]))
    return data, names


def merge_servers(
    servers: List[Dict[str, Any]],
    config_path: Path,
    overwrite: bool = False,
    backup: bool = True,
) -> Dict[str, List[str]]:
    """Merge converted servers into the config's mcp.servers list."""
    data, existing = _existing_names(config_path)
    added, skipped, replaced = [], [], []

    mcp = data.setdefault(MANIFEST_KEY, {})
    if not isinstance(mcp, dict):
        raise ValueError(f"'{MANIFEST_KEY}' key in {config_path} is not a mapping")
    current = mcp.setdefault("servers", [])
    if not isinstance(current, list):
        raise ValueError(f"'{MANIFEST_KEY}.servers' in {config_path} is not a list")

    by_name = {str(s.get("name")): s for s in current if isinstance(s, dict)}

    for srv in servers:
        name = srv["name"]
        if name in by_name and not overwrite:
            skipped.append(name)
            continue
        if name in by_name:
            current[:] = [s for s in current if not (isinstance(s, dict) and s.get("name") == name)]
            replaced.append(name)
        current.append(srv)
        added.append(name)

    if added or replaced:
        if backup and config_path.exists():
            stamp = time.strftime("%Y%m%d-%H%M%S")
            shutil.copy2(config_path, config_path.with_name(f"{config_path.name}.bak-{stamp}-import"))
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return {"added": added, "skipped": skipped, "replaced": replaced}


# ── CLI entry ───────────────────────────────────────────────────────────────


def run_config_command(tokens: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="jebat config",
        description="Import configuration from other CLI tools (omp, opencode, claude).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    imp = sub.add_parser("import", help="Import MCP server config from another CLI")
    imp.add_argument("--source", "-s", choices=["omp", "opencode", "claude"], help="which CLI to import from")
    imp.add_argument("--path", "-p", help="explicit path to a source config file (overrides --source)")
    imp.add_argument("--config", help="target jebat config.yaml (default ~/.jebat/config.yaml)")
    imp.add_argument("--dry-run", action="store_true", help="show converted servers without writing")
    imp.add_argument("--overwrite", action="store_true", help="replace servers whose names already exist")
    imp.add_argument("--only", help="comma-separated server names to import (default: all)")

    ns = parser.parse_args(list(tokens))

    try:
        kind, src_path, raw_servers = _load_source(ns.source, ns.path)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        cprint(f"✗ {exc}", C.RED)
        return 1

    if ns.only:
        wanted = {n.strip() for n in ns.only.split(",") if n.strip()}
        raw_servers = {k: v for k, v in raw_servers.items() if k in wanted}
        missing = wanted - set(raw_servers)
        if missing:
            cprint(f"  ⚠ not found in source: {', '.join(sorted(missing))}", C.YELLOW)

    converted = [_convert(name, cfg) for name, cfg in raw_servers.items()]

    cprint(f"\n┌─ import from {kind} ({src_path})", C.CYAN)
    if not converted:
        print("│  no MCP servers defined in source")
        print("└─ nothing to do")
        return 0

    for srv in converted:
        flag = "✓" if srv["enabled"] else "·"
        where = srv.get("url") or f"{srv.get('command', '')} {' '.join(srv.get('args', []))}".strip()
        cprint(f"│  {flag} {srv['name']:<22} {srv['transport']:<6} {where[:58]}", C.GREEN if srv["enabled"] else C.GRAY)

    target = Path(ns.config).expanduser() if ns.config else JEBAT_CONFIG_PATH

    if ns.dry_run:
        print("│")
        print("│  dry-run — YAML that would be merged:")
        print("│  " + yaml.safe_dump({"mcp": {"servers": converted}}, sort_keys=False).replace("\n", "\n│  ").rstrip("│ \n"))
        print("└─ no changes written")
        return 0

    try:
        result = merge_servers(converted, target, overwrite=ns.overwrite)
    except (ValueError, OSError, yaml.YAMLError) as exc:
        cprint(f"✗ merge failed: {exc}", C.RED)
        return 1

    print("│")
    if result["added"]:
        cprint(f"│  added    : {', '.join(result['added'])}", C.GREEN)
    if result["replaced"]:
        cprint(f"│  replaced : {', '.join(result['replaced'])}", C.YELLOW)
    if result["skipped"]:
        cprint(f"│  skipped  : {', '.join(result['skipped'])} (exist — use --overwrite)", C.GRAY)
    if result["added"] or result["replaced"]:
        print(f"│  target   : {target}")
    print("└─ done — restart jebat to pick up new servers")
    return 0
