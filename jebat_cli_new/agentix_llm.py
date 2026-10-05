"""Agentix LLM runtime — spawn a real agent for a doctrine-driven solution.

`runtime: llm` solutions have no Python entrypoint to execute; instead the
shared jebat_cli_new AgentLoop is spawned with the solution's constraints
applied:

- tool allowlist  → `llm_tools` names; denied calls never reach the filesystem
- workspace jail  → `llm_workspace` jails file tools to that subdirectory
- doctrine        → `agent.md` is appended to the system prompt
- budget          → `budget.tokens` / `budget.wall_clock` stop the loop
- run registry    → every run persists to ~/.jebat/agentix/runs/<id>/
                    (brief, manifest snapshot, events, result, messages);
                    `--resume <id>` continues a run with its conversation

Code-runtime solutions (entrypoint agent.py) never touch this module.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from jebat_cli_new.agentix import _load_manifest

_JAIL_DENIED = "[AGENTIX_JAIL_DENIED]"
PROVIDER_ERROR_PREFIX = "[JEBAT provider error:"
_PATH_TOOLS = ("read_file", "write_file", "search_files", "list_dir")
DEFAULT_LLM_TOOLS = ("read_file", "write_file", "search_files", "terminal", "list_dir")

# Minimum tokens a single ReAct iteration can plausibly cost (system prompt
# + history + tool observations). Used for spawn-time budget sanity.
_MIN_TOKENS_PER_ITERATION = 64


class AgentixLLMError(Exception):
    """Raised for invalid LLM-runtime solutions or denied operations."""


def runs_dir() -> Path:
    """Run-registry root. Override with JEBAT_AGENTIX_RUNS (tests)."""
    override = os.environ.get("JEBAT_AGENTIX_RUNS")
    if override:
        return Path(override)
    return Path.home() / ".jebat" / "agentix" / "runs"


def read_doctrine(sol: Path) -> str:
    path = sol / "agent.md"
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").strip()


def _inside(root: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def make_jailed_executor(manifest: Dict, sol: Path, workspace_override: Optional[Path] = None):
    """Wrap execute_tool with the allowlist + optional workspace jail.

    workspace_override: team runs redirect a jailed solution's file tools to
    the shared team workspace (only applies when the manifest sets
    llm_workspace — repo-touching agents keep host access).
    Returns a callable(name, args, yolo) -> str matching
    jebat_cli_new.tools.execute_tool's signature.
    """
    from jebat_cli_new.tools import execute_tool as base_execute

    allowed = set(manifest.get("llm_tools") or DEFAULT_LLM_TOOLS)
    workspace: Optional[Path] = None
    ws_rel = manifest.get("llm_workspace")
    if ws_rel:
        workspace = (workspace_override if workspace_override else (sol / str(ws_rel))).resolve()
        workspace.mkdir(parents=True, exist_ok=True)

    def jailed(name: str, args: Dict, yolo: bool = False) -> str:
        if name not in allowed:
            return (
                f"{_JAIL_DENIED} tool {name!r} is not in this solution's allowlist "
                f"({', '.join(sorted(allowed))}). Use one of the allowed tools."
            )
        args = dict(args or {})
        if workspace is not None:
            if name == "terminal":
                requested = args.get("workdir")
                if requested and not _inside(workspace, Path(requested)):
                    return (
                        f"{_JAIL_DENIED} workdir {requested!r} is outside the workspace "
                        f"({workspace}). Terminal commands run inside the workspace."
                    )
                args["workdir"] = str(workspace)
            elif name in _PATH_TOOLS:
                raw = str(args.get("path", "."))
                candidate = Path(raw)
                if candidate.is_absolute():
                    jailed_path = candidate if _inside(workspace, candidate) else None
                else:
                    jailed_path = (workspace / candidate).resolve()
                    if not _inside(workspace, jailed_path):
                        jailed_path = None
                if jailed_path is None:
                    return (
                        f"{_JAIL_DENIED} path {raw!r} escapes the workspace "
                        f"({workspace}). Use workspace-relative paths."
                    )
                args["path"] = str(jailed_path)
        return base_execute(name, args, yolo=yolo)

    return jailed


def parse_wall_clock(value) -> Optional[float]:
    """'30s' | '10m' | '1h' | int-seconds -> seconds. None if absent/invalid."""
    import re

    if value is None:
        return None
    if isinstance(value, (int, float)) and value > 0:
        return float(value)
    match = re.fullmatch(r"(\d+)\s*(s|m|h)?", str(value).strip().lower())
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2) or "s"
    return float(amount * {"s": 1, "m": 60, "h": 3600}[unit])


def _check_budget_sanity(budget_tokens: Optional[int], max_iterations: int) -> Optional[str]:
    """Spawn-time budget validation. Returns an error message, or None.

    Refuses budgets too tight to afford even minimal iterations; the
    documented failure class this prevents is a spawn that silently burns
    its budget mid-task instead of failing fast.
    """
    if budget_tokens is None:
        return None
    floor = max_iterations * _MIN_TOKENS_PER_ITERATION
    if budget_tokens < floor:
        return (
            f"budget.tokens={budget_tokens} is below the minimum {floor} "
            f"({max_iterations} iterations x {_MIN_TOKENS_PER_ITERATION} tokens) — refuse to spawn"
        )
    if budget_tokens < max_iterations * 512:
        print(
            f"  [agentix] warning: budget.tokens={budget_tokens} is tight for "
            f"{max_iterations} iterations — expect early stop + summary",
            file=sys.stderr,
        )
    return None


def _record_run(
    sol: Path,
    manifest: Dict,
    task: str,
    provider: str,
    model: str,
    step,
    messages,
    resumed_from: Optional[str],
    record_dir: Optional[Path] = None,
) -> str:
    """Persist a run to the run registry (or a team leg dir). Returns the run id."""
    run_id = f"{time.strftime('%Y%m%d-%H%M%S')}-{manifest['name']}-{uuid.uuid4().hex[:4]}"
    run_path = (record_dir if record_dir else runs_dir()) / run_id
    run_path.mkdir(parents=True, exist_ok=True)

    brief = {
        "run_id": run_id,
        "solution": manifest["name"],
        "path": str(sol),
        "task": task,
        "provider": provider,
        "model": model,
        "template": manifest.get("template"),
        "runtime": manifest.get("runtime", "code"),
        "max_iterations": manifest.get("max_iterations"),
        "budget": manifest.get("budget"),
        "resumed_from": resumed_from,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (run_path / "brief.json").write_text(json.dumps(brief, indent=2), encoding="utf-8")
    shutil.copy2(sol / "agentix.yaml", run_path / "manifest.yaml")

    events = []
    for i, action in enumerate(step.tool_actions, 1):
        events.append(json.dumps({"event": "tool", "i": i, "call": action}))
    events.append(json.dumps({
        "event": "final",
        "tokens": step.response.tokens_used,
        "provider": step.response.provider,
        "model": step.response.model,
    }))
    (run_path / "events.jsonl").write_text("\n".join(events) + "\n", encoding="utf-8")

    (run_path / "result.json").write_text(
        json.dumps(
            {
                "answer": step.response.text or "",
                "tool_calls": step.tool_actions,
                "tokens": step.response.tokens_used,
                "provider": step.response.provider,
                "model": step.response.model,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (run_path / "messages.json").write_text(
        json.dumps(
            [{"role": m.role, "content": m.content, "tool_calls": m.tool_calls} for m in messages],
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return run_id


def run_with_agent_loop(
    sol: Path,
    task: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    yolo: bool = False,
    verbose: bool = False,
    max_iterations: Optional[int] = None,
    registry=None,
    resume_from: Optional[str] = None,
    workspace_override: Optional[Path] = None,
    record_dir: Optional[Path] = None,
) -> Tuple[str, Dict]:
    """Spawn the shared AgentLoop for a doctrine solution and run `task`.

    resume_from: run id — loads that run's conversation, then continues it
    with `task`. The new (accumulated) conversation is persisted under a
    fresh run id with resumed_from set.
    workspace_override: team shared workspace for jailed solutions.
    record_dir: team leg directory (default: the global run registry).

    Returns (final_answer, info) where info carries provider/model/tool-call
    count and the run id for the CLI footer.
    """
    import time

    from jebat_cli_new import agent as agent_module
    from jebat_cli_new.agent import AgentLoop, AgentMessage
    from jebat_cli_new.providers import ProviderRegistry

    manifest = _load_manifest(sol)  # origin's loader returns the dict directly
    if registry is None:
        registry = ProviderRegistry()

    # Resolution order: CLI flag → manifest → AgentLoop's own defaults.
    provider_name = provider or manifest.get("provider") or "ollama"
    model_name = model or manifest.get("model") or "qwen2.5-coder:7b"

    budget = manifest.get("budget") if isinstance(manifest.get("budget"), dict) else {}
    budget_tokens = budget.get("tokens")
    deadline_ts = None
    wall = parse_wall_clock(budget.get("wall_clock"))
    if wall is not None:
        deadline_ts = time.time() + wall

    effective_iterations = max_iterations or int(manifest.get("max_iterations") or 12)
    budget_error = _check_budget_sanity(
        int(budget_tokens) if budget_tokens else None, effective_iterations
    )
    if budget_error:
        raise AgentixLLMError(budget_error)

    resumed_messages: List[AgentMessage] = []
    if resume_from:
        prior = runs_dir() / resume_from / "messages.json"
        if not prior.is_file():
            raise AgentixLLMError(f"unknown run id {resume_from!r} (no messages.json in {runs_dir() / resume_from})")
        for raw in json.loads(prior.read_text(encoding="utf-8")):
            resumed_messages.append(AgentMessage(role=raw["role"], content=raw["content"], tool_calls=raw.get("tool_calls")))

    loop = AgentLoop(
        registry=registry,
        default_provider=provider_name,
        model=model_name,
        yolo=yolo,
        style="openmanus" if manifest.get("template") == "reflex" else "jebat",
        verbose=verbose,
        budget_tokens=int(budget_tokens) if budget_tokens else None,
        deadline=deadline_ts,
    )
    loop.max_iterations = effective_iterations
    if resumed_messages:
        loop.messages = resumed_messages
    doctrine = read_doctrine(sol)
    if doctrine:
        loop.system_prompt_extra = (
            f"# Solution doctrine ({manifest['name']}, template: {manifest['template']})\n{doctrine}"
        )

    jailed = make_jailed_executor(manifest, sol, workspace_override=workspace_override)
    original = agent_module.execute_tool
    agent_module.execute_tool = jailed
    try:
        step = loop.step(task, provider=provider_name, model=model_name)
    finally:
        agent_module.execute_tool = original

    run_id = _record_run(
        sol, manifest, task, provider_name, model_name, step,
        messages=loop.messages, resumed_from=resume_from, record_dir=record_dir,
    )
    info = {
        "provider": step.response.provider,
        "model": step.response.model,
        "tool_calls": len(step.tool_actions),
        "tokens": step.response.tokens_used,
        "run_id": run_id,
        "resumed_from": resume_from,
    }
    return step.response.text or "", info
