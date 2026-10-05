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
    # max_iterations=8 -> floor 8*64=512; budget 600 allows 6 calls at 100
    # tokens each, so the budget binds before the iteration cap.
    sol = _llm_solution(tmp_path, "budgeted", max_iterations=8, budget={"tokens": 600})
    looping = (
        '<thought>t</thought><tool_call>'
        '{"tool": "list_dir", "args": {"path": "."}}'
        "</tool_call>"
    )
    registry = ProviderRegistry(path=str(tmp_path / "providers.json"))
    registry.register("mock", MockProvider([looping] * 20))

    class Costly(MockProvider):
        def complete(self, req):
            resp = super().complete(req)
            return CompletionResponse(text=resp.text, model="mock", provider="mock",
                                      tokens_used=100, latency_ms=1)

    registry.providers["mock"] = Costly([looping] * 20)
    result, info = _run_solution(sol, "loop forever", registry=registry, yolo=True,
                                 provider="mock", model="mock")
    assert info["tokens"] <= 700  # 6 budgeted calls + wrap-up synthesis call
    assert info["tool_calls"] <= 6


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
    _sol, mf, _ranked = _route("passive reconnaissance footprinting for acme.test")
    assert mf["name"] == "recon"


# ── Quickwins: doctor, budget sanity, run registry, resume, stdin, routing ──

def test_doctor_reports_and_prunes_dangling(tmp_path, monkeypatch):
    from jebat_cli_new.agentix_ops import doctor

    reg = tmp_path / "registry.json"
    reg.write_text(json.dumps({"ghost": {"path": str(tmp_path / "gone")}}), encoding="utf-8")
    monkeypatch.setattr("jebat_cli_new.agentix.REGISTRY_PATH", reg)

    lines, failures = doctor(fix=False)
    assert failures == 0  # dangling is a warning
    assert any("dangling" in line for line in lines)

    lines, failures = doctor(fix=True)
    assert any("pruned" in line for line in lines)
    assert json.loads(reg.read_text(encoding="utf-8")) == {}


def test_doctor_flags_stale_build_and_drift(tmp_path, monkeypatch):
    from jebat_cli_new.agentix_ops import doctor

    sol = _llm_solution(tmp_path, "stale-drift")
    _build(sol)
    (sol / "agentix.yaml").write_text(
        yaml.safe_dump({**_load_manifest(sol), "version": "9.9.9"}), encoding="utf-8"
    )
    reg = tmp_path / "registry.json"
    reg.write_text(json.dumps({"stale-drift": {"path": str(sol)}}), encoding="utf-8")
    monkeypatch.setattr("jebat_cli_new.agentix.REGISTRY_PATH", reg)

    lines, failures = doctor()
    assert failures == 0
    assert any("stale" in line.lower() for line in lines)


def test_doctor_flags_unrunnable_budget(tmp_path, monkeypatch):
    from jebat_cli_new.agentix_ops import doctor

    sol = _llm_solution(tmp_path, "poor", budget={"tokens": 100})
    reg = tmp_path / "registry.json"
    reg.write_text(json.dumps({"poor": {"path": str(sol)}}), encoding="utf-8")
    monkeypatch.setattr("jebat_cli_new.agentix.REGISTRY_PATH", reg)

    lines, failures = doctor()
    assert failures >= 1
    assert any("floor" in line for line in lines)


def test_spawn_refuses_absurd_budget(tmp_path):
    sol = _llm_solution(tmp_path, "cheap", budget={"tokens": 50})
    registry = _mock_registry(tmp_path, ["FINAL_ANSWER: never"])
    with pytest.raises(Exception, match="refuse to spawn"):
        _run_solution(sol, "go", registry=registry, provider="mock", model="mock")


def test_run_records_to_run_registry(tmp_path, monkeypatch):
    runs = tmp_path / "runs"
    monkeypatch.setenv("JEBAT_AGENTIX_RUNS", str(runs))
    sol = _llm_solution(tmp_path, "recorded")
    registry = _mock_registry(tmp_path, ["FINAL_ANSWER: done"])
    result, info = _run_solution(sol, "hello", registry=registry, provider="mock", model="mock")
    run_path = runs / info["run_id"]
    assert (run_path / "brief.json").is_file()
    assert (run_path / "messages.json").is_file()
    assert (run_path / "events.jsonl").is_file()
    assert (run_path / "manifest.yaml").is_file()
    brief = json.loads((run_path / "brief.json").read_text(encoding="utf-8"))
    assert brief["task"] == "hello" and brief["resumed_from"] is None
    messages = json.loads((run_path / "messages.json").read_text(encoding="utf-8"))
    assert messages[0]["role"] == "user"


def test_resume_continues_conversation(tmp_path, monkeypatch):
    runs = tmp_path / "runs"
    monkeypatch.setenv("JEBAT_AGENTIX_RUNS", str(runs))
    sol = _llm_solution(tmp_path, "resumable")
    registry = _mock_registry(tmp_path, ["FINAL_ANSWER: first", "FINAL_ANSWER: second"])

    r1, info1 = _run_solution(sol, "turn one", registry=registry, provider="mock", model="mock")
    r2, info2 = _run_solution(
        sol, "turn two", registry=registry, provider="mock", model="mock",
        resume_from=info1["run_id"],
    )
    assert info2["resumed_from"] == info1["run_id"]
    messages = json.loads((runs / info2["run_id"] / "messages.json").read_text(encoding="utf-8"))
    user_messages = [m for m in messages if m["role"] == "user"]
    assert [m["content"] for m in user_messages] == ["turn one", "turn two"]

    with pytest.raises(Exception, match="unknown run id"):
        _run_solution(sol, "x", registry=registry, provider="mock", model="mock", resume_from="nope")


def test_code_runtime_rejects_resume(tmp_path):
    sol = _scaffold("stateless", "lattice", tmp_path)
    with pytest.raises(SystemExit, match="stateless"):
        _run_solution(sol, "x", resume_from="whatever")


def test_provider_error_returns_exit_code_one(tmp_path, monkeypatch, capsys):
    from jebat_cli_new.agentix import run_agentix_command

    runs = tmp_path / "runs"
    monkeypatch.setenv("JEBAT_AGENTIX_RUNS", str(runs))
    sol = _llm_solution(tmp_path, "broken-provider")
    registry = _mock_registry(tmp_path, ["[JEBAT provider error: HTTP Error 500]"])

    def fake_registry():
        return registry

    monkeypatch.setattr("jebat_cli_new.providers.ProviderRegistry", fake_registry)
    rc = run_agentix_command(["run", str(sol), "hello", "--provider", "mock", "--model", "mock"])
    assert rc == 1
    assert "provider call failed" in capsys.readouterr().err


def test_run_reads_task_from_stdin(tmp_path, monkeypatch, capsys):
    import io

    from jebat_cli_new.agentix import run_agentix_command

    monkeypatch.setenv("JEBAT_AGENTIX_RUNS", str(tmp_path / "runs"))
    sol = _llm_solution(tmp_path, "piped")
    registry = _mock_registry(tmp_path, ["FINAL_ANSWER: piped task ran"])
    seen = []

    class Recording(MockProvider):
        def complete(self, req):
            seen.append(req.prompt)
            return super().complete(req)

    registry.providers["mock"] = Recording(registry.providers["mock"].responses)
    monkeypatch.setattr("jebat_cli_new.providers.ProviderRegistry", lambda: registry)
    monkeypatch.setattr("sys.stdin", io.StringIO("task from stdin\n"))
    rc = run_agentix_command(["run", str(sol), "-", "--provider", "mock", "--model", "mock"])
    assert rc == 0
    assert "task from stdin" in seen[0]


def test_ask_shows_top3_candidates(tmp_path, monkeypatch, capsys):
    from jebat_cli_new.agentix import _deploy, run_agentix_command

    monkeypatch.setenv("JEBAT_AGENTIX_RUNS", str(tmp_path / "runs"))
    a = _llm_solution(tmp_path, "alpha", description="audit security vulnerabilities in repos")
    b = _llm_solution(tmp_path, "beta", description="audit security posture of networks")
    reg = tmp_path / "registry.json"
    monkeypatch.setattr("jebat_cli_new.agentix.REGISTRY_PATH", reg)
    _deploy(a, "local", "x")
    _deploy(b, "local", "x")

    registry = _mock_registry(tmp_path, ["FINAL_ANSWER: routed"])
    monkeypatch.setattr("jebat_cli_new.providers.ProviderRegistry", lambda: registry)
    rc = run_agentix_command(["ask", "audit the security vulnerabilities", "--provider", "mock", "--model", "mock"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "also matched" in out and "beta" in out


def test_status_shows_runtime_and_stale(tmp_path, monkeypatch, capsys):
    from jebat_cli_new.agentix import _deploy, run_agentix_command

    sol = _llm_solution(tmp_path, "vis")
    reg = tmp_path / "registry.json"
    monkeypatch.setattr("jebat_cli_new.agentix.REGISTRY_PATH", reg)
    _deploy(sol, "local", "x")

    rc = run_agentix_command(["status"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "(llm)" in out
    assert "STALE" not in out  # deploy just built it

    (sol / "agentix.yaml").write_text(
        yaml.safe_dump({**_load_manifest(sol), "version": "2.0.0"}), encoding="utf-8"
    )
    capsys.readouterr()
    run_agentix_command(["status"])
    assert "STALE" in capsys.readouterr().out
