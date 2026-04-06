"""
Configuration Package
Contains configuration management components for the Multi-Agent Automation System.

This package provides:
- ConfigManager: Centralized configuration management system
- ConfigFormat: Supported configuration file formats
- ConfigScope: Configuration scope levels
- Schema validation and configuration merging utilities

Usage:
    from config import ConfigManager, ConfigFormat, ConfigScope
    from config.config_manager import ConfigManager

    # Create configuration manager
    config_manager = ConfigManager(config_directory="./configs")

    # Load and save configurations
    config_manager.save_config("agent", "my_agent", config_data)
    config = config_manager.get_config("agent", "my_agent")
"""

__version__ = "1.0.0"

# Import main components
from .config_manager import ConfigFormat, ConfigManager, ConfigSchema, ConfigScope

# Define what gets imported with "from config import *"
__all__ = [
    "ConfigManager",
    "ConfigFormat",
    "ConfigScope",
    "ConfigSchema",
]

# Default configuration templates
DEFAULT_CONFIGS = {
    "global": {
        "system": {
            "name": "Multi-Agent System",
            "version": "1.0.0",
            "environment": "development",
        },
        "logging": {
            "level": "INFO",
            "file_enabled": True,
            "console_enabled": True,
            "log_directory": "./logs",
        },
        "performance": {
            "max_workers": 4,
            "timeout_default": 30,
            "memory_limit_mb": 1024,
            "enable_metrics": True,
        },
        "security": {
            "enable_encryption": False,
            "api_key_rotation": False,
            "secure_communications": True,
        },
    },
    "agent": {
        "agent_id": "agent_001",
        "name": "Sample Agent",
        "description": "A sample agent configuration",
        "max_concurrent_tasks": 3,
        "timeout": 60,
        "retry_attempts": 3,
        "enabled": True,
        "skills": [],
        "resources": {"cpu_limit": 1.0, "memory_limit_mb": 512},
    },
    "skill": {
        "skill_id": "skill_001",
        "name": "Sample Skill",
        "type": "utility",
        "description": "A sample skill configuration",
        "version": "1.0.0",
        "enabled": True,
        "dependencies": [],
        "parameters": {},
        "resources": {"memory_limit_mb": 256, "execution_timeout": 30},
    },
}


def create_config_manager(config_directory: str = "./config", **kwargs):
    """
    Factory function to create a ConfigManager with default settings.

    Args:
        config_directory: Directory for configuration files
        **kwargs: Additional configuration parameters

    Returns:
        ConfigManager instance

    Example:
        config_manager = create_config_manager("./my_configs", auto_reload=True)
    """
    return ConfigManager(config_directory=config_directory, **kwargs)


def get_default_config(config_type: str):
    """
    Get default configuration template for a given type.

    Args:
        config_type: Type of configuration ("global", "agent", "skill")

    Returns:
        Dictionary containing default configuration

    Raises:
        ValueError: If config_type is not available

    Example:
        default_agent_config = get_default_config("agent")
    """
    if config_type not in DEFAULT_CONFIGS:
        available_types = list(DEFAULT_CONFIGS.keys())
        raise ValueError(
            f"Unknown config type '{config_type}'. Available types: {available_types}"
        )

    return DEFAULT_CONFIGS[config_type].copy()


def list_config_types():
    """
    List all available default configuration types.

    Returns:
        List of available configuration type names
    """
    return list(DEFAULT_CONFIGS.keys())


def get_config_templates():
    """
    Get all available configuration templates.

    Returns:
        Dictionary mapping config types to their default templates
    """
    return {
        config_type: template.copy()
        for config_type, template in DEFAULT_CONFIGS.items()
    }


def validate_config_structure(config_data: dict, config_type: str):
    """
    Basic validation of configuration structure against templates.

    Args:
        config_data: Configuration data to validate
        config_type: Type of configuration to validate against

    Returns:
        Tuple of (is_valid: bool, errors: list)

    Example:
        is_valid, errors = validate_config_structure(my_config, "agent")
    """
    errors = []

    if config_type not in DEFAULT_CONFIGS:
        errors.append(f"Unknown configuration type: {config_type}")
        return False, errors

    template = DEFAULT_CONFIGS[config_type]

    # Check for required fields based on template
    for key, value in template.items():
        if isinstance(value, dict):
            if key not in config_data:
                errors.append(f"Missing required section: {key}")
            elif not isinstance(config_data[key], dict):
                errors.append(f"Section '{key}' must be a dictionary")
        else:
            if key not in config_data:
                # Only report missing keys for non-dict template values that seem required
                if key in ["agent_id", "skill_id", "name", "type"]:
                    errors.append(f"Missing required field: {key}")

    return len(errors) == 0, errors


def merge_with_defaults(config_data: dict, config_type: str):
    """
    Merge configuration data with default template values.

    Args:
        config_data: User configuration data
        config_type: Type of configuration

    Returns:
        Merged configuration dictionary

    Example:
        full_config = merge_with_defaults(partial_config, "agent")
    """
    if config_type not in DEFAULT_CONFIGS:
        return config_data.copy()

    def deep_merge(base, override):
        """Recursively merge dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    template = DEFAULT_CONFIGS[config_type]
    return deep_merge(template, config_data)


# Configuration utilities
class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""

    pass


def setup_default_configs(config_manager: ConfigManager, overwrite: bool = False):
    """
    Setup default configurations using a ConfigManager instance.

    Args:
        config_manager: ConfigManager instance to use
        overwrite: Whether to overwrite existing configurations

    Returns:
        Dictionary of setup results for each config type

    Example:
        results = setup_default_configs(my_config_manager)
    """
    results = {}

    for config_type, default_config in DEFAULT_CONFIGS.items():
        try:
            # Check if config already exists
            existing_config = config_manager.get_config(config_type, "default")

            if existing_config and not overwrite:
                results[config_type] = {"status": "skipped", "reason": "already exists"}
                continue

            # Save default configuration
            success = config_manager.save_config(
                config_type, "default", default_config, format_type=ConfigFormat.JSON
            )

            if success:
                results[config_type] = {"status": "created", "config": default_config}
            else:
                results[config_type] = {"status": "failed", "reason": "save failed"}

        except Exception as e:
            results[config_type] = {"status": "error", "reason": str(e)}

    return results
