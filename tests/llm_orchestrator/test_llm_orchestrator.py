"""Tests for AI LLM Orchestration engine."""

import asyncio
import pytest

from jebat.features.llm_orchestrator.llm_orchestrator import (
    LLMProfile,
    DualLLMOrchestrator,
    CrossValidationOrchestrator,
    DebateOrchestrator,
    OrchestrationResult,
)


class TestLLMProfile:
    """LLMProfile data object behavior."""

    def test_default_profile_empty_strings(self):
        """Default profile should use empty strings (not None)."""
        p = LLMProfile()
        assert p.model == ""
        assert p.provider == ""
        assert p.system_prompt_extra == ""

    def test_custom_profile(self):
        """Custom values should be stored."""
        p = LLMProfile(model="gpt-4o", provider="openai", system_prompt_extra="Be concise.")
        assert p.model == "gpt-4o"
        assert p.provider == "openai"
        assert p.system_prompt_extra == "Be concise."

    def test_display_default(self):
        """Display with no model/provider."""
        p = LLMProfile()
        assert p.display() == "<default>"

    def test_display_with_model(self):
        """Display with model only."""
        p = LLMProfile(model="gemma3:12b")
        assert p.display() == "gemma3:12b"

    def test_display_with_both(self):
        """Display with provider and model."""
        p = LLMProfile(provider="ollama", model="gemma3:12b")
        assert p.display() == "ollama/gemma3:12b"


class TestDualLLMOrchestrator:
    """Dual LLM orchestrator — planner + executor."""

    def test_create_default(self):
        """Default orchestrator should create default profiles."""
        orch = DualLLMOrchestrator()
        assert orch.planner is not None
        assert orch.executor is not None
        assert orch.planner.model == ""
        assert "planner" in orch.planner.system_prompt_extra.lower()

    def test_create_with_profiles(self):
        """Orchestrator with specific profiles."""
        planner = LLMProfile(model="gpt-4o-mini", provider="openai")
        executor = LLMProfile(model="gpt-4o", provider="openai")
        orch = DualLLMOrchestrator(planner_profile=planner, executor_profile=executor)
        assert orch.planner.model == "gpt-4o-mini"
        assert orch.executor.model == "gpt-4o"

    def test_run_mocked(self, monkeypatch):
        """Mock LLM calls and verify orchestration completes."""
        async def fake_llm(system_prompt, user_message, profile=None):
            if "planner" in system_prompt.lower() or "Decompose" in user_message:
                return "1. Step one\n2. Step two\n3. Step three"
            return "Executed successfully!"

        monkeypatch.setattr(
            "jebat.features.llm_orchestrator.llm_orchestrator._call_llm",
            fake_llm,
        )
        orch = DualLLMOrchestrator()
        result = asyncio.run(orch.run("Test task"))
        assert result.success
        assert "Step one" in result.plan
        assert "Executed successfully!" in result.execution


class TestCrossValidationOrchestrator:
    """Cross-validation orchestrator — produce then validate."""

    def test_default_validation(self):
        """Default strictness should be 'normal'."""
        orch = CrossValidationOrchestrator()
        assert orch.strictness == "normal"

    def test_strict_validation(self):
        """Strict mode should be accepted."""
        orch = CrossValidationOrchestrator(strictness="strict")
        assert orch.strictness == "strict"

    def test_relaxed_validation(self):
        """Relaxed mode should be accepted."""
        orch = CrossValidationOrchestrator(strictness="relaxed")
        assert orch.strictness == "relaxed"

    def test_run_mocked(self, monkeypatch):
        """Mock LLM calls and verify produce+validate completes."""
        async def fake_llm(system_prompt, user_message, profile=None):
            if "Produce" in user_message:
                return "Here is my output."
            return "PASSED"

        monkeypatch.setattr(
            "jebat.features.llm_orchestrator.llm_orchestrator._call_llm",
            fake_llm,
        )
        orch = CrossValidationOrchestrator()
        result = asyncio.run(orch.run("Write docs"))
        assert result.success
        assert result.execution == "Here is my output."


class TestDebateOrchestrator:
    """Debate orchestrator — two independent analyses then synthesis."""

    def test_default_rounds(self):
        """Default should be 2 rounds."""
        orch = DebateOrchestrator()
        assert orch.max_rounds == 2

    def test_custom_rounds(self):
        """Custom round count should be stored."""
        orch = DebateOrchestrator(max_rounds=3)
        assert orch.max_rounds == 3

    def test_min_rounds(self):
        """Minimum 1 round should be accepted."""
        orch = DebateOrchestrator(max_rounds=1)
        assert orch.max_rounds == 1

    def test_run_mocked(self, monkeypatch):
        """Mock LLM calls and verify debate completes."""
        async def fake_llm(system_prompt, user_message, profile=None):
            if "Debater A" in system_prompt:
                return "Analysis A"
            elif "Debater B" in system_prompt:
                return "Analysis B"
            elif "synthesizer" in system_prompt.lower():
                return "Synthesised answer"
            return "OK"

        monkeypatch.setattr(
            "jebat.features.llm_orchestrator.llm_orchestrator._call_llm",
            fake_llm,
        )
        orch = DebateOrchestrator(max_rounds=1)
        result = asyncio.run(orch.run("Test problem"))
        assert result.success
        assert "Synthesised answer" in result.final_output
        assert len(result.debate_rounds) == 1
