"""Agentix team tests — manifests, resolution, pipelines, gates, budgets."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from jebat_cli_new.agentix import _scaffold, _load_manifest
from jebat_cli_new.agentix_llm import runs_dir
from jebat_cli_new.agentix_team import (
    TEAM_EXIT_GATE,
    TeamError,
    load_team,
    list_teams,
    resolve_member,
    run_team,
    verify_leg,
)
from jebat_cli_new.models import CompletionResponse
from jebat_cli_new.providers import ProviderRegistry


class MockProvider:
    def __init__(self, responses):
        self.responses = list(responses)
        self.index = 0

    def complete(self, req):
        if self.index < len(self.responses):
            text = self.responses[self.index]
            self.index += 1
        else:
            text = "FINAL_ANSWER: Done."
        return CompletionResponse(text=text, model="mock", provider="mock", tokens_used=10, latency_ms=1)


@pytest.fixture
def team_env(tmp_path, monkeypatch):
    """Isolate registry + runs; return the tmp base."""
    monkeypatch.setattr("jebat_cli_new.agentix.REGISTRY_PATH", tmp_path / "registry.json")
    monkeypatch.setenv("JEBAT_AGENTIX_RUNS", str(tmp_path / "runs"))
    return tmp_path


def _team_yaml(tmp_path, **overrides):
    base = {
        "team": "test-team",
        "description": "Two-leg test pipeline.",
        "budget": {"tokens": 900000, "wall_clock": "2h"},
        "pipeline": ["leg-a", "leg-b"],
        "spawns": ["leg-a", "leg-b"],
        "gates": [],
    }
    base.update(overrides)
    path = tmp_path / f"{base['team']}.yaml"
    path.write_text(yaml.safe_dump(base), encoding="utf-8")
    return path


def _member_sol(tmp_path, name, shared_registry, artifacts=(), responses=(), jailed=True):
    """A minimal llm-runtime member, deployed to the test registry, with its
    own named mock provider on the SHARED team registry (one registry serves
    all legs — distinct provider names prevent cross-leg clobbering)."""
    provider_name = f"mock-{name}"
    sol = _scaffold(name, "reflex", tmp_path)
    mf = _load_manifest(sol)
    mf["llm_tools"] = ["write_file"] if jailed else ["read_file"]
    mf["provider"] = provider_name
    mf["model"] = "mock"
    if jailed:
        mf["llm_workspace"] = "workspace"
    (sol / "agentix.yaml").write_text(yaml.safe_dump(mf), encoding="utf-8")
    for artifact in artifacts:
        doctrine = (sol / "agent.md").read_text(encoding="utf-8")
        (sol / "agent.md").write_text(doctrine + f"\nOutput: write {artifact} in workspace/\n", encoding="utf-8")
    from jebat_cli_new.agentix import _deploy_local

    _deploy_local(sol)  # registers into REGISTRY_PATH (patched by team_env)
    shared_registry.register(provider_name, MockProvider(list(responses)))
    return sol


def _write_call(path, content):
    return (
        '<thought>w</thought><tool_call>'
        f'{{"tool": "write_file", "args": {{"path": "{path}", "content": "{content}"}}}}'
        "</tool_call>"
    )


# ── Manifest validation ─────────────────────────────────────────────

def test_team_manifest_rejects_missing_roster(tmp_path):
    path = _team_yaml(tmp_path, spawns=["leg-a"])
    with pytest.raises(TeamError, match="not in spawns"):
        load_team(path)


def test_team_manifest_rejects_bad_gate(tmp_path):
    path = _team_yaml(tmp_path, gates=[{"after": "leg-z", "type": "human"}])
    with pytest.raises(TeamError, match="not a pipeline member"):
        load_team(path)


def test_team_manifest_rejects_empty_pipeline(tmp_path):
    path = _team_yaml(tmp_path, pipeline=[], spawns=[])
    with pytest.raises(TeamError, match="pipeline"):
        load_team(path)


# ── Resolution ──────────────────────────────────────────────────────

def test_resolve_member_from_catalog():
    sol = resolve_member("security-audit")
    assert (sol / "agent.md").is_file()


def test_resolve_member_unknown_raises():
    with pytest.raises(TeamError, match="not found"):
        resolve_member("no-such-worker")


def test_list_teams_ships_three():
    listing = list_teams()
    for team in ("go-to-market", "security-review", "product-release"):
        assert team in listing


# ── qa-verifier ─────────────────────────────────────────────────────

def test_verify_leg_checks_declared_artifact(tmp_path):
    sol = _member_sol(tmp_path, "verifier", ProviderRegistry(path=str(tmp_path / "p1.json")), artifacts=["report.md"])
    ws = tmp_path / "ws"
    ws.mkdir()
    ok, reasons = verify_leg(sol, "done", [ws])
    assert not ok and any("report.md" in r for r in reasons)
    (ws / "report.md").write_text("x", encoding="utf-8")
    ok, reasons = verify_leg(sol, "done", [ws])
    assert ok


def test_verify_leg_blocks_provider_error(tmp_path):
    sol = _member_sol(tmp_path, "verr", ProviderRegistry(path=str(tmp_path / "p2.json")))
    ok, reasons = verify_leg(sol, "[JEBAT provider error: HTTP 500]", [tmp_path / "ws"])
    assert not ok and any("provider error" in r for r in reasons)


# ── Full pipeline runs ──────────────────────────────────────────────

def test_two_leg_team_with_workspace_handoff(team_env, tmp_path):
    shared = ProviderRegistry(path=str(tmp_path / "prov.json"))
    _member_sol(
        tmp_path, "leg-a", shared, artifacts=["brief.md"],
        responses=[_write_call("brief.md", "the brief"), "FINAL_ANSWER: brief written"],
    )
    _member_sol(
        tmp_path, "leg-b", shared, artifacts=["memo.md"],
        responses=[_write_call("memo.md", "the memo"), "FINAL_ANSWER: memo written"],
    )
    team = load_team(_team_yaml(tmp_path))

    code, report, run_id = run_team(team, "produce brief then memo", registry=shared, yolo=True)
    assert code == 0, report
    assert "DONE" in report
    team_dir = runs_dir() / run_id
    state = json.loads((team_dir / "state.json").read_text(encoding="utf-8"))
    assert state["status"] == "done" and len(state["completed"]) == 2
    ws = Path(state["workspace"])
    assert (ws / "brief.md").is_file() and (ws / "memo.md").is_file()
    assert (team_dir / "team-report.md").is_file()
    # legs recorded as full runs inside the team dir
    legs = list((team_dir / "legs").iterdir())
    assert len(legs) == 2


def test_verify_failure_stops_team(team_env, tmp_path):
    # leg-a declares an artifact its mock never writes -> qa-verifier blocks
    shared = ProviderRegistry(path=str(tmp_path / "prov.json"))
    _member_sol(tmp_path, "leg-a", shared, artifacts=["missing.md"], responses=["FINAL_ANSWER: nothing written"])
    _member_sol(tmp_path, "leg-b", shared, responses=["FINAL_ANSWER: never reached"])
    team = load_team(_team_yaml(tmp_path))

    code, report, run_id = run_team(team, "go", registry=shared, yolo=True)
    assert code == 1
    assert "QA-VERIFIER blocked" in report and "missing.md" in report
    state = json.loads((runs_dir() / run_id / "state.json").read_text(encoding="utf-8"))
    assert state["status"] == "failed"


def test_human_gate_pauses_and_resumes(team_env, tmp_path):
    shared = ProviderRegistry(path=str(tmp_path / "prov.json"))
    _member_sol(
        tmp_path, "leg-a", shared, artifacts=["step.md"],
        responses=[_write_call("step.md", "x"), "FINAL_ANSWER: leg a done"],
    )
    _member_sol(tmp_path, "leg-b", shared, responses=["FINAL_ANSWER: leg b done"])
    team = load_team(_team_yaml(tmp_path, gates=[{"after": "leg-a", "type": "human"}]))

    code, report, run_id = run_team(team, "two legs with a gate", registry=shared, yolo=True)
    assert code == TEAM_EXIT_GATE
    assert "PAUSED at human gate" in report
    state = json.loads((runs_dir() / run_id / "state.json").read_text(encoding="utf-8"))
    assert state["status"] == "gate" and state["gate_pending"]["after"] == "leg-a"

    # resume without --approve stays paused
    code, report, _ = run_team(team, "x", resume_team_id=run_id, approve=False, registry=shared, yolo=True)
    assert code == TEAM_EXIT_GATE and "Approve and continue" in report

    # resume with --approve finishes the pipeline
    code, report, _ = run_team(team, "x", resume_team_id=run_id, approve=True, registry=shared, yolo=True)
    assert code == 0 and "DONE" in report
    state = json.loads((runs_dir() / run_id / "state.json").read_text(encoding="utf-8"))
    assert state["status"] == "done" and state["gates_cleared"] == ["leg-a"]


def test_team_budget_stops_mid_pipeline(team_env, tmp_path):
    shared = ProviderRegistry(path=str(tmp_path / "prov.json"))
    _member_sol(tmp_path, "leg-a", shared, artifacts=["a.md"],
                responses=[_write_call("a.md", "x"), "FINAL_ANSWER: a"])
    _member_sol(tmp_path, "leg-b", shared, artifacts=["b.md"], responses=["FINAL_ANSWER: b"])
    # team budget below the tokens the first leg spends (mock: 10/call)
    team = load_team(_team_yaml(tmp_path, budget={"tokens": 5, "wall_clock": "2h"}))

    code, report, run_id = run_team(team, "go", registry=shared, yolo=True)
    assert code == 1
    assert "budget exhausted" in report
    state = json.loads((runs_dir() / run_id / "state.json").read_text(encoding="utf-8"))
    assert state["status"] == "budget"


def test_code_runtime_member_rejected(team_env, tmp_path):
    from jebat_cli_new.agentix import _deploy_local

    sol = _scaffold("leg-code", "lattice", tmp_path)  # runtime: code
    _deploy_local(sol)
    team = load_team(_team_yaml(tmp_path, pipeline=["leg-code"], spawns=["leg-code"]))
    with pytest.raises(TeamError, match="llm-runtime"):
        run_team(team, "go", registry=ProviderRegistry(path=str(tmp_path / "p3.json")))
