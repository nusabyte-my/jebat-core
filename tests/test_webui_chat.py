"""Focused WebUI chat route contract tests."""

import pytest
from fastapi import FastAPI, HTTPException

from jebat.services.webui import webui_server as webui


def test_webui_static_routes_are_registered():
    app = FastAPI()
    webui._mount_static(app)
    app.include_router(webui.webui_router)

    paths = [getattr(route, "path", "") for route in app.routes]
    assert "/webui/static/js" in paths


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
    monkeypatch.setattr(webui, "CHAT_CONVERSATIONS", {})

    result = await webui.chat(
        webui.ChatMessage(user_id="webui", message="Plan the release", thinking_mode="strategic")
    )

    assert result["success"] is True
    assert result["response"] == "Release plan ready"
    assert result["provider"] == "llamacpp"
    assert result["model"] == "jebat-qwen"
    assert result["thinking_mode"] == "strategic"
    assert result["preset"] == "default"
    assert result["conversation_id"] in webui.CHAT_CONVERSATIONS


@pytest.mark.asyncio
async def test_conversations_are_scoped_to_the_requesting_user(monkeypatch):
    async def ensure_state():
        return None

    monkeypatch.setattr(webui, "_ensure_connection_state", ensure_state)
    monkeypatch.setattr(webui, "_persist_conversations", lambda: None)
    monkeypatch.setattr(webui, "CHAT_CONVERSATIONS", {})

    created = await webui.create_conversation(
        webui.ConversationCreateRequest(user_id="user-a", title="Release planning")
    )
    visible = await webui.list_conversations(user_id="user-a")

    assert visible["conversations"] == [created]
    with pytest.raises(HTTPException, match="conversation not found") as exc_info:
        await webui.get_conversation(created["id"], user_id="user-b")
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_agent_profiles_are_persisted_and_scoped(monkeypatch):
    async def ensure_state():
        return None

    monkeypatch.setattr(webui, "_ensure_connection_state", ensure_state)
    monkeypatch.setattr(webui, "_persist_agent_profiles", lambda: None)
    monkeypatch.setattr(webui, "AGENT_PROFILES", {})

    created = await webui.create_agent_profile(
        webui.AgentProfileCreateRequest(
            user_id="user-a",
            name="Release reviewer",
            description="Checks release readiness.",
            agent_type="analytical",
            capabilities=["review", "release"],
            provider="llamacpp",
            model="jebat-qwen",
        )
    )

    assert created["name"] == "Release reviewer"
    assert created["capabilities"] == ["review", "release"]
    assert (await webui.list_agent_profiles(user_id="user-a"))["profiles"] == [created]
    assert (await webui.list_agent_profiles(user_id="user-b"))["profiles"] == []


@pytest.mark.asyncio
async def test_chat_applies_owned_agent_profile_guidance(monkeypatch):
    async def ensure_state():
        return None

    async def generate_chat_reply(**kwargs):
        assert "You are Release reviewer, a analytical agent." in kwargs["prompt"]
        assert "Highlight deployment risks." in kwargs["prompt"]
        return "Review complete", "llamacpp", type("Config", (), {"model": "jebat-qwen"})()

    monkeypatch.setattr(webui, "_ensure_connection_state", ensure_state)
    monkeypatch.setattr(webui, "_persist_conversations", lambda: None)
    monkeypatch.setattr(webui, "_persist_agent_profiles", lambda: None)
    monkeypatch.setattr(webui, "CHAT_CONVERSATIONS", {})
    monkeypatch.setattr(webui, "AGENT_PROFILES", {})
    monkeypatch.setattr("jebat.llm.generate_chat_reply", generate_chat_reply)

    profile = await webui.create_agent_profile(
        webui.AgentProfileCreateRequest(
            user_id="user-a",
            name="Release reviewer",
            agent_type="analytical",
            system_prompt="Highlight deployment risks.",
        )
    )
    result = await webui.chat(
        webui.ChatMessage(
            user_id="user-a", message="Review this release", agent_profile_id=profile["id"]
        )
    )

    assert result["agent_profile_id"] == profile["id"]


@pytest.mark.asyncio
async def test_agent_run_plan_is_persisted_and_profile_scoped(monkeypatch):
    async def ensure_state():
        return None

    monkeypatch.setattr(webui, "_ensure_connection_state", ensure_state)
    monkeypatch.setattr(webui, "_persist_agent_profiles", lambda: None)
    monkeypatch.setattr(webui, "_persist_agent_runs", lambda: None)
    monkeypatch.setattr(webui, "AGENT_PROFILES", {})
    monkeypatch.setattr(webui, "AGENT_RUNS", {})

    profile = await webui.create_agent_profile(
        webui.AgentProfileCreateRequest(
            user_id="user-a", name="Release reviewer", capabilities=["review"]
        )
    )
    run = await webui.plan_agent_run(
        webui.AgentRunPlanRequest(
            user_id="user-a", agent_profile_id=profile["id"], objective="Review the release"
        )
    )

    assert run["status"] == "planned"
    assert run["agent_name"] == "Release reviewer"
    assert len(run["plan"]) == 3
    assert (await webui.list_agent_runs(user_id="user-a"))["runs"] == [run]
