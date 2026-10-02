"""Boot warmup must cap generation — the single llama.cpp slot is precious.

Regression: warmup ran with the full preset budget, generated 34-81 tokens at
~0.2 tok/s (minutes of slot occupancy) and queued every user chat behind it.
Only prompt PROCESSING warms the cache, so generation must be capped.
"""

from __future__ import annotations

import asyncio

import pytest


@pytest.fixture()
def fake_env(monkeypatch: pytest.MonkeyPatch):
    import jebat.services.webui.webui_server as m

    captured: dict = {}

    class _Config:
        model = "test-model"

    async def _fake_generate_chat_reply(**kwargs):
        captured.update(kwargs)
        return "pong", "llamacpp", _Config()

    async def _noop() -> None:
        return None

    async def _fast_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr("jebat.llm.generate_chat_reply", _fake_generate_chat_reply)
    monkeypatch.setattr(m, "_ensure_connection_state", _noop)
    monkeypatch.setattr(m.asyncio, "sleep", _fast_sleep)
    monkeypatch.delenv("JEBAT_WEBUI_WARMUP", raising=False)
    return m, captured


def test_warmup_caps_generation_tokens(fake_env) -> None:
    m, captured = fake_env
    asyncio.run(m.warm_prompt_cache())
    assert captured, "warmup never called generate_chat_reply"
    assert captured.get("max_tokens_override") == 4, (
        "warmup must cap generation — uncapped it holds the llama.cpp slot for minutes"
    )


def test_warmup_can_be_disabled(fake_env, monkeypatch: pytest.MonkeyPatch) -> None:
    m, captured = fake_env
    monkeypatch.setenv("JEBAT_WEBUI_WARMUP", "0")
    asyncio.run(m.warm_prompt_cache())
    assert captured == {}, "warmup ran despite JEBAT_WEBUI_WARMUP=0"
