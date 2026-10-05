"""Agentix LLM runtime — spawn a real agent for a doctrine-driven solution.

`runtime: llm` solutions have no Python entrypoint to execute; instead the
shared jebat_cli_new AgentLoop is spawned with the solution's constraints
applied:

- tool allowlist  → `llm_tools` names; denied calls never reach the filesystem
- workspace jail  → `llm_workspace` jails file tools to that subdirectory
- doctrine        → `agent.md` is appended to the system prompt

Code-runtime solutions (entrypoint agent.py) never touch this module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple

from jebat_cli_new.agentix import _load_manifest

_JAIL_DENIED = "[AGENTIX_JAIL_DENIED]"
_PATH_TOOLS = ("read_file", "write_file", "search_files", "list_dir")
DEFAULT_LLM_TOOLS = ("read_file", "write_file", "search_files", "terminal", "list_dir")


class AgentixLLMError(Exception):
    """Raised for invalid LLM-runtime solutions or denied operations."""


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


def make_jailed_executor(manifest: Dict, sol: Path):
    """Wrap execute_tool with the allowlist + optional workspace jail.

    Returns a callable(name, args, yolo) -> str matching
    jebat_cli_new.tools.execute_tool's signature.
    """
    from jebat_cli_new.tools import execute_tool as base_execute

    allowed = set(manifest.get("llm_tools") or DEFAULT_LLM_TOOLS)
    workspace: Optional[Path] = None
    ws_rel = manifest.get("llm_workspace")
    if ws_rel:
        workspace = (sol / str(ws_rel)).resolve()
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


def run_with_agent_loop(
    sol: Path,
    task: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    yolo: bool = False,
    verbose: bool = False,
    max_iterations: Optional[int] = None,
    registry=None,
) -> Tuple[str, Dict]:
    """Spawn the shared AgentLoop for a doctrine solution and run `task`.

    Returns (final_answer, info) where info carries provider/model/tool-call
    count for the CLI footer.
    """
    from jebat_cli_new import agent as agent_module
    from jebat_cli_new.agent import AgentLoop
    from jebat_cli_new.providers import ProviderRegistry

    manifest = _load_manifest(sol)  # origin's loader returns the dict directly
    if registry is None:
        registry = ProviderRegistry()

    # Resolution order: CLI flag → manifest → AgentLoop's own defaults.
    provider_name = provider or manifest.get("provider") or "ollama"
    model_name = model or manifest.get("model") or "qwen2.5-coder:7b"

    loop = AgentLoop(
        registry=registry,
        default_provider=provider_name,
        model=model_name,
        yolo=yolo,
        style="openmanus" if manifest.get("template") == "reflex" else "jebat",
        verbose=verbose,
    )
    loop.max_iterations = max_iterations or int(manifest.get("max_iterations") or 12)
    doctrine = read_doctrine(sol)
    if doctrine:
        loop.system_prompt_extra = (
            f"# Solution doctrine ({manifest['name']}, template: {manifest['template']})\n{doctrine}"
        )

    jailed = make_jailed_executor(manifest, sol)
    original = agent_module.execute_tool
    agent_module.execute_tool = jailed
    try:
        step = loop.step(task, provider=provider_name, model=model_name)
    finally:
        agent_module.execute_tool = original
    info = {
        "provider": step.response.provider,
        "model": step.response.model,
        "tool_calls": len(step.tool_actions),
        "tokens": step.response.tokens_used,
    }
    return step.response.text or "", info
