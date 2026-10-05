"""Agentix teams — declared pipelines of specialist agents.

A team is a YAML manifest: an ordered pipeline of llm-runtime members, a
default-deny `spawns:` roster, an optional human gate, and a team-level
budget. Legs run in sequence with file-based handoff through a shared
jailed workspace; the qa-verifier checks each leg against its doctrine's
declared output artifact before handing to the next.

    team: go-to-market
    pipeline: [marketing-strategist, copy-writer, seo-auditor, ads-manager]
    spawns:  [marketing-strategist, copy-writer, seo-auditor, ads-manager]
    budget:  {tokens: 900000, wall_clock: 2h}
    gates:   [{after: ads-manager, type: human}]

    jebat agentix team run go-to-market "launch plan for the beta"
    jebat agentix teams                     # list shipped + user teams
"""

from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from jebat_cli_new.agentix import MANIFEST_NAME, SPECIALISTS_DIR, _load_manifest
from jebat_cli_new.agentix_llm import (
    PROVIDER_ERROR_PREFIX,
    parse_wall_clock,
    runs_dir,
)

TEAM_EXIT_GATE = 2  # distinct exit code: paused for human approval


class TeamError(Exception):
    """Raised for invalid team manifests or unresolvable members."""


# ── Manifest ────────────────────────────────────────────────────────

def load_team(source: Path) -> Dict[str, Any]:
    """Load + validate a team YAML. Raises TeamError with reasons."""
    try:
        raw = yaml.safe_load(source.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError) as exc:
        raise TeamError(f"team manifest unreadable: {exc}")
    if not isinstance(raw, dict):
        raise TeamError("team manifest must be a YAML mapping")

    name = str(raw.get("team") or "").strip()
    pipeline = raw.get("pipeline") or []
    spawns = raw.get("spawns") or []
    errors: List[str] = []
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", name):
        errors.append("team name must match [a-zA-Z0-9_-]")
    if not pipeline or not all(isinstance(m, str) and m for m in pipeline):
        errors.append("pipeline must be a non-empty list of member names")
    if len(pipeline) != len(set(pipeline)):
        errors.append("pipeline contains duplicate members")
    if not spawns:
        errors.append("spawns is required and default-deny — list every member the team may run")
    missing_roster = [m for m in pipeline if m not in spawns]
    if missing_roster:
        errors.append(f"pipeline members not in spawns (default-deny): {', '.join(missing_roster)}")
    gates = raw.get("gates") or []
    for gate in gates:
        if not isinstance(gate, dict) or gate.get("type") != "human":
            errors.append(f"gate {gate!r}: only type 'human' gates are supported")
        elif gate.get("after") not in pipeline:
            errors.append(f"gate after {gate.get('after')!r} is not a pipeline member")
    budget = raw.get("budget") if isinstance(raw.get("budget"), dict) else {}
    if budget.get("tokens") is not None:
        try:
            if int(budget["tokens"]) <= 0:
                errors.append("budget.tokens must be positive")
        except (TypeError, ValueError):
            errors.append("budget.tokens must be an integer")
    if budget.get("wall_clock") is not None and parse_wall_clock(budget.get("wall_clock")) is None:
        errors.append("budget.wall_clock unparseable (use 30m / 2h)")
    if errors:
        raise TeamError("invalid team manifest:\n  " + "\n  ".join(errors))

    raw["_source"] = str(source)
    raw["_budget"] = budget
    return raw


def resolve_member(name: str) -> Path:
    """Resolve a team member: registry first, then the shipped catalog."""
    from jebat_cli_new import agentix as _agentix

    registry_path = _agentix.REGISTRY_PATH
    if registry_path.is_file():
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            registry = {}
        entry = registry.get(name)
        if entry and (Path(entry["path"]) / MANIFEST_NAME).is_file():
            return Path(entry["path"]).resolve()
    catalog = SPECIALISTS_DIR / name
    if (catalog / MANIFEST_NAME).is_file():
        return catalog.resolve()
    raise TeamError(
        f"member {name!r} not found (registry or specialist catalog) — "
        "create it: jebat agentix create NAME --from " + name
    )


def list_teams() -> str:
    """List shipped + user team manifests."""
    shipped = SPECIALISTS_DIR.parent / "agentix_teams"
    user = Path.home() / ".jebat" / "agentix" / "teams"
    lines = ["Teams (jebat agentix team run NAME \"objective\"):"]
    seen = set()
    for base, label in ((user, "user"), (shipped, "shipped")):
        if not base.is_dir():
            continue
        for path in sorted(base.glob("*.yaml")):
            try:
                mf = load_team(path)
            except TeamError as exc:
                lines.append(f"  {path.stem:18s} INVALID: {str(exc).splitlines()[0]}")
                continue
            if mf["team"] in seen:
                continue
            seen.add(mf["team"])
            gates = ",".join(g.get("after", "?") for g in (mf.get("gates") or []))
            gate_note = f"  [gate after {gates}]" if gates else ""
            lines.append(f"  {mf['team']:18s} {' -> '.join(mf['pipeline'])}{gate_note}")
    if len(lines) == 1:
        lines.append("  (none found)")
    return "\n".join(lines)


# ── qa-verifier (between legs) ──────────────────────────────────────

_ARTIFACT_RE = re.compile(r"write\s+([A-Za-z0-9_./-]+\.(?:md|json|txt|csv))", re.IGNORECASE)


def verify_leg(sol: Path, answer: str, workspaces: List[Path]) -> Tuple[bool, List[str]]:
    """qa-verifier: a leg may hand off only if its contract holds.

    Checks: non-empty answer, no provider error, and every output artifact
    the doctrine declares ("write X.md") exists in the team workspace (or
    the solution dir for host-repo agents).
    """
    reasons: List[str] = []
    if not answer or not answer.strip():
        reasons.append("empty answer")
    if answer.startswith(PROVIDER_ERROR_PREFIX):
        reasons.append(f"provider error: {answer[:120]}")
    doctrine_path = sol / "agent.md"
    if doctrine_path.is_file():
        doctrine = doctrine_path.read_text(encoding="utf-8", errors="replace")
        declared = [m.group(1) for m in _ARTIFACT_RE.finditer(doctrine)]
        search_dirs = [w for w in workspaces if w is not None] + [sol, Path.cwd()]
        for artifact in declared:
            found = any(
                (base / Path(artifact).name).is_file()
                or (base / artifact).is_file()
                for base in search_dirs
                if base is not None
            )
            if not found:
                reasons.append(f"declared artifact missing: {artifact} (searched {[str(s) for s in search_dirs]})")
    return (not reasons), reasons


# ── Runner ──────────────────────────────────────────────────────────

def _leg_brief(team: Dict, objective: str, index: int, prev: Optional[Dict], workspace: Path) -> str:
    member = team["pipeline"][index]
    parts = [
        f"[TEAM {team['team']}] You are leg {index + 1}/{len(team['pipeline'])}: {member}.",
        f"OBJECTIVE: {objective}",
    ]
    if prev:
        answer = (prev.get("answer") or "")[:1800]
        parts.append(f"PREVIOUS LEG ({prev['agent']}) summary:\n{answer}")
    existing = sorted(p.name for p in workspace.glob("*") if p.is_file() and p.name != ".gitkeep") if workspace.is_dir() else []
    parts.append(
        f"TEAM WORKSPACE: {workspace} — earlier artifacts: {', '.join(existing) if existing else '(none yet)'}. "
        "Read what you need from it and write your declared output artifact there."
    )
    parts.append("Do your part only — later legs handle the rest.")
    return "\n\n".join(parts)


def run_team(
    team: Dict,
    objective: str,
    *,
    yolo: bool = False,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    registry=None,
    resume_team_id: Optional[str] = None,
    approve: bool = False,
) -> Tuple[int, str, Optional[str]]:
    """Run (or resume) a team pipeline. Returns (exit_code, report, team_run_id).

    Exit codes: 0 done, 1 failed/verify-blocked, 2 paused at a human gate.
    """
    from jebat_cli_new.agentix_llm import run_with_agent_loop

    pipeline: List[str] = team["pipeline"]
    budget = team["_budget"]
    team_tokens = int(budget["tokens"]) if budget.get("tokens") else None
    wall = parse_wall_clock(budget.get("wall_clock"))
    deadline = time.time() + wall if wall else None

    # ── resolve members up front (fail before spending anything)
    solutions = [resolve_member(m) for m in pipeline]
    for m, sol in zip(pipeline, solutions):
        mf = _load_manifest(sol)
        if mf.get("runtime", "code") != "llm":
            raise TeamError(f"member {m!r} is runtime {mf.get('runtime', 'code')} — teams v1 runs llm-runtime members only")

    # ── state: fresh or resumed
    if resume_team_id:
        team_dir = runs_dir() / resume_team_id
        state_path = team_dir / "state.json"
        if not state_path.is_file():
            raise TeamError(f"unknown team run {resume_team_id!r}")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state["team"] != team["team"]:
            raise TeamError(f"team run {resume_team_id!r} belongs to team {state['team']!r}")
        if state["status"] != "gate":
            raise TeamError(f"team run {resume_team_id!r} is {state['status']!r} — only gate-paused runs resume")
        if not approve:
            return TEAM_EXIT_GATE, _format_gate_message(state, team_dir), resume_team_id
        state["status"] = "running"
        state["gate_pending"] = None
        state["gates_cleared"] = state.get("gates_cleared", []) + [state["completed"][-1]["agent"]]
        workspace = Path(state["workspace"])
    else:
        team_run_id = f"{time.strftime('%Y%m%d-%H%M%S')}-team-{team['team']}-{uuid.uuid4().hex[:4]}"
        team_dir = runs_dir() / team_run_id
        (team_dir / "legs").mkdir(parents=True, exist_ok=True)
        workspace = team_dir / "workspace"
        workspace.mkdir(exist_ok=True)
        state = {
            "team_run_id": team_run_id,
            "team": team["team"],
            "objective": objective,
            "pipeline": pipeline,
            "workspace": str(workspace),
            "completed": [],
            "next_index": 0,
            "gate_pending": None,
            "gates_cleared": [],
            "status": "running",
            "tokens_used": 0,
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        (team_dir / "brief.json").write_text(
            json.dumps({**state, "manifest_source": team.get("_source")}, indent=2), encoding="utf-8"
        )
        (team_dir / "manifest.yaml").write_text(
            yaml.safe_dump({k: v for k, v in team.items() if not k.startswith("_")}, sort_keys=False),
            encoding="utf-8",
        )

    def _save_state() -> None:
        state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        (team_dir / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")

    report: List[str] = [f"team {team['team']} · {len(pipeline)} legs · workspace {workspace}"]
    exit_code = 0

    i = state["next_index"]
    while i < len(pipeline):
        member = pipeline[i]
        sol = solutions[i]

        # team-level budget gates (leg budgets still apply inside each run)
        if team_tokens is not None and state["tokens_used"] >= team_tokens:
            state["status"] = "budget"
            report.append(f"STOP at leg {i + 1} ({member}): team token budget exhausted ({state['tokens_used']}/{team_tokens})")
            exit_code = 1
            break
        if deadline is not None and time.time() >= deadline:
            state["status"] = "budget"
            report.append(f"STOP at leg {i + 1} ({member}): team wall clock exhausted")
            exit_code = 1
            break

        report.append(f"leg {i + 1}/{len(pipeline)}: {member}")
        brief = _leg_brief(team, objective, i, state["completed"][-1] if state["completed"] else None, workspace)
        try:
            answer, info = run_with_agent_loop(
                sol, brief, provider=provider, model=model, yolo=yolo,
                registry=registry,
                workspace_override=workspace if _load_manifest(sol).get("llm_workspace") else None,
                record_dir=team_dir / "legs",
            )
        except Exception as exc:  # noqa: BLE001 — a crashing leg fails the team, visibly
            state["status"] = "failed"
            state["failed"] = {"leg": i + 1, "agent": member, "error": str(exc)}
            report.append(f"FAILED leg {i + 1} ({member}): {exc}")
            exit_code = 1
            break

        state["tokens_used"] += info.get("tokens", 0)
        leg_record = {"agent": member, "run_id": info["run_id"], "answer": answer, "tokens": info.get("tokens", 0)}

        ok, reasons = verify_leg(sol, answer, [workspace])
        if not ok:
            state["status"] = "failed"
            state["failed"] = {"leg": i + 1, "agent": member, "verify": reasons}
            report.append(f"QA-VERIFIER blocked handoff after {member}: {'; '.join(reasons)}")
            report.append("The failing leg's run is kept; fix the doctrine/artifact and rerun the team.")
            exit_code = 1
            _save_state()
            break

        state["completed"].append(leg_record)
        state["next_index"] = i + 1
        report.append(f"  ok  {member} · {info.get('tokens', 0)} tokens · run {info['run_id']}")

        gate = next((g for g in (team.get("gates") or []) if g.get("after") == member), None)
        if gate and member not in state["gates_cleared"]:
            state["status"] = "gate"
            state["gate_pending"] = {"after": member, "type": gate.get("type")}
            report.append(f"PAUSED at human gate after {member} — review, then: jebat agentix team run {team['team']} --resume-team {state['team_run_id']} --approve")
            exit_code = TEAM_EXIT_GATE
            _save_state()
            break
        i += 1
    else:
        state["status"] = "done"
        report.append(f"DONE · {len(state['completed'])} legs · {state['tokens_used']} tokens total")

    if state["status"] == "done":
        memo = _final_memo(team, state)
        (team_dir / "team-report.md").write_text(memo, encoding="utf-8", newline="\n")
        report.append(f"report: {team_dir / 'team-report.md'}")
    _save_state()
    return exit_code, "\n".join(report), state.get("team_run_id")


def _format_gate_message(state: Dict, team_dir: Path) -> str:
    completed = state["completed"][-1] if state["completed"] else {}
    return (
        f"team {state['team']} paused at human gate (after {state['gate_pending']['after']}).\n"
        f"Last leg answer (excerpt): {(completed.get('answer') or '')[:400]}\n"
        f"Workspace: {state['workspace']}\n"
        f"Approve and continue: jebat agentix team run {state['team']} --resume-team {state['team_run_id']} --approve"
    )


def _final_memo(team: Dict, state: Dict) -> str:
    lines = [
        f"# Team report — {team['team']}",
        "",
        f"Objective: {state['objective']}",
        f"Run: {state['team_run_id']} · {state['tokens_used']} tokens · {len(state['completed'])}/{len(state['pipeline'])} legs",
        "",
    ]
    for i, leg in enumerate(state["completed"], 1):
        lines.append(f"## Leg {i}: {leg['agent']} (run {leg['run_id']}, {leg['tokens']} tokens)")
        lines.append("")
        answer = (leg.get("answer") or "").strip()
        lines.append(answer[:2000] + ("…[truncated]" if len(answer) > 2000 else ""))
        lines.append("")
    return "\n".join(lines)
