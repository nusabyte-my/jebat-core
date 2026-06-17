"""JEBAT Configuration System — three-layer config with validation.

Architecture:
  1. ~/.jebat/config.yaml  — User defaults (committed)
  2. .env / secrets.env     — Secrets (gitignored)
  3. .jebatrc               — Per-project overrides (committed)

Each layer overrides the previous. All keys validated against JSON Schema.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# ── Defaults ──────────────────────────────────────────────────────────────

CONFIG_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "model": {
            "type": "object",
            "properties": {
                "provider": {"type": "string", "default": "openai"},
                "model": {"type": "string", "default": "gpt-4o"},
                "temperature": {"type": "number", "default": 0.2, "minimum": 0, "maximum": 2},
                "max_tokens": {"type": "integer", "default": 4096, "minimum": 1},
            },
        },
        "features": {
            "type": "object",
            "properties": {
                "terminal": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean", "default": True},
                        "timeout": {"type": "integer", "default": 300},
                        "dangerous_commands": {"type": "string", "enum": ["auto", "confirm", "block"], "default": "confirm"},
                    },
                },
                "browser": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean", "default": False},
                        "headless": {"type": "boolean", "default": True},
                    },
                },
                "wiki": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean", "default": True},
                        "dir": {"type": "string", "default": "~/.jebat/wiki"},
                        "max_context_pages": {"type": "integer", "default": 3},
                    },
                },
            },
        },
        "plugins": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "path": {"type": "string"},
                    "enabled": {"type": "boolean", "default": True},
                },
            },
        },
        "logging": {
            "type": "object",
            "properties": {
                "level": {"type": "string", "enum": ["debug", "info", "warn", "error"], "default": "info"},
                "audit": {"type": "boolean", "default": True},
            },
        },
    },
}

def _unpack_defaults(schema: dict[str, Any]) -> dict[str, Any]:
    """Extract default values from a JSON Schema into a flat dict."""
    result: dict[str, Any] = {}
    props = schema.get("properties", {})
    for key, val in props.items():
        if "default" in val:
            result[key] = val["default"]
        elif val.get("type") == "object":
            nested = _unpack_defaults(val)
            if nested:
                result[key] = nested
    return result


DEFAULT_CONFIG: dict[str, Any] = _unpack_defaults(CONFIG_SCHEMA)


# ── Loader ────────────────────────────────────────────────────────────────

@dataclass
class JebatConfig:
    """Merged JEBAT configuration from all layers."""
    data: dict[str, Any] = field(default_factory=lambda: DEFAULT_CONFIG.copy())

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value by dot-separated key, e.g. 'model.provider'."""
        parts = key.split(".")
        cur = self.data
        for part in parts:
            if isinstance(cur, dict):
                cur = cur.get(part)
                if cur is None:
                    return default
            else:
                return default
        return cur

    def set(self, key: str, value: Any) -> None:
        """Set a config value by dot-separated key."""
        parts = key.split(".")
        cur = self.data
        for part in parts[:-1]:
            if part not in cur:
                cur[part] = {}
            cur = cur[part]
        cur[parts[-1]] = value

    def to_dict(self) -> dict[str, Any]:
        return self.data

    def validate(self) -> list[str]:
        """Validate against schema. Returns list of errors (empty = valid)."""
        errors: list[str] = []
        self._validate_node(self.data, CONFIG_SCHEMA, errors, "")
        return errors

    def _validate_node(self, node: Any, schema: dict, errors: list[str], path: str) -> None:
        """Recursive schema validation."""
        if not isinstance(schema, dict):
            return
        schema_type = schema.get("type")

        if schema_type == "object" and isinstance(node, dict):
            props = schema.get("properties", {})
            for key, val_schema in props.items():
                child_path = f"{path}.{key}" if path else key
                if key in node:
                    self._validate_node(node[key], val_schema, errors, child_path)
                elif "default" not in val_schema and "required" in schema.get("required", []):
                    errors.append(f"Missing required: {child_path}")
            # Check for extra keys
            allowed = set(props.keys())
            for key in node:
                if key not in allowed:
                    errors.append(f"Unknown key: {path}.{key}" if path else f"Unknown key: {key}")

        elif schema_type in ("string", "number", "integer", "boolean"):
            expected = {"string": str, "number": (int, float), "integer": int, "boolean": bool}[schema_type]
            if not isinstance(node, expected):
                errors.append(f"{path}: expected {schema_type}, got {type(node).__name__}")
            if schema_type == "string" and "enum" in schema and node not in schema["enum"]:
                errors.append(f"{path}: must be one of {schema['enum']}, got '{node}'")

        elif schema_type == "array" and isinstance(node, list):
            items_schema = schema.get("items", {})
            for i, item in enumerate(node):
                self._validate_node(item, items_schema, errors, f"{path}[{i}]")


def _find_config_files() -> list[Path]:
    """Find config files in order: user global, project-local."""
    files: list[Path] = []

    # 1. User global config
    user_dir = Path.home() / ".jebat"
    user_config = user_dir / "config.yaml"
    if user_config.exists():
        files.append(user_config)

    # 2. Project-local .jebatrc
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        rc = parent / ".jebatrc"
        if rc.exists():
            files.append(rc)
            break

    return files


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _load_dotenv(path: Path | None = None) -> dict[str, str]:
    """Minimal .env loader — no dependency on python-dotenv."""
    env_path = path or Path(".env")
    if not env_path.exists():
        path_candidates = [
            Path.home() / ".jebat" / "secrets.env",
            Path.cwd() / ".env",
        ]
        for p in path_candidates:
            if p.exists():
                env_path = p
                break
        else:
            return {}

    result: dict[str, str] = {}
    try:
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                result[key.strip()] = value.strip().strip("'\"")
    except Exception:
        pass
    return result


def load_config() -> JebatConfig:
    """Load and merge all config layers. Returns a JebatConfig."""
    config = JebatConfig()

    # Layer 1: YAML config files
    for cf in _find_config_files():
        data = _load_yaml(cf)
        _deep_merge(config.data, data)

    # Layer 2: .env secrets
    env = _load_dotenv()
    for key, value in env.items():
        if key.startswith("JEBAT_"):
            # Map JEBAT_LLM_PROVIDER -> model.provider
            mapped = key[6:].lower().replace("_", ".")  # remove JEBAT_ prefix
            config.set(mapped, value)

    # Layer 3: Direct environment overrides
    for env_key, config_key in [
        ("JEBAT_MODEL_PROVIDER", "model.provider"),
        ("JEBAT_MODEL_MODEL", "model.model"),
        ("JEBAT_MODEL_TEMPERATURE", "model.temperature"),
        ("JEBAT_MODEL_MAX_TOKENS", "model.max_tokens"),
    ]:
        val = os.environ.get(env_key)
        if val is not None:
            config.set(config_key, val)

    return config


def save_config(config: JebatConfig, path: Path | None = None) -> None:
    """Save config to a YAML file."""
    target = path or (Path.home() / ".jebat" / "config.yaml")
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        yaml.dump(config.data, f, default_flow_style=False, allow_unicode=True)


def _deep_merge(base: dict, overlay: dict) -> None:
    """Deep merge overlay dict into base dict (mutates base)."""
    for key, value in overlay.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value