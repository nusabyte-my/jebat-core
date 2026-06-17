"""
Config command — Configuration management for JEBAT.
"""

from __future__ import annotations

from typing import Any


def config_command(args: Any) -> int:
    """Manage JEBAT configuration."""
    from jebat.config.unified import (
        config_cli_show,
        config_cli_set,
        config_cli_reset,
        ensure_config,
        get_settings,
    )

    # Ensure config is loaded
    ensure_config()

    # Determine subcommand
    subcommand = getattr(args, "config_command", None)

    if subcommand == "show":
        config_cli_show()
        return 0

    elif subcommand == "set":
        key = getattr(args, "key", None)
        value = getattr(args, "value", None)
        if not key or value is None:
            print("Usage: jebat config set <key> <value>")
            print("Example: jebat config set agent.safety_mode confirm")
            return 1
        config_cli_set(key, value)
        return 0

    elif subcommand == "reset":
        config_cli_reset()
        return 0

    elif subcommand == "edit":
        import os
        import subprocess
        import tempfile
        from pathlib import Path

        settings = get_settings()
        config_path = settings.get_config_path()

        if not config_path.exists():
            from jebat.config.unified import create_default_config
            config_path = create_default_config()

        with tempfile.NamedTemporaryFile("w+", suffix=".yaml", delete=False) as tf:
            with open(config_path, "r", encoding="utf-8") as f:
                tf.write(f.read())
            tf.flush()
            editor = os.environ.get("EDITOR", "notepad")
            subprocess.call([editor, tf.name])
            tf.seek(0)
            new_content = tf.read()
            try:
                import yaml
                yaml.safe_load(new_content)  # Validate YAML
                Path(config_path).write_text(new_content, encoding="utf-8")
                print(f"Configuration saved to {config_path}")
            except yaml.YAMLError as e:
                print(f"Invalid YAML: {e}")
                return 1
            finally:
                os.unlink(tf.name)
        return 0

    elif subcommand == "path":
        settings = get_settings()
        print(settings.get_config_path())
        return 0

    elif subcommand == "init":
        from jebat.config.unified import create_default_config
        path = create_default_config(getattr(args, "file", None))
        print(f"Created default configuration at {path}")
        return 0

    else:
        print("Usage: jebat config {show|set|reset|edit|path|init}")
        print()
        print("Commands:")
        print("  show     Show current configuration")
        print("  set      Set a configuration value (dot notation)")
        print("  reset    Reset configuration to defaults")
        print("  edit     Open configuration in $EDITOR")
        print("  path     Show configuration file path")
        print("  init     Create default configuration file")
        return 1


__all__ = ["config_command"]