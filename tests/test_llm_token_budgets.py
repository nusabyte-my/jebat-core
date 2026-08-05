from __future__ import annotations

from dataclasses import dataclass

import pytest

from jebat.llm.chat_runtime import generate_chat_reply
from jebat.llm.config import JebatLLMConfig
from jebat.llm.providers import ProviderGeneration, generate_with_failover
from jebat.llm.token_usage import budget_input, estimate_tokens, usage_from_texts
from jebat_cli_new.agent import AgentLoop


pytestmark = pytest.mark.unit


def test_budget_input_reserves_completion_tokens() -> None:
    bounded = budget_input(
        "word " * 500,
        "system instruction",
        context_window=100,
        max_output_tokens=30,
        provider="local",
    )

    assert bounded.input_budget == 70
    assert bounded.truncated is True
    assert bounded.input_tokens <= bounded.input_budget
    assert estimate_tokens(f"{bounded.system_prompt}\n\n{bounded.prompt}", provider="local") <= 70


@pytest.mark.asyncio
async def test_failover_budgets_input_before_provider_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    received: dict[str, str] = {}

    @dataclass
    class Provider:
        async def generate_with_metadata(self, prompt: str, system_prompt: str | None = None) -> ProviderGeneration:
            received["prompt"] = prompt
            received["system"] = system_prompt or ""
            return ProviderGeneration("ok", usage_from_texts(prompt, "ok", provider="local"))

    monkeypatch.setattr("jebat.llm.providers.build_provider", lambda config: Provider())
    config = JebatLLMConfig(provider="local", context_window=80, max_tokens=25, fallback_providers=())

    response, _ = await generate_with_failover(config, prompt="word " * 500, system_prompt="system", return_metadata=True)

    assert isinstance(response, ProviderGeneration)
    assert estimate_tokens(f"{received['system']}\n\n{received['prompt']}", provider="local") <= 55


@pytest.mark.asyncio
async def test_chat_runtime_budgets_conversation_and_exposes_usage(monkeypatch: pytest.MonkeyPatch) -> None:
    config = JebatLLMConfig(provider="local", context_window=100, max_tokens=40, fallback_providers=())
    monkeypatch.setattr("jebat.llm.chat_runtime.resolve_llm_config", lambda **_: config)

    text, provider, _, metadata = await generate_chat_reply(
        "current " * 200,
        conversation_messages=[{"role": "assistant", "content": "history " * 200}],
        return_metadata=True,
    )

    assert provider == "local"
    assert text
    assert metadata.prompt_tokens_estimate <= 60
    assert metadata.usage["total_tokens"] >= metadata.usage["prompt_tokens"]


def test_agent_limits_provider_prompt_and_estimates_usage() -> None:
    received: dict[str, str] = {}

    class Provider:
        def complete(self, request):
            received["prompt"] = request.prompt
            return type("Response", (), {"text": "ok", "model": request.model, "provider": "test", "tokens_used": 0, "latency_ms": 1})()

    class Registry:
        def get(self, provider: str):
            return Provider()

    agent = AgentLoop(Registry(), default_provider="test", context_window=80)
    response = agent._call_provider("word " * 500, "test", "model", max_tokens=25)

    assert estimate_tokens(received["prompt"], model="model", provider="test") <= 55
    assert response.tokens_used > 0
