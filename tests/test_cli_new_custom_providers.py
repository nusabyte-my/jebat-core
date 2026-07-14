"""Unit tests: custom providers wired into the shipped jebat_cli_new CLI."""

import pytest

from jebat.features.auth.custom_providers import CUSTOM_PROVIDER_IDS
from jebat_cli_new import jebat as jc
from jebat_cli_new.models import ProviderConfig
from jebat_cli_new.providers import OpenAIProviderImpl, OllamaProviderImpl, _provider_factory


@pytest.mark.unit
def test_cli_new_provider_kinds_include_custom():
    kinds = {k for k, *_ in jc.PROVIDER_KINDS}
    assert set(CUSTOM_PROVIDER_IDS) <= kinds


@pytest.mark.unit
def test_cli_new_model_catalog_includes_custom():
    for pid in CUSTOM_PROVIDER_IDS:
        assert pid in jc.MODEL_CATALOG
        assert jc.MODEL_CATALOG[pid], f"{pid} should have a placeholder model catalog"


@pytest.mark.unit
def test_cli_new_factory_routes_custom_to_openai():
    cfg = ProviderConfig(
        id="ocg",
        name="OpenCode Go",
        api_base="http://localhost/v1",
        model="opencode-go/default",
        kind="opencode_go",
    )
    impl = _provider_factory(cfg)
    assert isinstance(impl, OpenAIProviderImpl)
    # Unknown non-custom kind falls back to the placeholder AnyProvider
    unknown = _provider_factory(ProviderConfig(id="x", name="x", kind="mystery"))
    assert unknown.__class__.__name__ == "AnyProvider"


@pytest.mark.unit
def test_cli_new_openai_compat_routes_to_openai():
    cfg = ProviderConfig(
        id="cc", name="Custom", api_base="http://localhost/v1", model="m", kind="openai-compat"
    )
    assert isinstance(_provider_factory(cfg), OpenAIProviderImpl)


class _FakeURLResponse:
    def __init__(self, payload):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self._payload


@pytest.mark.unit
def test_fetch_live_models_parses(monkeypatch):
    import urllib.request as ureq

    monkeypatch.setattr(
        ureq, "urlopen", lambda req, timeout=8: _FakeURLResponse(b'{"data":[{"id":"a"},{"id":"b"}]}')
    )
    assert jc._fetch_live_models("http://x/v1") == ["a", "b"]


@pytest.mark.unit
def test_fetch_live_models_handles_failure(monkeypatch):
    import urllib.request as ureq

    monkeypatch.setattr(ureq, "urlopen", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("nope")))
    assert jc._fetch_live_models("http://x/v1") == []
