"""Test configuration management."""

import os
import tempfile

import pytest

from jebat.config.manager import ConfigManager


def test_config_layering_and_override() -> None:
    """Test three-layer config: defaults < .env < .jebatrc."""
    import yaml
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        # Write defaults
        defaults = os.path.join(td, "config.yaml")
        with open(defaults, "w") as f:
            yaml.safe_dump(
                {"model": {"provider": "openrouter", "model": "test-model"}}, f
            )
        # Write .env (secrets layer)
        env_file = os.path.join(td, ".env")
        with open(env_file, "w") as f:
            f.write("MODEL_PROVIDER=anthropic\n")
        # Write .jebatrc (project layer)
        proj_file = os.path.join(td, ".jebatrc")
        with open(proj_file, "w") as f:
            yaml.safe_dump({"model": {"temperature": 0.7}}, f)
        cm = ConfigManager(
            config_path=defaults, env_path=env_file, project_path=proj_file
        )
        try:
            # .env wins over defaults
            assert cm.get("model.provider") == "anthropic"
            # defaults preserved
            assert cm.get("model.model") == "test-model"
            # project layer adds
            assert cm.get("model.temperature") == 0.7
        finally:
            pass  # no cleanup needed


def test_config_set_and_get() -> None:
    """Test that config can be set and retrieved."""
    import yaml
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        defaults = os.path.join(td, "config.yaml")
        with open(defaults, "w") as f:
            yaml.safe_dump({"model": {"provider": "openai"}}, f)
        cm = ConfigManager(config_path=defaults)
        assert cm.get("model.provider") == "openai"
        cm.set("model.temperature", 0.5)
        assert cm.get("model.temperature") == 0.5