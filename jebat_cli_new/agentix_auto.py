"""Agentix solution foundry — turn an objective into a governed solution.

`jebat agentix auto "<objective>"` asks the configured provider to draft a
reflex/llm solution spec — name, trigger-style description, doctrine, tool
allowlist, iteration budget, jail choice — writes it in the same shape as the
specialist catalog, then validates it through the shared build gate. The
result is indistinguishable from a hand-written solution: run it, eval it,
deploy it (local | mcp), or put it in a team.

Deterministic surfaces (spec normalization, name rules, JSON extraction) are
plain functions so tests never need a model. The only model call is
`draft_spec`; the HTTP/MCP side can inject a ready `draft` to skip it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from jebat_cli_new.agentix import _build, _deploy_local, _deploy_mcp

ALLOWED_TOOLS = ("read_file", "search_files", "terminal", "write_file", "list_dir")
DEFAULT_TOOLS = ("read_file", "search_files", "terminal", "write_file", "list_dir")
NAME_RE = re.compile(r"^[a-z][a-z0-9-]{2,31}$")
MIN_DOCTRINE_LEN = 120
MAX_DESCRIPTION_LEN = 500
DRAFT_MAX_TOKENS = 4096

_SYSTEM = (
    "You are JEBAT's solution architect. You design one small, governed agent "
    "solution per request. Solutions follow the house doctrine style: a "
    "Mission line, a numbered Method, and an Output contract. Ground every "
    "claim in tool output and state what was not checked."
)

_INSTRUCTIONS = """\
Design ONE agent solution for this objective:

OBJECTIVE: {objective}

Reply with ONLY a JSON object (no prose, no code fences) using exactly these keys:
- "name": kebab-case id, 3-32 chars, must start with a letter (e.g. "log-triage").
- "description": one or two sentences for routing/discovery; end with a "Use for ..." trigger clause. No double quotes inside.
- "doctrine": markdown for agent.md. Start with "# <Name> doctrine", then a "Mission:" line, a numbered "Method:" the agent can execute with the tools it gets, and an "Output:" contract (what artifact is written where). Keep it 120-1200 characters; no double quotes needed.
- "tools": array drawn ONLY from ["read_file","search_files","terminal","write_file","list_dir"].
- "max_iterations": integer 6-20 (default 12).
- "jailed": true only if the solution should be confined to its own workspace/ directory; false when it must work on the host repo or target.
"""


class AgentixAutoError(Exception):
    """Raised when drafting, normalizing, or writing an auto solution fails."""


# ---------------------------------------------------------------------------
# Deterministic helpers (no model, no disk)
# ---------------------------------------------------------------------------


def _extract_json(text: str) -> Dict[str, Any]:
    """Pull the first JSON object out of a model reply (code fences tolerated)."""
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        raise AgentixAutoError("model reply contained no JSON object")
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise AgentixAutoError(f"model reply was not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise AgentixAutoError("model reply JSON was not an object")
    return data


def slugify(text: str) -> str:
    """kebab-case a display string into a solution-name candidate."""
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)[:32].strip("-")
    if not slug:
        return "auto-solution"
    if not slug[0].isalpha():
        slug = ("auto-" + slug)[:32].strip("-")
    return slug


def normalize_spec(
    raw: Dict[str, Any],
    objective: str,
    name_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate + normalize a drafted spec into the catalog shape."""
    name = re.sub(r"\s+", "-", str(name_override or raw.get("name") or "").strip().lower())
    if not NAME_RE.match(name):
        name = slugify(name or objective)
    if not NAME_RE.match(name):
        raise AgentixAutoError(f"could not derive a valid solution name (got {name!r})")

    description = " ".join(str(raw.get("description") or "").split())
    if len(description) < 20:
        description = f"Auto-drafted solution. Use for: {objective}".strip()
    description = description[:MAX_DESCRIPTION_LEN]

    doctrine = str(raw.get("doctrine") or "").strip()
    if len(doctrine) < MIN_DOCTRINE_LEN:
        raise AgentixAutoError(
            "drafted doctrine is too short — refusing to write a hollow solution"
        )

    tools: List[str] = []
    for tool in raw.get("tools") or []:
        if isinstance(tool, str) and tool in ALLOWED_TOOLS and tool not in tools:
            tools.append(tool)
    if not tools:
        tools = list(DEFAULT_TOOLS)

    try:
        iterations = int(raw.get("max_iterations") or 12)
    except (TypeError, ValueError):
        iterations = 12
    iterations = min(20, max(6, iterations))

    return {
        "name": name,
        "description": description,
        "doctrine": doctrine,
        "tools": tools,
        "max_iterations": iterations,
        "jailed": bool(raw.get("jailed", False)),
    }


def build_manifest(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Manifest dict in the same shape as the specialist catalog."""
    return {
        "name": spec["name"],
        "version": "1.0.0",
        "description": spec["description"],
        "template": "reflex",
        "runtime": "llm",
        "provider": None,
        "model": None,
        "max_iterations": spec["max_iterations"],
        "llm_tools": list(spec["tools"]),
        "llm_workspace": "workspace" if spec["jailed"] else None,
        "budget": {"tokens": 150000, "wall_clock": "30m"},
        "deploy": {"allow": ["local", "mcp"]},
    }


def write_solution(spec: Dict[str, Any], target_dir: Path) -> Path:
    """Materialize a normalized spec as a solution directory."""
    sol = Path(target_dir) / spec["name"]
    if sol.exists():
        raise AgentixAutoError(f"solution already exists: {sol} — pick another --name or --dir")
    sol.mkdir(parents=True)
    (sol / "agentix.yaml").write_text(
        yaml.safe_dump(build_manifest(spec), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
        newline="\n",
    )
    (sol / "agent.md").write_text(spec["doctrine"] + "\n", encoding="utf-8", newline="\n")
    if spec["jailed"]:
        (sol / "workspace").mkdir()
        (sol / "workspace" / ".gitkeep").write_text("", encoding="utf-8", newline="\n")
    return sol


# ---------------------------------------------------------------------------
# Model call
# ---------------------------------------------------------------------------


def _default_provider_id(registry) -> Optional[str]:
    """Mirror the CLI's active-provider resolution: flagged active, else first."""
    for cid, cfg in registry.configs.items():
        if getattr(cfg, "active", False):
            return cid
    for cid in registry.configs:
        return cid
    return None


def draft_spec(
    objective: str,
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """One provider call: objective -> drafted spec dict (raw, unnormalized)."""
    from jebat_cli_new.models import CompletionRequest
    from jebat_cli_new.providers import ProviderRegistry

    objective = " ".join(str(objective or "").split())
    if not objective:
        raise AgentixAutoError("objective is empty")

    registry = ProviderRegistry()
    provider_id = provider or _default_provider_id(registry)
    if not provider_id:
        raise AgentixAutoError(
            "no provider configured — add one with `jebat provider add` or pass --provider"
        )
    impl = registry.get(provider_id)
    if impl is None:
        known = ", ".join(sorted(registry.ids())) or "(none)"
        raise AgentixAutoError(f"provider {provider_id!r} is not configured — known: {known}")
    model_id = model or getattr(registry.configs.get(provider_id), "model", None) or ""

    prompt = _SYSTEM + "\n\n" + _INSTRUCTIONS.replace("{objective}", objective)
    try:
        response = impl.complete(
            CompletionRequest(
                provider=provider_id,
                model=model_id or "",
                prompt=prompt,
                temperature=0.3,
                max_tokens=DRAFT_MAX_TOKENS,
            )
        )
    except Exception as exc:  # noqa: BLE001 — surface provider failure as our error class
        raise AgentixAutoError(f"provider call failed ({provider_id}): {exc}") from exc

    text = getattr(response, "text", "") or ""
    if not text.strip():
        raise AgentixAutoError("provider returned an empty reply")
    return _extract_json(text)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def auto_create(
    objective: str,
    *,
    name: Optional[str] = None,
    target_dir: Path | str = ".",
    deploy: str = "none",
    provider: Optional[str] = None,
    model: Optional[str] = None,
    draft: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Draft -> normalize -> write -> build (-> deploy) in one call.

    `draft` injects a ready spec (tests, HTTP callers holding their own model);
    otherwise one provider call produces it. Raises AgentixAutoError on any
    failure of the deterministic path; a build failure keeps the solution on
    disk for inspection and reports its path.
    """
    raw = draft if draft is not None else draft_spec(objective, provider=provider, model=model)
    deploy = (deploy or "none").strip().lower()
    if deploy not in ("none", "local", "mcp", ""):
        raise AgentixAutoError(f"unknown deploy target {deploy!r} (none|local|mcp)")
    spec = normalize_spec(raw, objective, name_override=name)
    sol = write_solution(spec, Path(target_dir))
    try:
        info = _build(sol)
    except SystemExit as exc:
        raise AgentixAutoError(
            f"drafted solution failed validation (kept for inspection at {sol}): {exc}"
        ) from exc

    outcome: Dict[str, Any] = {"spec": spec, "path": str(sol), "build": info, "deploy": None}
    if deploy == "local":
        outcome["deploy"] = _deploy_local(sol)
    elif deploy == "mcp":
        outcome["deploy"] = _deploy_mcp(sol)
    return outcome
