"""`jebat agentix` subcommand — create, build, and deploy Agentix solutions.

Consolidates three agent-construction styles into one scaffold+deploy pipeline:

- **reflex**   — ReAct reasoning-loop agent (perceive → reason → act → reflect),
                 modeled on the Hermes/Atomic execution loop already in JEBAT.
- **flow**     — project-style solution: task folder + shared workspace files
                 the agent reads/writes across steps (scaffold-driven, no code).
- **lattice**  — schema-driven typed tools: every capability is a small typed
                 function with a JSON schema; the agent only orchestrates calls.

A solution is a directory with an `agentix.yaml` manifest:

    name: my-solution
    version: 0.1.0
    template: reflex            # reflex | flow | lattice
    entrypoint: agent.py        # module with run(task: str, ctx) -> str
    tools: []                   # tool module names under tools/ (lattice lists schemas)
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
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import yaml

from jebat_cli_new.theme import C, cprint


REGISTRY_PATH = Path.home() / ".jebat" / "agentix" / "registry.json"
MANIFEST_NAME = "agentix.yaml"

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

_HERMES_AGENT = '''"""{name} — Reflex archetype: bounded ReAct agent.

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

_ATOMIC_AGENT = '''"""{name} — Lattice archetype: orchestrator over schema-driven tools."""

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
    descriptions = {
        "reflex": "Deliberate ReAct agent — spawn by typing an objective; reasons, acts with tools, verifies.",
        "flow": "Workspace-driven solution — the agent reads and edits workspace/ files across steps.",
        "lattice": "Schema-driven typed tools — the agent only orchestrates declared capabilities.",
    }
    base = {
        "name": name,
        "version": "0.1.0",
        "description": descriptions[template],
        "template": template,
        "entrypoint": "agent.py",
        "tools": [] if template != "lattice" else ["tools/example.py"],
        "deploy": {"allow": ["local", "mcp", "vps"]},
    }
    if template == "reflex":
        # reflex ships doctrine-driven: `jebat agentix run NAME "task"` spawns
        # a real LLM agent with no code to write. Delete agent.md (or set
        # runtime: code) to fall back to executing agent.py.
        base["runtime"] = "llm"
        base["max_iterations"] = 12
        base["llm_tools"] = ["read_file", "write_file", "search_files", "terminal", "list_dir"]
    return base


_REFLEX_DOCTRINE = """\
# Reflex doctrine — deliberate ReAct

1. THINK in <thought> before every action. State what you know, what is
   missing, and the single next action.
2. ACT with exactly one tool batch per turn — no speculative calls.
3. OBSERVE before re-planning. Never assume a tool succeeded; read the
   <tool_response>.
4. VERIFY at least one artifact per claimed outcome (read the file you
   wrote, re-run the check you claim passes).
5. REPORT with FINAL_ANSWER: facts, artifacts touched, and what remains.

You do not fabricate command output, file contents, or verification results.
"""


def _scaffold(name: str, template: str, target: Path) -> Path:
    sol = target / name
    if sol.exists():
        raise FileExistsError(f"solution already exists: {sol}")
    (sol).mkdir(parents=True)
    (sol / MANIFEST_NAME).write_text(
        yaml.safe_dump(_manifest(name, template), sort_keys=False), encoding="utf-8"
    )
    if template == "reflex":
        (sol / "agent.py").write_text(_HERMES_AGENT.format(name=name), encoding="utf-8")
        (sol / "agent.md").write_text(_REFLEX_DOCTRINE, encoding="utf-8")
        (sol / "workspace").mkdir()
    elif template == "flow":
        (sol / "workspace").mkdir()
        (sol / "plan.md").write_text(_PLAN_MD.format(name=name), encoding="utf-8")
        (sol / "agent.py").write_text(
            "# flow solutions are folder-driven; see workspace/ and plan.md\n",
            encoding="utf-8",
        )
        (sol / "README.md").write_text(_OPENCLAW_README.format(name=name), encoding="utf-8")
    elif template == "lattice":
        tools = sol / "tools"
        tools.mkdir()
        (tools / "__init__.py").write_text("", encoding="utf-8")
        (tools / "example.py").write_text(_ATOMIC_TOOL.format(tool="example"), encoding="utf-8")
        (sol / "agent.py").write_text(_ATOMIC_AGENT.format(name=name), encoding="utf-8")
        golden = sol / "golden"
        golden.mkdir()
        (golden / "hello.json").write_text(
            json.dumps(
                {
                    "task": "hello world",
                    "checks": [{"type": "contains", "value": "example"}],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    else:
        shutil.rmtree(sol, ignore_errors=True)
        raise ValueError(f"unknown template: {template} (use reflex|flow|lattice)")
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
    if mf.get("runtime", "code") == "llm":
        pass  # llm runtime executes doctrine via the AgentLoop — no entrypoint to check
    elif not entry.exists():
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
        elif tp.suffix == ".py":
            import py_compile

            try:
                py_compile.compile(str(tp), doraise=True)
            except py_compile.PyCompileError as exc:
                errors.append(f"tool does not compile: {exc}")
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
                "command": sys.executable or "python",
                "args": ["-m", "jebat_cli_new.agentix_mcp_server", "--solution", info["name"]],
                "transport": "stdio",
                "timeout": 300,
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
            path = Path(entry.get("path", ""))
            runtime, stale = "?", ""
            try:
                mf = _load_manifest(path)
                runtime = mf.get("runtime", "code")
                build = path / ".agentix" / "build.json"
                if build.is_file():
                    stored = json.loads(build.read_text(encoding="utf-8"))
                    current = hashlib.sha256((path / MANIFEST_NAME).read_bytes()).hexdigest()[:16]
                    if stored.get("manifest_sha256") != current:
                        stale = "  [STALE — rebuild]"
                else:
                    stale = "  [never built]"
            except Exception:  # noqa: BLE001 — show the path even when unreadable
                stale = "  [manifest unreadable — run doctor]"
            lines.append(f"  • {name} v{entry.get('version')} ({runtime}) → {entry.get('path')}{stale}")
    else:
        lines.append("registry: empty")
    return "\n".join(lines)


def _route(objective: str) -> tuple[Path, Dict[str, Any], List[tuple[float, str]]]:
    """Type-only routing: match the objective against deployed solutions.

    Scores name, description, and template words of every registry entry;
    returns (best_path, best_manifest, ranked) where ranked is the top-3
    [(score, name)] for ambiguity display. Raises SystemExit on no match.
    """
    import re as _re

    if not REGISTRY_PATH.exists():
        raise SystemExit("registry is empty — deploy a solution first: jebat agentix deploy PATH --target local")
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    words = set(_re.findall(r"[a-z0-9]+", objective.lower()))
    scored: List[tuple[float, str, Path, Dict[str, Any]]] = []
    for name, entry in registry.items():
        path = Path(entry.get("path", ""))
        if not (path / MANIFEST_NAME).exists():
            continue
        try:
            mf = _load_manifest(path)
        except Exception:  # noqa: BLE001 — skip unreadable entries
            continue
        haystack = set(_re.findall(r"[a-z0-9]+", f"{name} {mf.get('description','')} {mf.get('template','')}".lower()))
        score = len(words & haystack) / (len(words) or 1)
        if score > 0:
            scored.append((score, name, path, mf))
    if not scored:
        raise SystemExit(f"no deployed solution matches {objective!r} — run `jebat agentix status` to list them")
    scored.sort(key=lambda item: item[0], reverse=True)
    ranked = [(round(score, 2), name) for score, name, _p, _mf in scored[:3]]
    return scored[0][2], scored[0][3], ranked


SPECIALISTS_DIR = Path(__file__).resolve().parent / "agentix_specialists"

# Mirrors jebat_cli_new.agentix_llm.PROVIDER_ERROR_PREFIX (kept local: the
# llm module imports from this file, so importing back at module scope
# would be circular).
PROVIDER_ERROR_PREFIX = "[JEBAT provider error:"


def _team_command(ns) -> int:
    from jebat_cli_new.agentix_team import TeamError, load_team, run_team

    objective = " ".join(ns.objective) if isinstance(ns.objective, list) else str(ns.objective)
    if objective == "-":
        objective = sys.stdin.read().strip()
    if not objective:
        print("agentix team: empty objective", file=sys.stderr)
        return 1

    team_path = Path(ns.team)
    if not team_path.is_file():
        user = Path.home() / ".jebat" / "agentix" / "teams" / f"{ns.team}.yaml"
        shipped = SPECIALISTS_DIR.parent / "agentix_teams" / f"{ns.team}.yaml"
        team_path = user if user.is_file() else shipped
    try:
        team = load_team(team_path)
        code, report, _run_id = run_team(
            team, objective,
            yolo=ns.yolo or ns.auto,  # --auto implies unattended legs
            provider=ns.provider, model=ns.model,
            resume_team_id=ns.resume_team, approve=ns.approve or ns.auto,
        )
    except TeamError as exc:
        print(f"agentix team: {exc}", file=sys.stderr)
        return 1
    print(report)
    return code


def _oneshot(ns) -> int:
    """Ephemeral agent: scaffold into a temp dir, run, discard.

    Transcripts persist in the run registry even though the solution dir
    is removed — the run id in the footer is the durable artifact.
    """
    import shutil as _shutil
    import tempfile as _tempfile

    task = " ".join(ns.task) if isinstance(ns.task, list) else str(ns.task)
    if task == "-":
        task = sys.stdin.read().strip()
    if not task:
        print("agentix oneshot: empty task", file=sys.stderr)
        return 1
    with _tempfile.TemporaryDirectory(prefix="agentix-oneshot-") as tmp:
        sol = _scaffold(f"oneshot-{uuid.uuid4().hex[:4]}", "reflex", Path(tmp))
        mf = _load_manifest(sol)
        if ns.tools:
            mf["llm_tools"] = [t.strip() for t in ns.tools.split(",") if t.strip()]
        if ns.model:
            mf["model"] = ns.model
        if ns.provider:
            mf["provider"] = ns.provider
        if ns.iterations:
            mf["max_iterations"] = ns.iterations
        (sol / "agentix.yaml").write_text(yaml.safe_dump(mf, sort_keys=False), encoding="utf-8")
        if ns.doctrine:
            doctrine_src = Path(ns.doctrine).expanduser()
            if not doctrine_src.is_file():
                print(f"agentix oneshot: doctrine not found: {doctrine_src}", file=sys.stderr)
                return 1
            _shutil.copy2(doctrine_src, sol / "agent.md")
        try:
            result, info = _run_solution(
                sol, task, yolo=ns.yolo, provider=ns.provider,
                model=ns.model, verbose=ns.verbose,
            )
        except SystemExit as exc:
            if isinstance(exc.code, int):
                raise
            print(exc, file=sys.stderr)
            return 1
    print(result or "(no answer)")
    if info:
        print(
            f"  [ephemeral · {info.get('provider','?')}:{info.get('model','?')}"
            f" · {info.get('tokens',0)} tokens · run {info.get('run_id','?')}]"
        )
    if result and result.startswith(PROVIDER_ERROR_PREFIX):
        print("agentix: provider call failed — see error above", file=sys.stderr)
        return 1
    return 0


def _list_runs(resume_hint: Optional[str]) -> str:
    """List recent runs (newest first) from the run registry."""
    from jebat_cli_new.agentix_llm import runs_dir

    base = runs_dir()
    if not base.is_dir():
        return "no runs yet — every agentix llm run is recorded automatically"
    entries = sorted((p for p in base.iterdir() if p.is_dir()), reverse=True)[:20]
    if not entries:
        return "no runs yet"
    lines = ["Recent runs (newest first):"]
    for run_path in entries:
        brief_path = run_path / "brief.json"
        if not brief_path.is_file():
            continue
        try:
            brief = json.loads(brief_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        marker = "  <-" if resume_hint and run_path.name == resume_hint else ""
        task_short = (brief.get("task") or "")[:60]
        lines.append(
            f"  {run_path.name}  {brief.get('solution','?'):18s}"
            f" {brief.get('ts','?')}  {task_short}{marker}"
        )
    return "\n".join(lines)


def _scaffold_from_specialist(spec: str, name: str, target: Path) -> Path:
    """Copy a specialist template into a new solution, renamed to `name`."""
    src = SPECIALISTS_DIR / spec
    if not (src / MANIFEST_NAME).is_file():
        known = sorted(p.name for p in SPECIALISTS_DIR.iterdir() if (p / MANIFEST_NAME).is_file()) if SPECIALISTS_DIR.is_dir() else []
        raise SystemExit(
            f"unknown specialist {spec!r}"
            + (f" — available: {', '.join(known)}" if known else " (catalog missing)")
        )
    sol = target / name
    if sol.exists():
        raise FileExistsError(f"solution already exists: {sol}")
    shutil.copytree(src, sol)
    mf = _load_manifest(sol)
    mf["name"] = name
    (sol / MANIFEST_NAME).write_text(yaml.safe_dump(mf, sort_keys=False), encoding="utf-8")
    return sol


def _list_specialists() -> str:
    if not SPECIALISTS_DIR.is_dir():
        return "specialist catalog missing"
    lines = ["Specialist templates (jebat agentix create NAME --from SPEC):"]
    for path in sorted(SPECIALISTS_DIR.iterdir()):
        if not (path / MANIFEST_NAME).is_file():
            continue
        try:
            mf = _load_manifest(path)
            desc = str(mf.get("description", "")).split(". ")[0]
            lines.append(f"  {mf['name']:22s} {desc[:90]}")
        except Exception:  # noqa: BLE001 — skip unreadable entries
            continue
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


def _run_solution(sol: Path, task: str, *, yolo: bool = False, provider: Optional[str] = None,
                  model: Optional[str] = None, verbose: bool = False,
                  max_iterations: Optional[int] = None, registry=None,
                  resume_from: Optional[str] = None):
    """Execute a solution. Returns (result_text, info).

    Runtime dispatch: `runtime: llm` spawns the shared AgentLoop with the
    solution's doctrine/allowlist/jail (agentix_llm); the default code
    runtime imports and executes the entrypoint's run(task, ctx).
    """
    mf = _load_manifest(sol)
    errors = _validate(sol)
    if errors:
        raise SystemExit("run aborted — build errors:\n  " + "\n  ".join(errors))
    if resume_from and mf.get("runtime", "code") != "llm":
        raise SystemExit("--resume requires a runtime: llm solution (code entrypoints are stateless)")
    if mf.get("runtime", "code") == "llm":
        from jebat_cli_new.agentix_llm import run_with_agent_loop

        return run_with_agent_loop(
            sol, task, provider=provider, model=model, yolo=yolo,
            verbose=verbose, max_iterations=max_iterations, registry=registry,
            resume_from=resume_from,
        )
    tools = _load_tools(sol, mf)
    entry = sol / str(mf.get("entrypoint", "agent.py"))
    import importlib.util

    spec = importlib.util.spec_from_file_location("agentix_entry", entry)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    if not hasattr(module, "run"):
        raise SystemExit(f"entrypoint {entry.name} has no run(task, ctx) function")
    return str(module.run(task, {"tools": tools, "manifest": mf, "root": str(sol)})), {}


# ---------------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------------


def run_agentix_command(tokens: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="jebat agentix",
        description="Create, build, and deploy Agentix solutions (reflex | flow | lattice).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="Scaffold a new solution (from an archetype or a specialist)")
    create.add_argument("name")
    create.add_argument("--template", "-t", default="reflex", choices=["reflex", "flow", "lattice"],
                        help="archetype (ignored when --from is used)")
    create.add_argument("--from", dest="from_spec", default=None,
                        help="scaffold from a specialist template (see: jebat agentix templates)")
    create.add_argument("--dir", default=".", help="target directory (default: cwd)")

    auto = sub.add_parser("auto", help="Draft a NEW solution from an objective (LLM), build it, optionally deploy")
    auto.add_argument("objective", nargs="+", help="What the solution should do ('-' reads stdin)")
    auto.add_argument("--name", default=None, help="Override the drafted solution name (kebab-case)")
    auto.add_argument("--dir", default=".", help="target directory (default: cwd)")
    auto.add_argument("--deploy", choices=["none", "local", "mcp"], default="none",
                      help="deploy after build ('mcp' prints the paste-ready client config)")
    auto.add_argument("--provider", default=None, help="Override provider for the drafting call")
    auto.add_argument("--model", default=None, help="Override model for the drafting call")

    fmc = sub.add_parser("from-mcp", help="Draft a solution from a configured MCP server (introspect + LLM), build it")
    fmc.add_argument("server", nargs="?", help="MCP server name from ~/.jebat/config.yaml ('--list' shows them)")
    fmc.add_argument("--list", dest="list_servers", action="store_true",
                     help="List configured MCP servers and exit")
    fmc.add_argument("--name", default=None, help="Override the drafted solution name (kebab-case)")
    fmc.add_argument("--dir", default=".", help="target directory (default: cwd)")
    fmc.add_argument("--deploy", choices=["none", "local", "mcp"], default="none",
                     help="deploy after build ('mcp' prints the paste-ready client config)")
    fmc.add_argument("--provider", default=None, help="Override provider for the drafting call")
    fmc.add_argument("--model", default=None, help="Override model for the drafting call")

    build = sub.add_parser("build", help="Validate + build (writes .agentix/build.json)")
    build.add_argument("path")

    deploy = sub.add_parser("deploy", help="Deploy a built solution")
    deploy.add_argument("path")
    deploy.add_argument("--target", choices=["local", "mcp", "vps"], default="local")
    deploy.add_argument("--host", default="72.62.255.206", help="VPS host for --target vps")

    status = sub.add_parser("status", help="Show solution/registry status")
    status.add_argument("path", nargs="?", help="optional solution directory")

    evalp = sub.add_parser("eval", help="Structural checks + golden tasks for a solution")
    evalp.add_argument("path")
    evalp.add_argument("--live", action="store_true",
                       help="execute llm-runtime golden tasks against the real provider")

    export = sub.add_parser("export", help="Export a solution to another harness format")
    export.add_argument("path")
    export.add_argument("--format", dest="fmt", choices=["claude-subagent", "skill"], default="claude-subagent")
    export.add_argument("--out", default=None, help="output directory (default: ./agentix-export)")

    sub.add_parser("templates", help="List the specialist template catalog")

    run = sub.add_parser("run", help="Execute a built solution: run PATH_OR_NAME \"task text\" (task '-' reads stdin)")
    run.add_argument("solution", help="solution directory or registry name")
    run.add_argument("task", help="task text ('-' reads the task from stdin)")
    run.add_argument("--provider", default=None, help="Override provider (llm runtime)")
    run.add_argument("--model", default=None, help="Override model (llm runtime)")
    run.add_argument("--iterations", type=int, default=None, help="Override max_iterations (llm runtime)")
    run.add_argument("--yolo", action="store_true", help="Skip safety confirmations")
    run.add_argument("--verbose", action="store_true", help="Show thought + tool cards")
    run.add_argument("--resume", default=None, metavar="RUN_ID",
                     help="continue a recorded run's conversation (llm runtime; list ids: jebat agentix runs)")

    ask = sub.add_parser("ask", help="Type only an objective — routes to the best deployed solution")
    ask.add_argument("objective", nargs="+", help="Objective text; matched against solution names + descriptions")
    ask.add_argument("--provider", default=None, help="Override provider (llm runtime)")
    ask.add_argument("--model", default=None, help="Override model (llm runtime)")
    ask.add_argument("--yolo", action="store_true", help="Skip safety confirmations")

    doctor = sub.add_parser("doctor", help="Health-check registry, builds, budgets, doctrine drift")
    doctor.add_argument("--fix", action="store_true", help="Prune dangling registry entries")

    oneshot = sub.add_parser("oneshot", help="Ephemeral agent — no solution folder, transcript kept in the run registry")
    oneshot.add_argument("task", nargs="+", help="Task text ('-' reads stdin)")
    oneshot.add_argument("--tools", default=None, help="Comma-separated llm_tools allowlist (default: reflex set)")
    oneshot.add_argument("--doctrine", default=None, help="Path to an agent.md to use as doctrine")
    oneshot.add_argument("--provider", default=None)
    oneshot.add_argument("--model", default=None)
    oneshot.add_argument("--iterations", type=int, default=None)
    oneshot.add_argument("--yolo", action="store_true")
    oneshot.add_argument("--verbose", action="store_true")

    sub.add_parser("runs", help="List recent runs (ids usable with run --resume)")

    team = sub.add_parser("team", help="Run a declared specialist pipeline")
    team_sub = team.add_subparsers(dest="team_command", required=True)
    team_run = team_sub.add_parser("run", help="Run (or resume) a team pipeline")
    team_run.add_argument("team", help="Team name, or path to a team .yaml")
    team_run.add_argument("objective", nargs="+", help="Objective for the team ('-' reads stdin)")
    team_run.add_argument("--provider", default=None)
    team_run.add_argument("--model", default=None)
    team_run.add_argument("--yolo", action="store_true", help="Skip safety confirmations on every leg")
    team_run.add_argument("--auto", action="store_true", help="Skip human gates (explicit)")
    team_run.add_argument("--resume-team", dest="resume_team", default=None, metavar="TEAM_RUN_ID",
                          help="Resume a gate-paused team run (list: runs dir / jebat agentix runs)")
    team_run.add_argument("--approve", action="store_true", help="Approve the pending gate on resume")

    sub.add_parser("teams", help="List shipped + user team pipelines")

    ns = parser.parse_args(list(tokens))
    try:
        if ns.command == "create":
            if ns.from_spec:
                sol = _scaffold_from_specialist(ns.from_spec, ns.name, Path(ns.dir).resolve())
                mf = _load_manifest(sol)
                cprint(f"✓ created {mf['template']} solution from specialist {ns.from_spec!r}: {sol}", C.GREEN)
                print(f"  next: jebat agentix build {sol} && jebat agentix eval {sol}")
                return 0
            sol = _scaffold(ns.name, ns.template, Path(ns.dir).resolve())
            cprint(f"✓ created {ns.template} solution: {sol}", C.GREEN)
            print(f"  next: jebat agentix build {sol}")
            return 0
        if ns.command == "auto":
            from jebat_cli_new.agentix_auto import AgentixAutoError, auto_create

            words = list(ns.objective)
            objective = sys.stdin.read().strip() if words == ["-"] else " ".join(words)
            if not objective:
                print("agentix auto: empty objective", file=sys.stderr)
                return 1
            try:
                outcome = auto_create(
                    objective,
                    name=ns.name,
                    target_dir=Path(ns.dir).resolve(),
                    deploy=ns.deploy,
                    provider=ns.provider,
                    model=ns.model,
                )
            except AgentixAutoError as exc:
                print(f"agentix auto: {exc}", file=sys.stderr)
                return 1
            spec, info = outcome["spec"], outcome["build"]
            cprint(
                f"✓ drafted {spec['name']}"
                + (f" [jailed]" if spec["jailed"] else "")
                + f" — {spec['max_iterations']} iters, tools: {', '.join(spec['tools'])}",
                C.GREEN,
            )
            print(f"  solution: {outcome['path']}")
            print(f"  built: sha:{info['manifest_sha256']}")
            if outcome.get("deploy"):
                print(outcome["deploy"])
            print(f'  next: jebat agentix eval "{outcome["path"]}"  |  run "{outcome["path"]}" "<task>"')
            return 0
        if ns.command == "from-mcp":
            from jebat_cli_new import mcp_bridge

            if ns.list_servers or not ns.server:
                servers = mcp_bridge.list_servers()
                if not servers:
                    print("no MCP servers configured (~/.jebat/config.yaml `mcp:` section)", file=sys.stderr)
                    return 1
                for srv in servers:
                    state = "on " if srv["enabled"] else "off"
                    target = srv.get("url") or srv.get("command") or "?"
                    print(f"  {state} {srv['name']:24s} {srv['transport']:8s} {str(target)[:80]}")
                print('  create one: jebat agentix from-mcp <server> [--name N] [--deploy local|mcp]')
                return 0

            from jebat_cli_new.agentix_auto import AgentixAutoError
            from jebat_cli_new.agentix_mcp import from_mcp

            try:
                outcome = from_mcp(
                    ns.server,
                    name=ns.name,
                    target_dir=Path(ns.dir).resolve(),
                    deploy=ns.deploy,
                    provider=ns.provider,
                    model=ns.model,
                )
            except AgentixAutoError as exc:
                print(f"agentix from-mcp: {exc}", file=sys.stderr)
                return 1
            spec, info = outcome["spec"], outcome["build"]
            cprint(
                f"✓ drafted {spec['name']} from MCP server {outcome['mcp']['server']!r} "
                f"({outcome['mcp']['tool_count']} tools)",
                C.GREEN,
            )
            print(f"  solution: {outcome['path']}")
            print(f"  built: sha:{info['manifest_sha256']}")
            if outcome.get("deploy"):
                print(outcome["deploy"])
            print(f'  next: jebat agentix eval "{outcome["path"]}"  |  run "{outcome["path"]}" "<task>"')
            return 0
        if ns.command == "templates":
            print(_list_specialists())
            return 0
        if ns.command == "eval":
            from jebat_cli_new.agentix_ops import evaluate_solution

            lines, failures = evaluate_solution(Path(ns.path).resolve(), live=ns.live)
            print("\n".join(lines))
            return 1 if failures else 0
        if ns.command == "export":
            from jebat_cli_new.agentix_ops import export_solution

            out = export_solution(
                Path(ns.path).resolve(), ns.fmt,
                Path(ns.out).expanduser() if ns.out else None,
            )
            cprint(f"✓ exported {ns.fmt} → {out}", C.GREEN)
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
            task = sys.stdin.read().strip() if ns.task == "-" else ns.task
            if not task:
                print("agentix: empty task (stdin was read because task was '-')", file=sys.stderr)
                return 1
            sol = _resolve_solution(ns.solution)
            result, info = _run_solution(
                sol, task, yolo=ns.yolo, provider=ns.provider,
                model=ns.model, verbose=ns.verbose, max_iterations=ns.iterations,
                resume_from=ns.resume,
            )
            print(result or "(no answer)")
            if info:
                print(
                    f"  [{info.get('provider','?')}:{info.get('model','?')}"
                    f" · {info.get('tool_calls',0)} tool calls · {info.get('tokens',0)} tokens"
                    + (f" · run {info['run_id']}" if info.get("run_id") else "")
                    + (f" · resumed from {info['resumed_from']}" if info.get("resumed_from") else "")
                    + "]"
                )
            if result and result.startswith(PROVIDER_ERROR_PREFIX):
                print("agentix: provider call failed — see error above", file=sys.stderr)
                return 1
            return 0
        if ns.command == "ask":
            objective = " ".join(ns.objective) if isinstance(ns.objective, list) else str(ns.objective)
            sol, mf, ranked = _route(objective)
            print(f"  routed to: {mf['name']} ({mf['template']})")
            if len(ranked) > 1:
                others = "  ".join(f"{name}({score})" for score, name in ranked[1:])
                print(f"  also matched: {others}")
            result, info = _run_solution(
                sol, objective, yolo=ns.yolo, provider=ns.provider, model=ns.model,
            )
            print(result or "(no answer)")
            if info and info.get("run_id"):
                print(f"  [run {info['run_id']} · {info.get('tokens',0)} tokens]")
            if result and result.startswith(PROVIDER_ERROR_PREFIX):
                print("agentix: provider call failed — see error above", file=sys.stderr)
                return 1
            return 0
        if ns.command == "team":
            return _team_command(ns)
        if ns.command == "teams":
            from jebat_cli_new.agentix_team import list_teams

            print(list_teams())
            return 0
        if ns.command == "doctor":
            from jebat_cli_new.agentix_ops import doctor

            lines, failures = doctor(fix=ns.fix)
            print("\n".join(lines))
            return 1 if failures else 0
        if ns.command == "oneshot":
            return _oneshot(ns)
        if ns.command == "runs":
            print(_list_runs(getattr(ns, "resume_target", None)))
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
