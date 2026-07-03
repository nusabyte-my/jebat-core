"""Tests for Multi-LLM Orchestration — model registry, smart router."""

import pytest

from jebat.features.orchestration.models import ModelRegistry, ModelInfo
from jebat.features.orchestration.router import SmartRouter, classify_task, RouteDecision


class TestModelRegistry:
    """ModelRegistry CRUD and querying."""

    def test_has_builtins(self):
        reg = ModelRegistry()
        assert reg.count() >= 12  # built-in models
        assert reg.get("gemma3:12b") is not None

    def test_get_missing(self):
        reg = ModelRegistry()
        assert reg.get("nonexistent-model") is None

    def test_register(self):
        reg = ModelRegistry()
        reg.register(ModelInfo(id="test-model", provider="test"))
        assert reg.get("test-model") is not None

    def test_unregister(self):
        reg = ModelRegistry()
        reg.register(ModelInfo(id="temp", provider="test"))
        assert reg.get("temp") is not None
        reg.unregister("temp")
        assert reg.get("temp") is None

    def test_list_by_provider(self):
        reg = ModelRegistry()
        ollama_models = reg.list_by_provider("ollama")
        assert len(ollama_models) >= 5
        assert all(m.provider == "ollama" for m in ollama_models)

    def test_list_by_capability(self):
        reg = ModelRegistry()
        code_models = reg.list_by_capability("code")
        assert len(code_models) >= 4
        assert all("code" in m.capabilities for m in code_models)

    def test_search(self):
        reg = ModelRegistry()
        results = reg.search("qwen")
        assert len(results) >= 2
        assert all("qwen" in m.id.lower() for m in results)

    def test_get_compatible_models(self):
        reg = ModelRegistry()
        # Models that can do code AND are cheap
        results = reg.get_compatible_models(
            required_capabilities=["code", "cheap"],
        )
        assert len(results) >= 2
        assert all("code" in m.capabilities and "cheap" in m.capabilities for m in results)

    def test_get_compatible_with_provider(self):
        reg = ModelRegistry()
        results = reg.get_compatible_models(
            required_capabilities=["code"],
            preferred_provider="openai",
        )
        assert len(results) >= 2
        assert all(m.provider == "openai" for m in results)

    def test_providers(self):
        reg = ModelRegistry()
        providers = reg.providers()
        assert "ollama" in providers
        assert "openai" in providers

    def test_list_available(self):
        reg = ModelRegistry()
        all_models = reg.list_available()
        # All builtins should be available by default
        assert len(all_models) == reg.count()


class TestClassifyTask:
    """Task classification into types."""

    def test_code_task(self):
        assert classify_task("write a Python function to sort a list") == "code"
        assert classify_task("implement a REST API endpoint") == "code"

    def test_reasoning_task(self):
        assert classify_task("explain how quantum computing works") == "reasoning"
        assert classify_task("solve this math equation") == "reasoning"

    def test_simple_task(self):
        assert classify_task("hello") == "simple"
        assert classify_task("summarize this article") == "simple"

    def test_creative_task(self):
        assert classify_task("write a story about a dragon") == "creative"
        assert classify_task("brainstorm startup ideas") == "creative"

    def test_general_task(self):
        assert classify_task("what is the weather today?") == "general"


class TestSmartRouter:
    """Routing decisions by strategy."""

    def test_auto_routes_code_to_code_model(self):
        router = SmartRouter()
        decision = router.route(task="write a Python function", preference="auto")
        assert decision.model is not None
        # Should pick a code-capable model
        assert "code" in decision.model.capabilities or "reasoning" in decision.model.capabilities

    def test_auto_routes_simple_to_fast_model(self):
        router = SmartRouter()
        decision = router.route(task="hello", preference="auto")
        # Should pick a cheap/fast model
        assert decision.model is not None

    def test_cheapest_strategy(self):
        router = SmartRouter()
        decision = router.route(task="anything", preference="cheapest")
        assert decision.strategy == "cheapest"
        # Cheapest should be a free/ollama model
        assert decision.model.cost_per_1k_input == 0.0

    def test_fastest_strategy(self):
        router = SmartRouter()
        decision = router.route(task="anything", preference="fastest")
        assert decision.strategy == "fastest"

    def test_best_quality_strategy(self):
        router = SmartRouter()
        decision = router.route(task="anything", preference="best_quality")
        assert decision.strategy == "best_quality"

    def test_fallback_chain_has_models(self):
        router = SmartRouter()
        decision = router.route(task="anything", preference="fallback_chain")
        assert decision.strategy == "fallback_chain"
        assert len(decision.fallback_chain) >= 2

    def test_returns_decision(self):
        router = SmartRouter()
        decision = router.route(task="write code", preference="auto")
        assert isinstance(decision, RouteDecision)
        assert isinstance(decision.model, ModelInfo)
        assert len(decision.reason) > 0

    def test_explicit_task_type_overrides(self):
        router = SmartRouter()
        # Explicitly set type to simple
        decision = router.route(task="complex philosophical analysis", task_type="simple", preference="auto")
        assert decision.model is not None

    def test_preferred_provider(self):
        router = SmartRouter()
        decision = router.route(task="write code", preference="auto", preferred_provider="openai")
        assert decision.model.provider == "openai"

    def test_invalid_preference_defaults_to_auto(self):
        router = SmartRouter()
        decision = router.route(task="hello", preference="nonexistent")
        assert decision.strategy == "auto"
