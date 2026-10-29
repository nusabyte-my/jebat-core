"""Parallel Agentix operations: concurrency and exact route inheritance."""
import json
import threading
import time

import pytest

from jebat_cli_new.agentix import _scaffold
from jebat_cli_new.agentix_parallel import ParallelOperationError, run_parallel
from jebat_cli_new.models import CompletionResponse
from jebat_cli_new.providers import ProviderRegistry


class ParallelProvider:
    def __init__(self):
        self.calls = []
        self.lock = threading.Lock()
        self.active = 0
        self.max_active = 0

    def complete(self, req):
        with self.lock:
            self.calls.append((req.provider, req.model, req.prompt))
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        try:
            if "Split the objective" in req.prompt:
                return CompletionResponse(
                    text=json.dumps({"tasks": ["inspect API", "inspect UI", "inspect database"]}),
                    provider=req.provider, model=req.model, tokens_used=10, latency_ms=1,
                )
            time.sleep(0.08)
            marker = "API" if "inspect API" in req.prompt else "UI" if "inspect UI" in req.prompt else "database"
            return CompletionResponse(
                text=f"FINAL_ANSWER: {marker} complete", provider=req.provider,
                model=req.model, tokens_used=10, latency_ms=80,
            )
        finally:
            with self.lock:
                self.active -= 1


def test_parallel_workers_overlap_and_preserve_exact_route(tmp_path, monkeypatch):
    monkeypatch.setenv("JEBAT_AGENTIX_RUNS", str(tmp_path / "runs"))
    provider = ParallelProvider()
    registry = ProviderRegistry(path=str(tmp_path / "providers.json"))
    registry.register("selected-provider", provider)
    sol = _scaffold("parallel-test", "reflex", tmp_path)

    result, info = run_parallel(
        sol, "audit application", agents=3, provider="selected-provider",
        model="qwen2.5-coder:7b", registry=registry,
    )

    assert provider.max_active == 3
    assert len(provider.calls) == 4
    assert all(route == "selected-provider" and model == "qwen2.5-coder:7b" for route, model, _prompt in provider.calls)
    assert all(section in result for section in ("API complete", "UI complete", "database complete"))
    assert "## Worker 1 — inspect API" in result
    assert "## Worker 2 — inspect UI" in result
    assert "## Worker 3 — inspect database" in result
    assert info["agents"] == 3
    assert info["tokens"] == 30
    assert (tmp_path / "runs" / info["run_id"] / "result.md").is_file()


def test_parallel_inherits_active_provider_and_model(tmp_path, monkeypatch):
    monkeypatch.setenv("JEBAT_AGENTIX_RUNS", str(tmp_path / "runs"))
    provider = ParallelProvider()
    registry = ProviderRegistry(path=str(tmp_path / "providers.json"))
    registry.register("selected-provider", provider)
    registry.configs["selected-provider"].active = True
    registry.configs["selected-provider"].model = "user-selected-model"
    sol = _scaffold("active-route", "reflex", tmp_path)

    result, info = run_parallel(sol, "audit application", agents=3, registry=registry)

    assert info["provider"] == "selected-provider"
    assert info["model"] == "user-selected-model"
    assert all(route == "selected-provider" and model == "user-selected-model" for route, model, _prompt in provider.calls)


def test_parallel_does_not_fall_back_when_decomposition_fails(tmp_path):
    class BrokenProvider:
        def complete(self, req):
            raise RuntimeError("selected provider unavailable")

    registry = ProviderRegistry(path=str(tmp_path / "providers.json"))
    registry.register("chosen", BrokenProvider())
    sol = _scaffold("no-fallback", "reflex", tmp_path)

    with pytest.raises(ParallelOperationError, match="no model fallback"):
        run_parallel(sol, "task", agents=2, provider="chosen", model="exact-model", registry=registry)


def test_parallel_rejects_more_than_three_workers(tmp_path):
    with pytest.raises(ParallelOperationError, match="2 or 3"):
        run_parallel(tmp_path, "task", agents=4)
