"""Focused tests for the WebUI integrations command-center overview."""

import pytest

from jebat.services.webui import webui_server as webui


@pytest.mark.asyncio
async def test_integrations_overview_reports_safe_operational_counts(monkeypatch):
    async def ensure_state():
        return None

    monkeypatch.setattr(webui, "_ensure_connection_state", ensure_state)
    monkeypatch.setattr(
        webui,
        "_console_meta",
        lambda: {
            "jebat-gateway": {"gateway_port": 18789, "agent_names": ["Hermes"], "channel_names": ["telegram"]},
            "channels": ["discord", "telegram"],
            "integrations": [{"name": "OpenClaw Bundle", "state": "versioned"}],
            "skills": {"count": 4, "top": [{"name": "hermes-agent"}]},
        },
    )
    monkeypatch.setattr(webui, "_gateway_template", lambda: {"mcpServers": {"filesystem": {}}})
    monkeypatch.setattr(
        webui,
        "CHANNEL_CONNECTIONS",
        {"telegram": {"status": "active", "active": True, "missing": [], "config_keys": ["bot_token"]}},
    )

    result = await webui.integrations_overview()

    assert result["gateway"] == {"status": "configured", "port": 18789, "agent_count": 1, "channel_count": 1}
    assert result["integrations"] == {"status": "available", "count": 1, "statuses": ["versioned"]}
    assert result["channels"]["active_count"] == 1
    assert result["mcp"] == {"status": "configured", "server_count": 1}
    assert result["skills"] == {"status": "available", "count": 4, "featured_count": 1}
    assert result["workflow"] == {"status": "available", "tracked_workflows": 0, "tracked_executions": 0}


@pytest.mark.asyncio
async def test_integrations_overview_never_returns_audit_payloads(monkeypatch):
    async def ensure_state():
        return None

    monkeypatch.setattr(webui, "_ensure_connection_state", ensure_state)
    monkeypatch.setattr(
        webui,
        "_console_meta",
        lambda: {
            "jebat-gateway": {"gateway_port": None, "agent_names": [], "channel_names": []},
            "channels": [],
            "integrations": [],
            "skills": {"count": 0, "top": []},
        },
    )
    monkeypatch.setattr(webui, "_gateway_template", lambda: {})
    monkeypatch.setattr(webui, "CHANNEL_CONNECTIONS", {})

    from jebat.features import security

    monkeypatch.setattr(
        security,
        "read_audit_log",
        lambda limit: [{"ts": "2026-07-16T00:00:00Z", "approved": True, "params": {"token": "secret-value"}}],
    )

    result = await webui.integrations_overview()

    assert result["audit"] == {"status": "available", "recent_count": 1, "approved_count": 1, "latest_at": "2026-07-16T00:00:00Z"}
    assert "secret-value" not in str(result)
