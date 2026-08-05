"""Unit tests: custom providers surfaced in the WebUI provider catalog + auth targets."""

import pytest

from jebat.features.auth.custom_providers import CUSTOM_PROVIDER_IDS
from jebat.services.webui import webui_server as webui_mod


@pytest.mark.unit
def test_webui_catalog_includes_custom_providers():
    catalog = webui_mod._provider_model_catalog()
    for pid in CUSTOM_PROVIDER_IDS:
        assert pid in catalog
        assert catalog[pid]["supports_custom"] is True


@pytest.mark.unit
def test_webui_env_targets_custom_provider():
    targets = webui_mod._provider_env_targets("zenmux")
    assert targets == ["ZENMUX_API_KEY", "ZENMUX_BASE_URL"]
    # Unrecognised provider yields empty list (400 path upstream)
    assert webui_mod._provider_env_targets("notacustom") == []
