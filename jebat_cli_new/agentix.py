"""`jebat agentix` subcommand — create, build, and deploy Agentix solutions.

Consolidates three agent-construction styles into one scaffold+deploy pipeline:

- **hermes**   — ReAct reasoning-loop agent (perceive → reason → act → reflect),
                 modeled on the Hermes/Atomic execution loop already in JEBAT.
- **openclaw** — project-style solution: task folder + shared workspace files
                 the agent reads/writes across steps (scaffold-driven, no code).
- **atomic**   — schema-driven typed tools: every capability is a small typed
                 function with a JSON schema; the agent only orchestrates calls.

A solution is a directory with an `agentix.yaml` manifest:

    name: my-solution
    version: 0.1.0
    template: hermes            # hermes | openclaw | atomic
    entrypoint: agent.py        # module with run(task: str, ctx) -> str
    tools: []                   # tool module names under tools/ (atomic lists schemas)
    deploy:
      allow: [local, mcp, vps]  # permitted deploy targets (staged approval)

Deployment targets:
- local — copy + register in ~/.jebat/agentix/registry.json
- mcp   — print ready-to-paste MCP server config exposing the solution
- vps   — ship to the JEBAT mainframe via scp (requires SSH access)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import yaml

from jebat_cli_new.theme import C, cprint


REGISTRY_PATH = Path.home() / ".jebat" / "agentix" / "registry.json"
MANIFEST_NAME = "agentix.yaml"

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

_HERMES_AGENT = '''"""{name} — Hermes-style ReAct agent.

Loop: perceive -> reason -> act -> reflect. The model reasons in steps and
chooses tools explicitly; every action is checked against the solution's
tool allowlist before execution.
"""

from __future__ import annotations

from typing import Any, Dict

MAX_STEPS = 8


def run(task: str, ctx: Dict[str, Any]) -> str:
    """Execute `task` with a bounded ReAct loop. `ctx.tools` maps tool name -> callable."""
    trace: List[str] = []
    tools: Dict[str, Any] = ctx.get("tools", {{}})
    for step in range(MAX_STEPS):
        # THINK: replace with your model call; the loop shape stays the same.
        thought = f"step {{step}}: need data for: {{task[:60]}}"
        trace.append(thought)
        # ACT: pick exactly one tool (or finish). No tool loops without progress.
        if not tools:
            break
        name, fn = next(iter(tools.items()))
        result = fn(task)
        trace.append(f"act: {{name}} -> {{str(result)[:120]}}")
        # REFLECT: decide if the goal is met; stop when it is.
        if result:
            return "\\n".join(trace)
    return "\\n".join(trace + ["max steps reached"])
'''

_OPENCLAW_README = '''# {name}

OpenClaw-style solution: the workspace IS the program.

- `workspace/` holds task files the agent reads and edits across steps.
- `plan.md` is the living checklist — the agent updates it as it works.
- No orchestration code required; the harness drives the folder.

Add task files to `workspace/`, then run: `jebat agentix build {name}`
'''

_PLAN_MD = '''# Plan — {name}

- [ ] Understand the task
- [ ] Draft output in workspace/
- [ ] Verify against plan.md
- [ ] Mark steps done as you go
'''

_ATOMIC_TOOL = '''"""{tool} — typed tool with JSON schema (Atomic style).

Schema-first: the manifest advertises this tool; the agent can only call
what the schema describes. Keep functions pure and boring.
"""

from __future__ import annotations

SCHEMA = {{
    "name": "{tool}",
    "description": "Describe what {tool} does for the agent here.",
    "parameters": {{
        "type": "object",
        "properties": {{
            "task": {{"type": "string", "description": "The task or input text"}},
        }},
        "required": ["task"],
    }},
}}


def run(task: str, **kwargs) -> str:
    # Replace with the real capability. Return strings only.
    return f"{tool} handled: {{task[:80]}}"
'''

_ATOMIC_AGENT = '''"""{name} — Atomic-style orchestrator over schema-driven tools."""

from __future__ import annotations

from typing import Any, Dict


def run(task: str, ctx: Dict[str, Any]) -> str:
    """Dispatch to tools declared in the manifest; no hidden capabilities."""
    tools: Dict[str, Any] = ctx.get("tools", {{}})
    if not tools:
        return "no tools registered — check agentix.yaml"
    # Minimal orchestrator: call each tool once, in manifest order.
    parts = [f"{{fn(task)}}" for fn in tools.values()]
    return "\\n".join(parts)
'''


def _manifest(name: str, template: str) -> Dict[str, Any]:
    return {
        "name": name,
        "version": "0.1.0",
        "template": template,
        "entrypoint": "agent.py",
        "tools": [] if template != "atomic" else ["tools/example.py"],
        "deploy": {"allow": ["local", "mcp", "vps"]},
    }


def _scaffold(name: str, template: str, target: Path) -> Path:
    sol = target / name
    if sol.exists():
        raise FileExistsError(f"solution already exists: {sol}")
    (sol).mkdir(parents=True)
    (sol / MANIFEST_NAME).write_text(
        yaml.safe_dump(_manifest(name, template), sort_keys=False), encoding="utf-8"
    )
    if template == "hermes":
        (sol / "agent.py").write_text(_HERMES_AGENT.format(name=name), encoding="utf-8")
    elif template == "openclaw":
        (sol / "workspace").mkdir()
        (sol / "plan.md").write_text(_PLAN_MD.format(name=name), encoding="utf-8")
        (sol / "agent.py").write_text(
            "# openclaw solutions are folder-driven; see workspace/ and plan.md\n",
            encoding="utf-8",
        )
        (sol / "README.md").write_text(_OPENCLAW_README.format(name=name), encoding="utf-8")
    elif template == "atomic":
        tools = sol / "tools"
        tools.mkdir()
        (tools / "__init__.py").write_text("", encoding="utf-8")
        (tools / "example.py").write_text(_ATOMIC_TOOL.format(tool="example"), encoding="utf-8")
        (sol / "agent.py").write_text(_ATOMIC_AGENT.format(name=name), encoding="utf-8")
    else:
        shutil.rmtree(sol, ignore_errors=True)
        raise ValueError(f"unknown template: {template} (use hermes|openclaw|atomic)")
    return sol


# ---------------------------------------------------------------------------
# Validate / build
# ---------------------------------------------------------------------------


def _load_manifest(sol: Path) -> Dict[str, Any]:
    mf = sol / MANIFEST_NAME
    if not mf.exists():
        raise FileNotFoundError(f"missing {MANIFEST_NAME} in {sol}")
    data = yaml.safe_load(mf.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "name" not in data or "template" not in data:
        raise ValueError(f"invalid manifest: {mf}")
    return data


def _validate(sol: Path) -> List[str]:
    errors: List[str] = []
    try:
        mf = _load_manifest(sol)
    except Exception as exc:  # noqa: BLE001 — report, don't crash the CLI
        return [str(exc)]
    entry = sol / str(mf.get("entrypoint", "agent.py"))
    if not entry.exists():
        errors.append(f"entrypoint not found: {entry}")
    elif entry.suffix == ".py":
        import py_compile

        try:
            py_compile.compile(str(entry), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"entrypoint does not compile: {exc}")
    for tool in mf.get("tools", []) or []:
        tp = sol / tool
        if not tp.exists():
            errors.append(f"declared tool missing: {tool}")
    allowed = (mf.get("deploy", {}) or {}).get("allow", [])
    if not allowed:
        errors.append("deploy.allow is empty — no deploy target permitted")
    return errors


def _build(sol: Path) -> Dict[str, Any]:
    errors = _validate(sol)
    if errors:
        raise SystemExit("build failed:\n  " + "\n  ".join(errors))
    mf = _load_manifest(sol)
    manifest_bytes = (sol / MANIFEST_NAME).read_bytes()
    info = {
        "name": mf["name"],
        "version": mf.get("version", "0.0.0"),
        "template": mf["template"],
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest()[:16],
        "tools": mf.get("tools", []),
    }
    build_dir = sol / ".agentix"
    build_dir.mkdir(exist_ok=True)
    (build_dir / "build.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    return info


# ---------------------------------------------------------------------------
# Deploy
# ---------------------------------------------------------------------------


def _deploy_local(sol: Path) -> str:
    info = _build(sol)
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    registry: Dict[str, Any] = {}
    if REGISTRY_PATH.exists():
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    registry[info["name"]] = {**info, "path": str(sol.resolve())}
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    return f"registered locally → {REGISTRY_PATH} ({info['manifest_sha256']})"


def _deploy_mcp(sol: Path) -> str:
    info = _build(sol)
    cfg = {
        "mcpServers": {
            f"agentix-{info['name']}": {
                "command": "python",
                "args": [str((Path(__file__).resolve().parents[1] / "jebat-mcp"))],
                "env": {"JEBAT_AGENTIX_SOLUTION": str(sol.resolve())},
            }
        }
    }
    return json.dumps(cfg, indent=2)


def _deploy_vps(sol: Path, host: str) -> str:
    info = _build(sol)
    remote = f"/var/www/jebat-core/agentix/{info['name']}"
    cmd = ["scp", "-r", str(sol.resolve()), f"root@{host}:{remote}"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except FileNotFoundError:
        raise SystemExit("scp not found — install OpenSSH client for vps deploys")
    if proc.returncode != 0:
        raise SystemExit(f"vps deploy failed: {proc.stderr.strip() or proc.stdout.strip()}")
    return f"shipped to {host}:{remote} ({info['manifest_sha256']})"


def _deploy(sol: Path, target: str, host: str) -> str:
    mf = _load_manifest(sol)
    allowed = (mf.get("deploy", {}) or {}).get("allow", ["local"])
    if target not in allowed:
        raise SystemExit(f"target '{target}' not in deploy.allow {allowed} — edit {MANIFEST_NAME} first")
    if target == "local":
        return _deploy_local(sol)
    if target == "mcp":
        return _deploy_mcp(sol)
    if target == "vps":
        return _deploy_vps(sol, host)
    raise SystemExit(f"unknown target: {target}")


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------


def _status(sol: Optional[Path]) -> str:
    lines: List[str] = []
    if sol:
        try:
            mf = _load_manifest(sol)
            errors = _validate(sol)
            lines.append(f"[{mf['name']}] template={mf['template']} v{mf.get('version', '?')}")
            build = sol / ".agentix" / "build.json"
            if build.exists():
                info = json.loads(build.read_text(encoding="utf-8"))
                lines.append(f"  built: {info['built_at']} sha:{info['manifest_sha256']}")
            else:
                lines.append("  built: never (run `jebat agentix build`)")
            lines += [f"  ERROR: {e}" for e in errors] or ["  state: valid"]
        except Exception as exc:  # noqa: BLE001
            lines.append(f"  ERROR: {exc}")
    if REGISTRY_PATH.exists():
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        lines.append(f"registry: {len(registry)} deployed")
        for name, entry in registry.items():
            lines.append(f"  • {name} v{entry.get('version')} → {entry.get('path')}")
    else:
        lines.append("registry: empty")
    return "\n".join(lines)


def _resolve_solution(path_or_name: str) -> Path:
    """Accept a solution directory OR a registry name."""
    p = Path(path_or_name)
    if (p / MANIFEST_NAME).exists():
        return p.resolve()
    if REGISTRY_PATH.exists():
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        entry = registry.get(path_or_name)
        if entry and Path(entry["path"]).exists():
            return Path(entry["path"]).resolve()
    raise SystemExit(f"solution not found (dir or registry name): {path_or_name}")


def _load_tools(sol: Path, manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Import declared tool modules; map name -> run callable."""
    import importlib.util

    tools: Dict[str, Any] = {}
    for rel in manifest.get("tools", []) or []:
        tool_path = sol / rel
        if not tool_path.exists():
            raise SystemExit(f"declared tool missing: {rel}")
        mod_name = f"agentix_tool_{tool_path.stem}"
        spec = importlib.util.spec_from_file_location(mod_name, tool_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        if not hasattr(module, "run"):
            raise SystemExit(f"tool {rel} has no run() function")
        tools[tool_path.stem] = module.run
    return tools


def _run_solution(sol: Path, task: str) -> str:
    mf = _load_manifest(sol)
    errors = _validate(sol)
    if errors:
        raise SystemExit("run aborted — build errors:\n  " + "\n  ".join(errors))
    tools = _load_tools(sol, mf)
    entry = sol / str(mf.get("entrypoint", "agent.py"))
    import importlib.util

    spec = importlib.util.spec_from_file_location("agentix_entry", entry)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    if not hasattr(module, "run"):
        raise SystemExit(f"entrypoint {entry.name} has no run(task, ctx) function")
    return str(module.run(task, {"tools": tools, "manifest": mf, "root": str(sol)}))


# ---------------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------------


def run_agentix_command(tokens: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="jebat agentix",
        description="Create, build, and deploy Agentix solutions (hermes | openclaw | atomic).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="Scaffold a new solution")
    create.add_argument("name")
    create.add_argument("--template", "-t", default="hermes", choices=["hermes", "openclaw", "atomic"])
    create.add_argument("--dir", default=".", help="target directory (default: cwd)")

    build = sub.add_parser("build", help="Validate + build (writes .agentix/build.json)")
    build.add_argument("path")

    deploy = sub.add_parser("deploy", help="Deploy a built solution")
    deploy.add_argument("path")
    deploy.add_argument("--target", choices=["local", "mcp", "vps"], default="local")
    deploy.add_argument("--host", default="72.62.255.206", help="VPS host for --target vps")

    status = sub.add_parser("status", help="Show solution/registry status")
    status.add_argument("path", nargs="?", help="optional solution directory")

    run = sub.add_parser("run", help="Execute a built solution: run PATH_OR_NAME \"task text\"")
    run.add_argument("solution", help="solution directory or registry name")
    run.add_argument("task", help="task text passed to the solution entrypoint")

    ns = parser.parse_args(list(tokens))
    try:
        if ns.command == "create":
            sol = _scaffold(ns.name, ns.template, Path(ns.dir).resolve())
            cprint(f"✓ created {ns.template} solution: {sol}", C.GREEN)
            print(f"  next: jebat agentix build {sol}")
            return 0
        if ns.command == "build":
            info = _build(Path(ns.path).resolve())
            cprint(f"✓ built {info['name']} v{info['version']} sha:{info['manifest_sha256']}", C.GREEN)
            return 0
        if ns.command == "deploy":
            out = _deploy(Path(ns.path).resolve(), ns.target, ns.host)
            print(out)
            return 0
        if ns.command == "status":
            sol = Path(ns.path).resolve() if getattr(ns, "path", None) else None
            print(_status(sol))
            return 0
        if ns.command == "run":
            sol = _resolve_solution(ns.solution)
            out = _run_solution(sol, ns.task)
            print(out)
            return 0
    except SystemExit as exc:
        # argparse uses SystemExit(2) for usage errors — let those propagate.
        if isinstance(exc.code, int):
            raise
        print(exc, file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"agentix: {exc}", file=sys.stderr)
        return 1
    parser.print_help(sys.stderr)
    return 2
