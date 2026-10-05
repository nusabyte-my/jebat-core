"""Quickwin regression tests — CLI word dispatch, stream failover, MCP robustness."""

from __future__ import annotations

import asyncio
import json
import sys

import pytest

import jebat_cli_new.jebat as cli


def _run_main(monkeypatch, argv, **stubs):
    """Run cli.main() with sys.argv set and heavy collaborators stubbed."""
    monkeypatch.setattr(sys, "argv", ["jebat"] + argv)
    monkeypatch.setattr(cli, "banner", lambda: None)
    monkeypatch.setattr(cli, "show_setup", lambda *a, **k: None)

    class BoomAgent:
        def __init__(self, *a, **k):
            pass

        def step(self, *a, **k):  # any reach into the LLM path fails loudly
            raise AssertionError("agent.step called — word fell through to the LLM")

        def chat(self, *a, **k):
            raise AssertionError("agent.chat called")

    monkeypatch.setattr(cli, "Agent", BoomAgent)
    for name, fn in stubs.items():
        monkeypatch.setattr(cli, name, fn)
    return cli.main()


def test_status_dispatch_prints_card_without_llm(monkeypatch, capsys):
    rc = _run_main(monkeypatch, ["status"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "JEBAT v" in out and "agentix" in out


def test_doctor_dispatch_runs_health_check(monkeypatch, capsys):
    rc = _run_main(monkeypatch, ["doctor"])
    out = capsys.readouterr().out
    assert rc in (0, 1)
    assert "doctor" in out


def test_repl_dispatch_opens_repl_not_llm(monkeypatch, capsys):
    opened = []
    monkeypatch.setattr(cli, "repl", lambda *a, **k: opened.append(True))
    rc = _run_main(monkeypatch, ["repl"])
    assert rc is None and opened == [True]
    assert "agent.step" not in capsys.readouterr().out


def test_think_maps_to_chat(monkeypatch, capsys):
    chats = []

    class ChatAgent:
        def __init__(self, *a, **k):
            pass

        def chat(self, prompt, **k):
            chats.append(prompt)
            return "thought about it"

        def step(self, *a, **k):
            raise AssertionError("think must not use tools")

    rc = _run_main(monkeypatch, ["think", "why", "is", "the", "sky", "blue"], Agent=ChatAgent)
    assert rc is None
    assert chats == ["why is the sky blue"]


def test_webui_reports_missing_uvicorn_gracefully(monkeypatch, capsys):
    import builtins

    real_import = builtins.__import__

    def no_uvicorn(name, *a, **k):
        if name == "uvicorn":
            raise ImportError("no uvicorn")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", no_uvicorn)
    rc = _run_main(monkeypatch, ["webui"])
    assert rc == 1
    assert "uvicorn" in capsys.readouterr().err


# ── #5 streaming failover ───────────────────────────────────────────

def _collect(agen):
    async def drive():
        return [chunk async for chunk in agen]

    return asyncio.run(drive())


def test_stream_failover_falls_back_before_first_chunk(monkeypatch):
    from jebat.llm import providers as P

    class PreStreamFailure:
        def generate_stream(self, **k):
            raise RuntimeError("cold start boom")
            yield  # pragma: no cover

    monkeypatch.setattr(P, "build_provider", lambda cfg: PreStreamFailure())
    async def fake_failover(**k):
        return _fake_response(), "local"

    monkeypatch.setattr(P, "generate_with_failover", fake_failover)
    chunks = _collect(P.generate_stream_with_failover(_cfg(), "hi"))
    assert [c["type"] for c in chunks] == ["metadata", "token", "done"]
    assert chunks[1]["text"] == "fallback answer"


def test_stream_failover_reraises_after_emitted_chunks(monkeypatch):
    from jebat.llm import providers as P

    class MidStreamFailure:
        async def generate_stream(self, **k):
            yield {"type": "token", "text": "PARTIAL "}
            raise RuntimeError("mid-stream boom")

    monkeypatch.setattr(P, "build_provider", lambda cfg: MidStreamFailure())
    fallback_calls = []

    async def fake_failover(**k):
        fallback_calls.append(1)
        return _fake_response(), "local"

    monkeypatch.setattr(P, "generate_with_failover", fake_failover)
    with pytest.raises(RuntimeError, match="mid-stream boom"):
        _collect(P.generate_stream_with_failover(_cfg(), "hi"))
    assert fallback_calls == []  # no silent regeneration


def _fake_response():
    from jebat.llm.providers import ProviderGeneration
    from jebat.llm.token_usage import TokenUsage

    return ProviderGeneration(text="fallback answer", usage=TokenUsage(prompt_tokens=1, completion_tokens=2, total_tokens=3))


def _cfg():
    from jebat.llm.config import JebatLLMConfig

    return JebatLLMConfig(provider="llamacpp", fallback_providers=("local",))


# ── #7 ask multi-word + #8 MCP SystemExit ───────────────────────────

def test_ask_accepts_unquoted_multi_word(monkeypatch, capsys, tmp_path):
    from jebat_cli_new.agentix import run_agentix_command

    monkeypatch.setenv("JEBAT_AGENTIX_RUNS", str(tmp_path / "runs"))
    reg = tmp_path / "registry.json"
    monkeypatch.setattr("jebat_cli_new.agentix.REGISTRY_PATH", reg)
    rc = run_agentix_command(["ask", "audit", "the", "repo", "for", "leaks"])
    assert rc == 1  # routing error, NOT argparse exit 2
    assert "registry is empty" in capsys.readouterr().err


def test_mcp_server_survives_system_exit(tmp_path, capsys, monkeypatch):
    import io

    from jebat_cli_new import agentix_mcp_server

    requests = [
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
        json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "agentix_status", "arguments": {}}}),
        json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/list"}),
    ]
    monkeypatch.setattr("sys.stdin", io.StringIO("\n".join(requests) + "\n"))
    agentix_mcp_server.serve("definitely-not-a-real-solution")
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 3  # server survived the tools/call
    second = json.loads(out[1])
    assert second["id"] == 2 and second["result"]["isError"] is True
    assert "solution not found" in second["result"]["content"][0]["text"]
    assert json.loads(out[2])["id"] == 3  # tools/list still answered
