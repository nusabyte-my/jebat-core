"""Focused WebUI chat route contract tests."""

import pytest

from jebat.services.webui import webui_server as webui


@pytest.mark.asyncio
async def test_webui_chat_returns_response_and_runtime_selection(monkeypatch):
    async def ensure_state():
        return None

    async def generate_chat_reply(**kwargs):
        assert kwargs["prompt"] == "Plan the release"
        assert kwargs["mode"] == "strategic"
        assert kwargs["provider_override"] == "llamacpp"
        assert kwargs["model_override"] == "jebat-qwen"
        return "Release plan ready", "llamacpp", type("Config", (), {"model": "jebat-qwen"})()

    monkeypatch.setattr(webui, "_ensure_connection_state", ensure_state)
    monkeypatch.setattr("jebat.llm.generate_chat_reply", generate_chat_reply)
    monkeypatch.setattr(webui, "RUNTIME_OVERRIDES", {"provider": "llamacpp", "model": "jebat-qwen"})

    result = await webui.chat(
        webui.ChatMessage(user_id="webui", message="Plan the release", thinking_mode="strategic")
    )

    assert result == {
        "success": True,
        "response": "Release plan ready",
        "provider": "llamacpp",
        "model": "jebat-qwen",
        "thinking_mode": "strategic",
        "preset": "default",
    }
