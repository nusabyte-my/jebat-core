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
