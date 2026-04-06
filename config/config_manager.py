"""
Configuration Manager
Centralized configuration management system for agents and skills.
Handles loading, validation, merging, and persistence of configurations.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml


class ConfigFormat(Enum):
    """Supported configuration file formats"""

    JSON = "json"
    YAML = "yaml"
    YML = "yml"


class ConfigScope(Enum):
    """Configuration scope levels"""

    GLOBAL = "global"
    AGENT = "agent"
    SKILL = "skill"
    PROJECT = "project"


@dataclass
class ConfigSchema:
    """Schema definition for configuration validation"""

    required_fields: List[str] = field(default_factory=list)
    optional_fields: Dict[str, Any] = field(default_factory=dict)
    field_types: Dict[str, type] = field(default_factory=dict)
    validation_rules: Dict[str, callable] = field(default_factory=dict)
    nested_schemas: Dict[str, "ConfigSchema"] = field(default_factory=dict)


class ConfigManager:
    """
    Centralized configuration management system.
    Provides loading, validation, merging, and persistence of configurations
    across different scopes (global, agent, skill, project).
    """

    def __init__(
        self,
        config_directory: str = "./config",
        auto_reload: bool = False,
        validation_enabled: bool = True,
        backup_enabled: bool = True,
    ):
        """
        Initialize the Configuration Manager.

        Args:
            config_directory: Base directory for configuration files
            auto_reload: Whether to automatically reload configs on file changes
            validation_enabled: Whether to validate configurations against schemas
            backup_enabled: Whether to create backups before saving
        """
        self.config_directory = Path(config_directory)
        self.auto_reload = auto_reload
        self.validation_enabled = validation_enabled
        self.backup_enabled = backup_enabled

        # Create config directory if it doesn't exist
        self.config_directory.mkdir(parents=True, exist_ok=True)

        # Storage for configurations
        self.configurations: Dict[str, Dict[str, Any]] = {}
        self.schemas: Dict[str, ConfigSchema] = {}
        self.file_watchers: Dict[str, float] = {}  # file -> last_modified

        # Setup logging
        self.logger = self._setup_logging()

        # Initialize default configurations and schemas
        self._initialize_defaults()

        # Load existing configurations
        self._load_all_configurations()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the configuration manager"""
        logger = logging.getLogger("config_manager")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "[ConfigManager] %(asctime)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _initialize_defaults(self):
        """Initialize default configurations and schemas"""
        # Global configuration schema
        global_schema = ConfigSchema(
            required_fields=["system"],
            optional_fields={
                "logging": {
                    "level": "INFO",
                    "file_enabled": True,
                    "console_enabled": True,
                },
                "performance": {
                    "max_workers": 4,
                    "timeout_default": 30,
                    "memory_limit_mb": 1024,
                },
                "security": {
                    "enable_encryption": False,
                    "api_key_rotation": False,
                },
            },
            field_types={
                "system": dict,
                "logging": dict,
                "performance": dict,
                "security": dict,
            },
        )

        # Agent configuration schema
        agent_schema = ConfigSchema(
            required_fields=["agent_id", "name"],
            optional_fields={
                "description": "",
                "max_concurrent_tasks": 5,
                "timeout": 60,
                "retry_attempts": 3,
                "enabled": True,
                "skills": [],
                "resources": {
                    "cpu_limit": 1.0,
                    "memory_limit_mb": 512,
                },
            },
            field_types={
                "agent_id": str,
                "name": str,
                "description": str,
                "max_concurrent_tasks": int,
                "timeout": (int, float),
                "retry_attempts": int,
                "enabled": bool,
                "skills": list,
                "resources": dict,
            },
        )

        # Skill configuration schema
        skill_schema = ConfigSchema(
            required_fields=["skill_id", "name", "type"],
            optional_fields={
                "description": "",
                "version": "1.0.0",
                "enabled": True,
                "dependencies": [],
                "parameters": {},
                "resources": {
                    "memory_limit_mb": 256,
                    "execution_timeout": 30,
                },
            },
            field_types={
                "skill_id": str,
                "name": str,
                "type": str,
                "description": str,
                "version": str,
                "enabled": bool,
                "dependencies": list,
                "parameters": dict,
                "resources": dict,
            },
        )

        # Register schemas
        self.register_schema("global", global_schema)
        self.register_schema("agent", agent_schema)
        self.register_schema("skill", skill_schema)

        # Default global configuration
        default_global_config = {
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
        }

        self.set_config("global", "default", default_global_config)

    def register_schema(self, config_type: str, schema: ConfigSchema):
        """
        Register a configuration schema for validation.

        Args:
            config_type: Type of configuration (global, agent, skill, etc.)
            schema: Schema definition
        """
        self.schemas[config_type] = schema
        self.logger.info(f"Registered schema for config type: {config_type}")

    def load_config(
        self,
        config_type: str,
        config_name: str,
        file_path: Optional[str] = None,
        format_type: Optional[ConfigFormat] = None,
    ) -> Dict[str, Any]:
        """
        Load configuration from file.

        Args:
            config_type: Type of configuration
            config_name: Name of the configuration
            file_path: Custom file path (optional)
            format_type: File format override

        Returns:
            Loaded configuration dictionary

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If configuration is invalid
        """
        if file_path:
            config_file = Path(file_path)
        else:
            # Determine file path based on type and name
            config_file = self._get_config_file_path(
                config_type, config_name, format_type
            )

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        try:
            # Detect format if not specified
            if not format_type:
                format_type = self._detect_format(config_file)

            # Load configuration based on format
            if format_type in [ConfigFormat.YAML, ConfigFormat.YML]:
                with open(config_file, "r", encoding="utf-8") as f:
                    config_data = yaml.safe_load(f) or {}
            elif format_type == ConfigFormat.JSON:
                with open(config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            else:
                raise ValueError(f"Unsupported configuration format: {format_type}")

            # Validate configuration
            if self.validation_enabled and config_type in self.schemas:
                self._validate_config(config_data, self.schemas[config_type])

            # Store configuration
            self.set_config(config_type, config_name, config_data)

            # Track file for auto-reload
            if self.auto_reload:
                self.file_watchers[str(config_file)] = config_file.stat().st_mtime

            self.logger.info(f"Loaded configuration: {config_type}/{config_name}")
            return config_data

        except Exception as e:
            self.logger.error(
                f"Failed to load configuration {config_type}/{config_name}: {str(e)}"
            )
            raise

    def save_config(
        self,
        config_type: str,
        config_name: str,
        config_data: Optional[Dict[str, Any]] = None,
        file_path: Optional[str] = None,
        format_type: ConfigFormat = ConfigFormat.JSON,
    ) -> bool:
        """
        Save configuration to file.

        Args:
            config_type: Type of configuration
            config_name: Name of the configuration
            config_data: Configuration data (uses stored config if None)
            file_path: Custom file path (optional)
            format_type: File format to save as

        Returns:
            True if save successful

        Raises:
            ValueError: If configuration doesn't exist or is invalid
        """
        try:
            # Use provided data or get from storage
            if config_data is None:
                config_data = self.get_config(config_type, config_name)
                if not config_data:
                    raise ValueError(
                        f"Configuration {config_type}/{config_name} not found"
                    )

            # Validate before saving
            if self.validation_enabled and config_type in self.schemas:
                self._validate_config(config_data, self.schemas[config_type])

            # Determine file path
            if file_path:
                config_file = Path(file_path)
            else:
                config_file = self._get_config_file_path(
                    config_type, config_name, format_type
                )

            # Create parent directories
            config_file.parent.mkdir(parents=True, exist_ok=True)

            # Create backup if enabled
            if self.backup_enabled and config_file.exists():
                self._create_backup(config_file)

            # Save based on format
            if format_type in [ConfigFormat.YAML, ConfigFormat.YML]:
                with open(config_file, "w", encoding="utf-8") as f:
                    yaml.dump(config_data, f, default_flow_style=False, indent=2)
            elif format_type == ConfigFormat.JSON:
                with open(config_file, "w", encoding="utf-8") as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"Unsupported save format: {format_type}")

            self.logger.info(f"Saved configuration: {config_type}/{config_name}")
            return True

        except Exception as e:
            self.logger.error(
                f"Failed to save configuration {config_type}/{config_name}: {str(e)}"
            )
            return False

    def get_config(
        self,
        config_type: str,
        config_name: str,
        default: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get configuration from memory.

        Args:
            config_type: Type of configuration
            config_name: Name of the configuration
            default: Default value if configuration not found

        Returns:
            Configuration dictionary or default
        """
        key = f"{config_type}.{config_name}"
        return self.configurations.get(key, default)

    def set_config(
        self,
        config_type: str,
        config_name: str,
        config_data: Dict[str, Any],
        validate: bool = True,
    ) -> bool:
        """
        Set configuration in memory.

        Args:
            config_type: Type of configuration
            config_name: Name of the configuration
            config_data: Configuration data
            validate: Whether to validate the configuration

        Returns:
            True if set successful
        """
        try:
            # Validate if enabled and schema exists
            if validate and self.validation_enabled and config_type in self.schemas:
                self._validate_config(config_data, self.schemas[config_type])

            key = f"{config_type}.{config_name}"
            self.configurations[key] = config_data.copy()

            self.logger.debug(f"Set configuration: {key}")
            return True

        except Exception as e:
            self.logger.error(
                f"Failed to set configuration {config_type}/{config_name}: {str(e)}"
            )
            return False

    def merge_configs(
        self,
        base_config: Dict[str, Any],
        override_config: Dict[str, Any],
        deep_merge: bool = True,
    ) -> Dict[str, Any]:
        """
        Merge two configuration dictionaries.

        Args:
            base_config: Base configuration
            override_config: Override configuration
            deep_merge: Whether to perform deep merge

        Returns:
            Merged configuration
        """
        if not deep_merge:
            merged = base_config.copy()
            merged.update(override_config)
            return merged

        def _deep_merge(
            base: Dict[str, Any], override: Dict[str, Any]
        ) -> Dict[str, Any]:
            result = base.copy()
            for key, value in override.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = _deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        return _deep_merge(base_config, override_config)

    def get_merged_config(
        self,
        config_type: str,
        config_name: str,
        include_global: bool = True,
    ) -> Dict[str, Any]:
        """
        Get configuration merged with global settings.

        Args:
            config_type: Type of configuration
            config_name: Name of the configuration
            include_global: Whether to include global configuration

        Returns:
            Merged configuration dictionary
        """
        config = self.get_config(config_type, config_name, {})

        if include_global and config_type != "global":
            global_config = self.get_config("global", "default", {})
            if global_config:
                config = self.merge_configs(global_config, config)

        return config

    def list_configs(
        self,
        config_type: Optional[str] = None,
    ) -> Dict[str, List[str]]:
        """
        List all available configurations.

        Args:
            config_type: Filter by configuration type (optional)

        Returns:
            Dictionary mapping config types to config names
        """
        result = {}

        for key in self.configurations.keys():
            parts = key.split(".", 1)
            if len(parts) == 2:
                ctype, cname = parts
                if config_type is None or ctype == config_type:
                    if ctype not in result:
                        result[ctype] = []
                    result[ctype].append(cname)

        return result

    def delete_config(
        self,
        config_type: str,
        config_name: str,
        delete_file: bool = False,
    ) -> bool:
        """
        Delete configuration from memory and optionally from file.

        Args:
            config_type: Type of configuration
            config_name: Name of the configuration
            delete_file: Whether to delete the file as well

        Returns:
            True if deletion successful
        """
        try:
            key = f"{config_type}.{config_name}"

            # Remove from memory
            if key in self.configurations:
                del self.configurations[key]
                self.logger.info(f"Deleted configuration from memory: {key}")

            # Delete file if requested
            if delete_file:
                config_file = self._get_config_file_path(config_type, config_name)
                if config_file.exists():
                    if self.backup_enabled:
                        self._create_backup(config_file)
                    config_file.unlink()
                    self.logger.info(f"Deleted configuration file: {config_file}")

            return True

        except Exception as e:
            self.logger.error(
                f"Failed to delete configuration {config_type}/{config_name}: {str(e)}"
            )
            return False

    def reload_all(self):
        """Reload all configurations from files"""
        self.logger.info("Reloading all configurations...")
        self.configurations.clear()
        self._load_all_configurations()

    def check_for_updates(self) -> List[str]:
        """
        Check for configuration file updates (if auto-reload is enabled).

        Returns:
            List of updated configuration keys
        """
        updated = []

        if not self.auto_reload:
            return updated

        for file_path, last_modified in self.file_watchers.items():
            config_file = Path(file_path)
            if config_file.exists():
                current_modified = config_file.stat().st_mtime
                if current_modified > last_modified:
                    # File has been modified, reload it
                    try:
                        config_type, config_name = self._parse_config_path(config_file)
                        self.load_config(config_type, config_name, file_path)
                        self.file_watchers[file_path] = current_modified
                        updated.append(f"{config_type}.{config_name}")
                    except Exception as e:
                        self.logger.error(f"Failed to reload {file_path}: {str(e)}")

        return updated

    def export_all_configs(
        self,
        export_path: str,
        format_type: ConfigFormat = ConfigFormat.JSON,
    ) -> bool:
        """
        Export all configurations to a single file.

        Args:
            export_path: Path to export file
            format_type: Export format

        Returns:
            True if export successful
        """
        try:
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "configurations": self.configurations.copy(),
                "schemas": {
                    name: {
                        "required_fields": schema.required_fields,
                        "optional_fields": schema.optional_fields,
                    }
                    for name, schema in self.schemas.items()
                },
            }

            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)

            if format_type in [ConfigFormat.YAML, ConfigFormat.YML]:
                with open(export_file, "w", encoding="utf-8") as f:
                    yaml.dump(export_data, f, default_flow_style=False, indent=2)
            elif format_type == ConfigFormat.JSON:
                with open(export_file, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Exported all configurations to: {export_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export configurations: {str(e)}")
            return False

    def import_configs(
        self,
        import_path: str,
        merge_existing: bool = False,
    ) -> bool:
        """
        Import configurations from a file.

        Args:
            import_path: Path to import file
            merge_existing: Whether to merge with existing configs

        Returns:
            True if import successful
        """
        try:
            import_file = Path(import_path)
            if not import_file.exists():
                raise FileNotFoundError(f"Import file not found: {import_path}")

            # Detect format and load
            format_type = self._detect_format(import_file)

            if format_type in [ConfigFormat.YAML, ConfigFormat.YML]:
                with open(import_file, "r", encoding="utf-8") as f:
                    import_data = yaml.safe_load(f)
            elif format_type == ConfigFormat.JSON:
                with open(import_file, "r", encoding="utf-8") as f:
                    import_data = json.load(f)

            # Import configurations
            imported_configs = import_data.get("configurations", {})
            for key, config_data in imported_configs.items():
                if merge_existing and key in self.configurations:
                    # Merge with existing
                    existing = self.configurations[key]
                    merged = self.merge_configs(existing, config_data)
                    self.configurations[key] = merged
                else:
                    # Replace or add new
                    self.configurations[key] = config_data

            self.logger.info(
                f"Imported {len(imported_configs)} configurations from: {import_path}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to import configurations: {str(e)}")
            return False

    def _validate_config(self, config_data: Dict[str, Any], schema: ConfigSchema):
        """Validate configuration against schema"""
        # Check required fields
        for field in schema.required_fields:
            if field not in config_data:
                raise ValueError(f"Missing required field: {field}")

        # Check field types
        for field, expected_type in schema.field_types.items():
            if field in config_data:
                value = config_data[field]
                if not isinstance(value, expected_type):
                    raise ValueError(
                        f"Field '{field}' must be of type {expected_type.__name__}, got {type(value).__name__}"
                    )

        # Apply validation rules
        for field, validator in schema.validation_rules.items():
            if field in config_data:
                if not validator(config_data[field]):
                    raise ValueError(f"Validation failed for field: {field}")

        # Validate nested schemas
        for field, nested_schema in schema.nested_schemas.items():
            if field in config_data and isinstance(config_data[field], dict):
                self._validate_config(config_data[field], nested_schema)

    def _get_config_file_path(
        self,
        config_type: str,
        config_name: str,
        format_type: Optional[ConfigFormat] = None,
    ) -> Path:
        """Get the file path for a configuration"""
        if format_type is None:
            format_type = ConfigFormat.JSON

        extension = format_type.value
        filename = f"{config_name}.{extension}"

        return self.config_directory / config_type / filename

    def _detect_format(self, file_path: Path) -> ConfigFormat:
        """Detect configuration file format from extension"""
        suffix = file_path.suffix.lower()

        if suffix == ".json":
            return ConfigFormat.JSON
        elif suffix in [".yaml", ".yml"]:
            return ConfigFormat.YAML
        else:
            # Default to JSON
            return ConfigFormat.JSON

    def _parse_config_path(self, file_path: Path) -> Tuple[str, str]:
        """Parse configuration type and name from file path"""
        relative_path = file_path.relative_to(self.config_directory)
        config_type = str(relative_path.parent)
        config_name = file_path.stem  # filename without extension

        return config_type, config_name

    def _load_all_configurations(self):
        """Load all existing configuration files"""
        if not self.config_directory.exists():
            return

        for config_file in self.config_directory.rglob("*"):
            if config_file.is_file() and config_file.suffix.lower() in [
                ".json",
                ".yaml",
                ".yml",
            ]:
                try:
                    config_type, config_name = self._parse_config_path(config_file)
                    self.load_config(config_type, config_name, str(config_file))
                except Exception as e:
                    self.logger.error(f"Failed to load {config_file}: {str(e)}")

    def _create_backup(self, config_file: Path):
        """Create backup of configuration file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{config_file.stem}_{timestamp}{config_file.suffix}"
        backup_path = config_file.parent / "backups" / backup_name

        backup_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, "rb") as src, open(backup_path, "wb") as dst:
            dst.write(src.read())

        self.logger.debug(f"Created backup: {backup_path}")
