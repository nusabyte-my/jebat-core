"""Configuration manager with three-layer YAML support.

Layering (later overrides earlier):
  1. Defaults: ~/.jebat/config.yaml
  2. Secrets:  ~/.jebat/.env (or .jebat/secrets.env)
  3. Project:  .jebatrc

Provides get/set with dot-notation, validate, edit, reset.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import jsonschema
import yaml

DEFAULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "model": {
            "type": "object",
            "properties": {
                "provider": {"type": "string"},
                "model": {"type": "string"},
                "temperature": {"type": "number"},
            },
        },
    },
    "additionalProperties": True,
}


class ConfigManager:
    def __init__(
        self,
        config_path: str = "~/.jebat/config.yaml",
        env_path: str = "~/.jebat/.env",
        project_path: str = ".jebatrc",
    ) -> None:
        self.config_path = Path(config_path).expanduser()
        self.env_path = Path(env_path).expanduser()
        self.project_path = Path(project_path)
        self._data: dict[str, Any] = {}
        self._load_all()
        self._validate()

    # ── IO helpers ────────────────────────────────────────────────
    def _load_yaml(self, path: Path) -> dict[str, Any]:
        if not path.is_file():
            return {}
        with path.open() as f:
            return yaml.safe_load(f) or {}

    def _load_env(self, path: Path) -> dict[str, Any]:
        env: dict[str, str] = {}
        if not path.is_file():
            return {}
        with path.open() as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
        # Flat env keys like MODEL_PROVIDER → model.provider
        nested: dict[str, Any] = {}
        for k, v in env.items():
            parts = k.lower().split("_")
            d: dict[str, Any] = nested
            for p in parts[:-1]:
                d = d.setdefault(p, {})
                if not isinstance(d, dict):
                    d = {}
            d[parts[-1]] = v
        return nested

    def _save(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config_path.open("w") as f:
            yaml.safe_dump(self._data, f)

    # ── Layer resolution ──────────────────────────────────────────
    def _load_all(self) -> None:
        # Layers: defaults → env → project (last wins)
        data: dict[str, Any] = {}
        _deep_update(data, self._load_yaml(self.config_path))
        _deep_update(data, self._load_env(self.env_path))
        _deep_update(data, self._load_yaml(self.project_path))
        self._data = data

    def _validate(self) -> None:
        try:
            jsonschema.validate(instance=self._data, schema=DEFAULT_SCHEMA)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Configuration validation error: {e.message}") from e

    # ── Public API ────────────────────────────────────────────────
    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value with dot-notation."""
        cur: Any = self._data
        for part in key.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return default
        return cur

    def set(self, key: str, value: Any) -> None:
        """Set a config value with dot-notation, validate, and persist."""
        cur: dict[str, Any] = self._data
        parts = key.split(".")
        for p in parts[:-1]:
            if p not in cur or not isinstance(cur[p], dict):
                cur[p] = {}
            cur = cur[p]
        cur[parts[-1]] = value
        self._validate()
        self._save()

    def edit(self) -> None:
        """Open config in $EDITOR (or notepad on Windows)."""
        with tempfile.NamedTemporaryFile(
            "w+", suffix=".yaml", delete=False
        ) as tf:
            yaml.safe_dump(self._data, tf)
            tf.flush()
            editor = os.environ.get("EDITOR", "notepad")
            subprocess.call([editor, tf.name])
            tf.seek(0)
            new_data = yaml.safe_load(tf) or {}
            self._data = new_data
            self._validate()
            self._save()
            os.unlink(tf.name)

    def validate(self) -> None:
        """Validate the current configuration and print result."""
        self._validate()
        print("Configuration is valid.")

    def reset(self) -> None:
        """Restore to defaults-only (ignore env/project)."""
        if self.config_path.is_file():
            self._data = self._load_yaml(self.config_path)
        else:
            self._data = {}
        self._save()


def _deep_update(base: dict, overlay: dict) -> None:
    """Recursively update base with overlay (mutates base in place)."""
    for k, v in overlay.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_update(base[k], v)
        else:
            base[k] = v