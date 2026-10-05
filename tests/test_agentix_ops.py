"""Agentix ops tests — budget gates, eval (golden tasks), export, specialists."""

from __future__ import annotations

import json

import pytest
import yaml

from jebat_cli_new.agentix import (
    _build,
    _load_manifest,
    _route,
    _run_solution,
    _scaffold,
    _scaffold_from_specialist,
)
from jebat_cli_new.agentix_llm import parse_wall_clock
from jebat_cli_new.agentix_ops import apply_checks, evaluate_solution, export_solution
from jebat_cli_new.models import CompletionResponse
from jebat_cli_new.providers import ProviderRegistry


@pytest.fixture
def registry_file(tmp_path, monkeypatch):
    reg = tmp_path / "agentix-registry.json"
    monkeypatch.setattr("jebat_cli_new.agentix.REGISTRY_PATH", reg)
    return reg


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


def _mock_registry(tmp_path, responses):
    registry = ProviderRegistry(path=str(tmp_path / "providers.json"))
    registry.register("mock", MockProvider(responses))
    return registry


def _llm_solution(tmp_path, name="s", **manifest_extra):
    sol = _scaffold(name, "reflex", tmp_path)
    mf = _load_manifest(sol)
    mf.update(manifest_extra)
    (sol / "agentix.yaml").write_text(yaml.safe_dump(mf), encoding="utf-8")
    return sol


# ── Wall-clock parsing ──────────────────────────────────────────────

def test_parse_wall_clock():
    assert parse_wall_clock("30s") == 30.0
    assert parse_wall_clock("10m") == 600.0
    assert parse_wall_clock("1h") == 3600.0
    assert parse_wall_clock(90) == 90.0
    assert parse_wall_clock(None) is None
    assert parse_wall_clock("bogus") is None


# ── Budget gates in the loop ────────────────────────────────────────

def test_token_budget_stops_the_loop(tmp_path):
    sol = _llm_solution(tmp_path, "budgeted", budget={"tokens": 15})
    # Each mock response costs 10 tokens; 15-token budget allows 1 call + wrap-up.
    looping = (
        '<thought>t</thought><tool_call>'
        '{"tool": "list_dir", "args": {"path": "."}}'
        "</tool_call>"
    )
    registry = _mock_registry(tmp_path, [looping, looping, looping, looping])
    result, info = _run_solution(sol, "loop forever", registry=registry, yolo=True,
                                 provider="mock", model="mock")
    assert info["tokens"] <= 45  # budget cut the loop well before max_iterations=12


def test_deadline_stops_the_loop(tmp_path):
    sol = _llm_solution(tmp_path, "deadlined", budget={"wall_clock": "1s"})
    looping = (
        '<thought>t</thought><tool_call>'
        '{"tool": "list_dir", "args": {"path": "."}}'
        "</tool_call>"
    )
    # Many iterations would take far longer than 1s without the gate.
    registry = _mock_registry(tmp_path, [looping] * 99 + ["FINAL_ANSWER: never reached"])
    result, info = _run_solution(sol, "loop forever", registry=registry, yolo=True,
                                 provider="mock", model="mock", max_iterations=100)
    assert "never reached" not in result or info["tool_calls"] < 99


# ── Eval: checks, golden tasks, structural rules ────────────────────

def test_apply_checks_types():
    checks = [
        {"type": "contains", "value": "HELLO"},
        {"type": "not_contains", "value": "bye"},
        {"type": "regex", "value": r"\d+ items"},
    ]
    results = apply_checks("hello world — 42 items", checks)
    assert all(ok for _, ok, _ in results)
    assert not all(ok for _, ok, _ in apply_checks("bye", checks))


def test_eval_code_runtime_runs_golden_tasks(tmp_path):
    sol = _scaffold("evalme", "lattice", tmp_path)
    lines, failures = evaluate_solution(sol)
    assert failures == 0
    assert any("1 executed" in line for line in lines)


def test_eval_detects_failing_golden_check(tmp_path):
    sol = _scaffold("evalbad", "lattice", tmp_path)
    golden = sol / "golden" / "broken.json"
    golden.write_text(json.dumps({"task": "hello", "checks": [{"type": "contains", "value": "NONEXISTENT"}]}), encoding="utf-8")
    lines, failures = evaluate_solution(sol)
    assert failures >= 1
    assert any("NONEXISTENT" in line for line in lines)


def test_eval_llm_runtime_skips_without_live(tmp_path):
    sol = _llm_solution(tmp_path, "skips")
    golden = sol / "golden"
    golden.mkdir()
    (golden / "g.json").write_text(
        json.dumps({"task": "x", "checks": [{"type": "contains", "value": "y"}]}), encoding="utf-8"
    )
    lines, failures = evaluate_solution(sol)
    assert failures == 0
    assert any("skip" in line and "--live" in line for line in lines)


def test_eval_enforces_allowlist_cap(tmp_path):
    sol = _llm_solution(tmp_path, "fat", llm_tools=[f"tool{i}" for i in range(12)])
    lines, failures = evaluate_solution(sol)
    assert failures >= 1
    assert any("cap is 10" in line for line in lines)


def test_eval_reports_structural_errors(tmp_path):
    sol = _scaffold("struct", "lattice", tmp_path)
    (sol / "agent.py").unlink()
    lines, failures = evaluate_solution(sol)
    assert failures >= 1
    assert any("entrypoint" in line for line in lines)


# ── Export ──────────────────────────────────────────────────────────

def test_export_claude_subagent(tmp_path):
    sol = _llm_solution(tmp_path, "exportable")
    out = export_solution(sol, "claude-subagent", tmp_path / "export")
    text = out.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name: exportable" in text
    assert "description:" in text
    assert "tools: Read" in text  # native read_file mapped to Read
    assert "model: inherit" in text
    assert "ReAct" in text  # doctrine body carried over


def test_export_skill_format(tmp_path):
    sol = _llm_solution(tmp_path, "skilly")
    out = export_solution(sol, "skill", tmp_path / "export")
    assert out.name == "SKILL.md"
    text = out.read_text(encoding="utf-8")
    assert 'name: "skilly"' in text
    assert "description:" in text


def test_export_requires_doctrine(tmp_path):
    sol = _scaffold("coded", "lattice", tmp_path)
    with pytest.raises(SystemExit):
        export_solution(sol, "claude-subagent", tmp_path / "export")


# ── Specialist catalog ──────────────────────────────────────────────

def test_create_from_specialist_renames(tmp_path):
    sol = _scaffold_from_specialist("security-audit", "my-audit", tmp_path)
    mf = _load_manifest(sol)
    assert mf["name"] == "my-audit"
    assert mf["runtime"] == "llm"
    assert "security" in mf["description"]  # lineage description preserved for routing
    assert (sol / "agent.md").is_file()
    assert _build(sol)["template"] == "reflex"


def test_create_from_unknown_specialist_lists(tmp_path):
    with pytest.raises(SystemExit, match="unknown specialist"):
        _scaffold_from_specialist("nonexistent", "x", tmp_path)


def test_specialist_catalog_complete():
    from jebat_cli_new.agentix import SPECIALISTS_DIR

    expected = {
        "security-audit", "osint-recon", "code-reviewer", "test-writer",
        "doc-writer", "data-analyst", "marketing-strategist", "ads-manager",
        "seo-auditor", "incident-responder", "release-manager",
        "contract-reviewer", "support-triage", "competitor-watch",
    }
    actual = {p.name for p in SPECIALISTS_DIR.iterdir() if (p / "agentix.yaml").is_file()}
    assert actual == expected


def test_route_matches_specialist_description(tmp_path, registry_file):
    sol = _scaffold_from_specialist("osint-recon", "recon", tmp_path)
    _build(sol)
    from jebat_cli_new.agentix import _deploy

    _deploy(sol, "local", "x")
    routed_sol, mf = _route("passive reconnaissance footprinting for acme.test")
    assert mf["name"] == "recon"
