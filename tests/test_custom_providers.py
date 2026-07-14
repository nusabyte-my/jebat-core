"""Unit tests for custom (non-standard) LLM provider registry + auth-first flow."""

import sys
import types

import pytest

from jebat.features.auth import auth as auth_mod
from jebat.features.auth.auth import (
    CUSTOM_PROVIDER_IDS,
    SUPPORTED_PROVIDERS,
    fetch_provider_models,
    get_custom_provider,
    is_custom_provider,
    select_provider_model,
)
from jebat.features.auth.custom_providers import CUSTOM_PROVIDERS, CustomProvider
from jebat.llm import providers as providers_mod
from jebat.llm.config import JebatLLMConfig
from jebat.llm.providers import CustomOpenAIProvider, build_provider


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeRequests:
    def __init__(self, payload):
        self._payload = payload

    def get(self, url, headers=None, timeout=None):
        self.last_url = url
        self.last_headers = headers
        return _FakeResponse(self._payload)


@pytest.mark.unit
def test_custom_providers_registry_complete():
    assert set(CUSTOM_PROVIDER_IDS) == {
        "opencode_go",
        "opencode_zen",
        "zenmux",
        "tokerrouter",
        "agent_router",
    }
    for cp in CUSTOM_PROVIDERS.values():
        assert isinstance(cp, CustomProvider)
        assert cp.api_key_env and cp.base_url_env and cp.models_path


@pytest.mark.unit
def test_custom_providers_have_placeholder_models():
    for cp in CUSTOM_PROVIDERS.values():
        assert cp.default_models, f"{cp.id} should ship a placeholder model catalog"
        assert all(isinstance(m, str) and m for m in cp.default_models)


@pytest.mark.unit
def test_supported_providers_includes_custom():
    assert all(is_custom_provider(p) for p in CUSTOM_PROVIDER_IDS)
    assert all(p in SUPPORTED_PROVIDERS for p in CUSTOM_PROVIDER_IDS)


@pytest.mark.unit
def test_lookup_helpers():
    assert is_custom_provider("notacustom") is False
    assert is_custom_provider("opencode_go") is True
    assert get_custom_provider("ZENMUX") is CUSTOM_PROVIDERS["zenmux"]
    assert get_custom_provider("nope") is None


@pytest.mark.unit
def test_fetch_provider_models_parses_openai_format(monkeypatch):
    fake = _FakeRequests({"data": [{"id": "m1"}, {"id": "m2"}]})
    monkeypatch.setitem(sys.modules, "requests", fake)
    models = fetch_provider_models("zenmux", "k", "http://x/v1")
    assert models == ["m1", "m2"]
    assert fake.last_url == "http://x/v1/models"
    assert fake.last_headers == {"Authorization": "Bearer k"}


@pytest.mark.unit
def test_fetch_provider_models_handles_failure(monkeypatch):
    class _Boom:
        def get(self, *a, **k):
            raise RuntimeError("network down")

    monkeypatch.setitem(sys.modules, "requests", _Boom())
    assert fetch_provider_models("zenmux", "k", "http://x") == []


@pytest.mark.unit
def test_select_provider_model_picks_from_list(monkeypatch):
    fake = _FakeRequests({"data": [{"id": "alpha"}, {"id": "beta"}]})
    monkeypatch.setitem(sys.modules, "requests", fake)
    monkeypatch.setattr("builtins.input", lambda prompt="": "2")
    assert select_provider_model("zenmux", "k", "http://x") == "beta"


@pytest.mark.unit
def test_select_provider_model_default_on_empty_input(monkeypatch):
    fake = _FakeRequests({"data": [{"id": "alpha"}, {"id": "beta"}]})
    monkeypatch.setitem(sys.modules, "requests", fake)
    monkeypatch.setattr("builtins.input", lambda prompt="": "")
    assert select_provider_model("zenmux", "k", "http://x", current="alpha") == "alpha"


@pytest.mark.unit
def test_auth_test_custom_branch(monkeypatch):
    monkeypatch.setattr(auth_mod, "_retrieve", lambda provider, key_type: "secret")
    monkeypatch.setattr(auth_mod, "fetch_provider_models", lambda *a, **k: ["m1"])
    import asyncio

    out = asyncio.run(auth_mod.auth_test("zenmux"))
    assert out.get("valid") is True
    assert out.get("models_available") == 1


@pytest.mark.unit
def test_auth_test_custom_branch_failure(monkeypatch):
    monkeypatch.setattr(auth_mod, "_retrieve", lambda provider, key_type: "secret")
    monkeypatch.setattr(auth_mod, "fetch_provider_models", lambda *a, **k: [])
    import asyncio

    out = asyncio.run(auth_mod.auth_test("zenmux"))
    assert out.get("valid") is False


@pytest.mark.unit
def test_build_custom_provider_routing(monkeypatch):
    monkeypatch.setattr(providers_mod, "get_provider_secret", lambda provider: "secret-key")
    monkeypatch.setenv("ZENMUX_BASE_URL", "http://zenmux.local")
    cfg = JebatLLMConfig(provider="zenmux", model="m1", temperature=0.2, max_tokens=100)
    provider = build_provider(cfg)
    assert isinstance(provider, CustomOpenAIProvider)
    assert provider.base_url == "http://zenmux.local"
    assert provider.api_key == "secret-key"
    assert provider.provider_id == "zenmux"


@pytest.mark.unit
def test_build_custom_provider_missing_base_url_raises(monkeypatch):
    monkeypatch.setattr(providers_mod, "get_provider_secret", lambda provider: "secret-key")
    monkeypatch.delenv("ZENMUX_BASE_URL", raising=False)
    cfg = JebatLLMConfig(provider="zenmux", model="m1", temperature=0.2, max_tokens=100)
    with pytest.raises(ValueError):
        build_provider(cfg)


@pytest.mark.unit
def test_list_supported_providers_includes_custom():
    names = {entry["name"] for entry in providers_mod.list_supported_providers()}
    assert set(CUSTOM_PROVIDER_IDS) <= names
