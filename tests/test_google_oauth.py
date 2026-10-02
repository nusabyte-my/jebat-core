"""Google OAuth store + refresh + provider wiring.

No network: HTTP is monkeypatched at the jebat.llm.oauth._post_* seam.
Run: pytest tests/test_google_oauth.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest


@pytest.fixture()
def oauth_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    store = tmp_path / "oauth_tokens.json"
    monkeypatch.setenv("JEBAT_OAUTH_STORE", str(store))
    return store


def _write_entry(store: Path, **overrides) -> None:
    entry = {
        "client_id": "test-client.apps.googleusercontent.com",
        "client_secret": "test-secret",
        "scopes": ["https://www.googleapis.com/auth/generative-language.retriever"],
        "access_token": "ya29.fresh",
        "refresh_token": "1//refresh",
        "expires_at": time.time() + 3600,
        "connected_at": time.time(),
    }
    entry.update(overrides)
    store.write_text(json.dumps({"google": entry}), encoding="utf-8")


def test_status_disconnected_without_store(oauth_store: Path) -> None:
    from jebat.llm.oauth import google_oauth_status

    assert google_oauth_status().connected is False


def test_status_connected_with_refresh_token(oauth_store: Path) -> None:
    _write_entry(oauth_store)
    from jebat.llm.oauth import google_oauth_status

    status = google_oauth_status()
    assert status.connected is True
    assert status.scopes


def test_access_token_cached_when_fresh(oauth_store: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_entry(oauth_store)
    calls = []

    def _fail(url, data):  # must never be called for a fresh token
        calls.append(url)
        raise AssertionError("refresh should not run for a fresh token")

    monkeypatch.setattr("jebat.llm.oauth._post_sync", _fail)
    from jebat.llm.oauth import get_google_access_token

    assert get_google_access_token() == "ya29.fresh"
    assert calls == []


def test_access_token_refreshes_when_expired(oauth_store: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_entry(oauth_store, expires_at=time.time() - 10, access_token="ya29.stale")
    seen = {}

    def _fake_post(url, data):
        seen.update(data)
        return {"access_token": "ya29.refreshed", "expires_in": 3600}

    monkeypatch.setattr("jebat.llm.oauth._post_sync", _fake_post)
    from jebat.llm.oauth import get_google_access_token

    assert get_google_access_token() == "ya29.refreshed"
    assert seen["grant_type"] == "refresh_token"
    assert seen["refresh_token"] == "1//refresh"
    # persisted for next call
    stored = json.loads(oauth_store.read_text())
    assert stored["google"]["access_token"] == "ya29.refreshed"


def test_access_token_none_when_not_connected(oauth_store: Path) -> None:
    from jebat.llm.oauth import get_google_access_token

    assert get_google_access_token() is None


def test_disconnect_removes_entry(oauth_store: Path) -> None:
    _write_entry(oauth_store)
    from jebat.llm.oauth import google_oauth_disconnect, google_oauth_status

    assert google_oauth_disconnect() is True
    assert google_oauth_status().connected is False


def test_build_provider_google_uses_oauth_when_no_key(
    oauth_store: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr("jebat.llm.oauth.get_google_access_token", lambda: "ya29.bearer")

    # ensure the provider-auth store fallback cannot satisfy the key path
    monkeypatch.setattr("jebat.llm.auth._provider_auth_store", lambda: {})

    from jebat.llm.config import JebatLLMConfig
    from jebat.llm.providers import GoogleProvider, build_provider

    provider = build_provider(
        JebatLLMConfig(provider="google", model="gemini-2.0-flash")
    )
    assert isinstance(provider, GoogleProvider)
    assert provider.access_token == "ya29.bearer"
    assert provider.api_key == ""


def test_build_provider_google_raises_without_key_or_oauth(
    oauth_store: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr("jebat.llm.auth._provider_auth_store", lambda: {})
    monkeypatch.setattr("jebat.llm.oauth.get_google_access_token", lambda: None)

    from jebat.llm.config import JebatLLMConfig
    from jebat.llm.providers import build_provider

    with pytest.raises(RuntimeError, match="google"):
        build_provider(JebatLLMConfig(provider="google", model="gemini-2.0-flash"))
