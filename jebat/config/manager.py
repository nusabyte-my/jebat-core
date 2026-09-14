"""Three-layer YAML configuration manager."""

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

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        if not path.is_file():
            return {}
        with path.open() as handle:
            return yaml.safe_load(handle) or {}

    def _load_env(self, path: Path) -> dict[str, Any]:
        values: dict[str, str] = {}
        if not path.is_file():
            return {}
        with path.open() as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    values[key.strip()] = value.strip()

        nested: dict[str, Any] = {}
        for key, value in values.items():
            parts = key.lower().split("_")
            current: dict[str, Any] = nested
            for part in parts[:-1]:
                child = current.setdefault(part, {})
                if not isinstance(child, dict):
                    child = {}
                    current[part] = child
                current = child
            current[parts[-1]] = value
        return nested

    def _save(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config_path.open("w") as handle:
            yaml.safe_dump(self._data, handle)

    def _load_all(self) -> None:
        data: dict[str, Any] = {}
        _deep_update(data, self._load_yaml(self.config_path))
        _deep_update(data, self._load_env(self.env_path))
        _deep_update(data, self._load_yaml(self.project_path))
        self._data = data

    def _validate(self) -> None:
        try:
            jsonschema.validate(instance=self._data, schema=DEFAULT_SCHEMA)
        except jsonschema.ValidationError as exc:
            raise ValueError(f"Configuration validation error: {exc.message}") from exc

    def get(self, key: str, default: Any = None) -> Any:
        current: Any = self._data
        for part in key.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current

    def set(self, key: str, value: Any) -> None:
        current: dict[str, Any] = self._data
        parts = key.split(".")
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
        self._validate()
        self._save()

    def edit(self) -> None:
        with tempfile.NamedTemporaryFile("w+", suffix=".yaml", delete=False) as handle:
            yaml.safe_dump(self._data, handle)
            handle.flush()
            editor = os.environ.get("EDITOR", "notepad")
            subprocess.call([editor, handle.name])
            handle.seek(0)
            self._data = yaml.safe_load(handle) or {}
            self._validate()
            self._save()
        os.unlink(handle.name)

    def validate(self) -> None:
        self._validate()
        print("Configuration is valid.")

    def reset(self) -> None:
        self._data = self._load_yaml(self.config_path) if self.config_path.is_file() else {}
        self._save()


def _deep_update(base: dict[str, Any], overlay: dict[str, Any]) -> None:
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_update(base[key], value)
        else:
            base[key] = value
