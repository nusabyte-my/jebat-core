"""Agentix tests — scaffold/build/deploy surface, LLM runtime, MCP server.

Covers the merged agentix.py (reflex|flow|lattice) plus the LLM runtime
(agentix_llm: allowlist + workspace jail + doctrine) and the stdio MCP
bridge (agentix_mcp_server).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from jebat_cli_new.agentix import (
    _build,
    _deploy,
    _load_manifest,
    _route,
    _run_solution,
    _scaffold,
    _validate,
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


def _mock_registry(tmp_path, responses):
    """ProviderRegistry isolated to tmp_path — register() persists to disk."""
    registry = ProviderRegistry(path=str(tmp_path / "providers.json"))
    registry.register("mock", MockProvider(responses))
    return registry


@pytest.fixture
def registry_file(tmp_path, monkeypatch):
    """Isolate the agentix registry (a module-level Path constant)."""
    reg = tmp_path / "agentix-registry.json"
    monkeypatch.setattr("jebat_cli_new.agentix.REGISTRY_PATH", reg)
    return reg


# ── Scaffolding ─────────────────────────────────────────────────────

@pytest.mark.parametrize("template", ["reflex", "flow", "lattice"])
def test_scaffold_all_templates(tmp_path, template):
    sol = _scaffold(f"s-{template}", template, tmp_path)
    mf = _load_manifest(sol)
    assert mf["template"] == template
    assert mf["description"]  # routing key present
    assert _validate(sol) == []


def test_reflex_scaffold_is_llm_runtime_with_doctrine(tmp_path):
    sol = _scaffold("reflexy", "reflex", tmp_path)
    mf = _load_manifest(sol)
    assert mf["runtime"] == "llm"
    assert mf["max_iterations"] == 12
    assert "read_file" in mf["llm_tools"]
    doctrine = (sol / "agent.md").read_text(encoding="utf-8")
    assert "ReAct" in doctrine


def test_scaffold_refuses_existing(tmp_path):
    _scaffold("dup", "reflex", tmp_path)
    with pytest.raises(FileExistsError):
        _scaffold("dup", "reflex", tmp_path)


# ── Build / validate ────────────────────────────────────────────────

def test_build_writes_manifest(tmp_path):
    sol = _scaffold("built", "reflex", tmp_path)
    info = _build(sol)
    assert (sol / ".agentix" / "build.json").is_file()
    stored = json.loads((sol / ".agentix" / "build.json").read_text(encoding="utf-8"))
    assert stored["manifest_sha256"] == info["manifest_sha256"]


def test_validate_reports_missing_entrypoint(tmp_path):
    sol = _scaffold("broken", "lattice", tmp_path)
    (sol / "agent.py").unlink()
    errors = _validate(sol)
    assert any("entrypoint" in e for e in errors)


def test_validate_reports_broken_tool_syntax(tmp_path):
    sol = _scaffold("syntaxbroke", "lattice", tmp_path)
    (sol / "tools" / "boom.py").write_text("def (:\n", encoding="utf-8")
    mf = _load_manifest(sol)
    mf["tools"] = ["tools/boom.py"]
    (sol / "agentix.yaml").write_text(yaml.safe_dump(mf), encoding="utf-8")
    errors = _validate(sol)
    assert any("boom.py" in e for e in errors)


# ── Deploy: gate + registry ─────────────────────────────────────────

def test_deploy_local_registers_in_registry(tmp_path, registry_file):
    sol = _scaffold("deployed", "reflex", tmp_path)
    out = _deploy(sol, "local", "irrelevant")
    assert "registered locally" in out
    registry = json.loads(registry_file.read_text(encoding="utf-8"))
    assert "deployed" in registry
    assert Path(registry["deployed"]["path"]) == sol.resolve()


def test_deploy_target_gate(tmp_path, registry_file):
    sol = _scaffold("gated", "reflex", tmp_path)
    mf = _load_manifest(sol)
    mf["deploy"]["allow"] = ["local"]
    (sol / "agentix.yaml").write_text(yaml.safe_dump(mf), encoding="utf-8")
    with pytest.raises(SystemExit, match="not in deploy.allow"):
        _deploy(sol, "vps", "unused-host")


# ── Routing (type-only `ask`) ───────────────────────────────────────

def test_route_matches_description_words(tmp_path, registry_file):
    recon = _scaffold("osint-recon", "reflex", tmp_path)
    mf = _load_manifest(recon)
    mf["description"] = "Passive reconnaissance and attack-surface mapping from a domain"
    (recon / "agentix.yaml").write_text(yaml.safe_dump(mf), encoding="utf-8")
    _deploy(recon, "local", "x")

    other = _scaffold("docs-writer", "flow", tmp_path)
    _deploy(other, "local", "x")

    sol, routed = _route("map the attack surface of acme.test with reconnaissance")
    assert routed["name"] == "osint-recon"


def test_route_no_match_raises(tmp_path, registry_file):
    sol = _scaffold("only", "reflex", tmp_path)
    _deploy(sol, "local", "x")
    with pytest.raises(SystemExit, match="no deployed solution matches"):
        _route("frobnicate the widget flanges")


# ── LLM runtime: doctrine, allowlist, jail ──────────────────────────

def test_llm_runtime_spawns_real_agent_with_doctrine(tmp_path, registry_file, monkeypatch):
    sol = _scaffold("doctrined", "reflex", tmp_path)
    registry = _mock_registry(tmp_path, ["FINAL_ANSWER: via-llm"])
    seen = []

    class Recording(MockProvider):
        def complete(self, req):
            seen.append(req.prompt)
            return super().complete(req)

    registry.providers["mock"] = Recording(registry.providers["mock"].responses)

    result, info = _run_solution(sol, "hello", registry=registry, provider="mock", model="mock")
    assert result == "via-llm"
    assert "ReAct" in seen[0]  # agent.md doctrine reached the system prompt


def test_llm_runtime_enforces_allowlist_in_loop(tmp_path, registry_file):
    sol = _scaffold("allowlisted", "reflex", tmp_path)
    mf = _load_manifest(sol)
    mf["llm_tools"] = ["write_file"]  # terminal denied
    (sol / "agentix.yaml").write_text(yaml.safe_dump(mf), encoding="utf-8")

    deny_then_answer = (
        '<thought>t</thought><tool_call>'
        '{"tool": "terminal", "args": {"command": "echo hi"}}'
        "</tool_call>"
    )
    registry = _mock_registry(tmp_path, [deny_then_answer, "FINAL_ANSWER: saw denial"])

    result, info = _run_solution(sol, "try the shell", registry=registry, yolo=True, provider="mock", model="mock")
    assert result == "saw denial"
    assert info["tool_calls"] == 1


def test_llm_runtime_workspace_jail(tmp_path, registry_file):
    sol = _scaffold("jailed", "reflex", tmp_path)
    mf = _load_manifest(sol)
    mf["llm_tools"] = ["write_file"]
    mf["llm_workspace"] = "workspace"
    (sol / "agentix.yaml").write_text(yaml.safe_dump(mf), encoding="utf-8")
    (tmp_path / "secret.txt").write_text("secret", encoding="utf-8")

    escape = (
        '<thought>e</thought><tool_call>'
        '{"tool": "write_file", "args": {"path": "../secret.txt", "content": "pwned"}}'
        "</tool_call>"
    )
    inside = (
        '<thought>w</thought><tool_call>'
        '{"tool": "write_file", "args": {"path": "out.txt", "content": "ok"}}'
        "</tool_call>"
    )
    registry = _mock_registry(tmp_path, [escape, inside, "FINAL_ANSWER: done"])

    result, info = _run_solution(sol, "work", registry=registry, yolo=True, provider="mock", model="mock")
    assert (sol / "workspace" / "out.txt").read_text(encoding="utf-8") == "ok"
    assert (tmp_path / "secret.txt").read_text(encoding="utf-8") == "secret"  # untouched


def test_code_runtime_still_executes_entrypoint(tmp_path, registry_file):
    sol = _scaffold("coded", "lattice", tmp_path)
    assert _load_manifest(sol).get("runtime", "code") == "code"
    result, info = _run_solution(sol, "hello world")
    assert "example" in result  # lattice orchestrator calls tools/example.py
    assert info == {}


# ── MCP stdio bridge ────────────────────────────────────────────────

def _mcp_roundtrip(monkeypatch, requests, solution):
    import io

    from jebat_cli_new import agentix_mcp_server

    monkeypatch.setattr("sys.stdin", io.StringIO("\n".join(requests) + "\n"))
    agentix_mcp_server.serve(solution)
    return agentix_mcp_server


def test_mcp_initialize_and_tools_list(tmp_path, registry_file, monkeypatch, capsys):
    _mcp_roundtrip(
        monkeypatch,
        [
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
        ],
        "any-solution-name",
    )
    out = capsys.readouterr().out.strip().splitlines()
    init = json.loads(out[0])
    assert init["result"]["protocolVersion"] == "2024-11-05"
    tools = json.loads(out[1])["result"]["tools"]
    assert {t["name"] for t in tools} == {"agentix_run", "agentix_status"}


def test_mcp_tool_call_runs_llm_solution(tmp_path, registry_file, monkeypatch, capsys):
    sol = _scaffold("mcpd", "reflex", tmp_path)
    mf = _load_manifest(sol)
    mf["provider"] = "mock"
    mf["model"] = "mock"
    (sol / "agentix.yaml").write_text(yaml.safe_dump(mf), encoding="utf-8")
    registry = _mock_registry(tmp_path, ["FINAL_ANSWER: via-mcp"])

    def fake_registry():
        return registry

    monkeypatch.setattr("jebat_cli_new.providers.ProviderRegistry", fake_registry)
    _mcp_roundtrip(
        monkeypatch,
        [
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 7,
                    "method": "tools/call",
                    "params": {"name": "agentix_run", "arguments": {"task": "hello"}},
                }
            )
        ],
        str(sol),
    )
    response = json.loads(capsys.readouterr().out.strip())
    assert response["id"] == 7
    assert response["result"]["content"][0]["text"] == "via-mcp"
