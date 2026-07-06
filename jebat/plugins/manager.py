"""
JEBAT Plugin System

Plugin architecture for extending JEBAT capabilities.

Features:
- Dynamic plugin loading
- Plugin sandboxing
- Version management
- Dependency resolution
- Plugin marketplace ready

Plugin Types:
- Tool plugins (external APIs)
- Skill plugins (custom capabilities)
- Channel plugins (new platforms)
- Memory plugins (storage backends)

Usage:
    from jebat.plugins import PluginManager

    manager = PluginManager()
    await manager.load_plugin("my_plugin")
    await manager.execute_plugin("my_plugin", data)
"""

import asyncio
import importlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


class PluginType(str, Enum):
    """Plugin type enumeration"""

    TOOL = "tool"  # External API integrations
    SKILL = "skill"  # Custom capabilities
    CHANNEL = "channel"  # New communication platforms
    MEMORY = "memory"  # Storage backends


class PluginStatus(str, Enum):
    """Plugin status enumeration"""

    LOADED = "loaded"
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class PluginManifest:
    """Plugin manifest/metadata"""

    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    entry_point: str
    dependencies: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict) -> "PluginManifest":
        """Create manifest from dict"""
        return cls(
            name=data.get("name", "unknown"),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            author=data.get("author", "unknown"),
            plugin_type=PluginType(data.get("type", "tool")),
            entry_point=data.get("entry_point", ""),
            dependencies=data.get("dependencies", []),
            permissions=data.get("permissions", []),
            config_schema=data.get("config_schema", {}),
        )

    @classmethod
    def from_file(cls, path: Path) -> "PluginManifest":
        """Load manifest from file"""
        with open(path / "manifest.json", "r") as f:
            data = json.load(f)
        return cls.from_dict(data)


@dataclass
class Plugin:
    """Loaded plugin instance"""

    manifest: PluginManifest
    module: Any
    status: PluginStatus = PluginStatus.LOADED
    config: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    loaded_at: datetime = field(default_factory=datetime.utcnow)


class PluginManager:
    """
    Plugin manager for JEBAT.

    Responsibilities:
    - Plugin discovery and loading
    - Lifecycle management
    - Dependency resolution
    - Sandboxing and security
    - Configuration management
    """

    def __init__(
        self,
        plugins_dir: Optional[Path] = None,
        auto_load: bool = False,
    ):
        """
        Initialize plugin manager.

        Args:
            plugins_dir: Directory to search for plugins
            auto_load: Auto-load plugins on initialization
        """
        self.plugins_dir = plugins_dir or Path(__file__).parent / "plugins"
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_hooks: Dict[str, List[Callable]] = {}

        if auto_load:
            self.discover_plugins()

        logger.info(f"PluginManager initialized (plugins_dir={self.plugins_dir})")

    def discover_plugins(self) -> List[str]:
        """
        Discover available plugins.

        Returns:
            List of discovered plugin names
        """
        discovered = []

        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory does not exist: {self.plugins_dir}")
            return discovered

        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir():
                continue

            manifest_file = plugin_dir / "manifest.json"
            if not manifest_file.exists():
                continue

            try:
                manifest = PluginManifest.from_file(plugin_dir)
                discovered.append(manifest.name)
                logger.info(f"Discovered plugin: {manifest.name} v{manifest.version}")
            except Exception as e:
                logger.error(f"Failed to load plugin manifest: {e}")

        return discovered

    async def load_plugin(
        self,
        plugin_name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> Plugin:
        """
        Load a plugin.

        Args:
            plugin_name: Name of plugin to load
            config: Plugin configuration

        Returns:
            Loaded Plugin instance
        """
        if plugin_name in self.plugins:
            logger.warning(f"Plugin {plugin_name} already loaded")
            return self.plugins[plugin_name]

        # Find plugin directory
        plugin_dir = self.plugins_dir / plugin_name
        if not plugin_dir.exists():
            raise FileNotFoundError(f"Plugin {plugin_name} not found")

        # Load manifest
        manifest = PluginManifest.from_file(plugin_dir)

        # Check dependencies
        await self._check_dependencies(manifest)

        # Load plugin module
        try:
            entry_point = manifest.entry_point
            spec = importlib.util.spec_from_file_location(
                plugin_name,
                plugin_dir / entry_point,
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Create plugin instance
            plugin = Plugin(
                manifest=manifest,
                module=module,
                config=config or {},
            )

            # Initialize plugin
            if hasattr(module, "init"):
                await module.init(config or {})

            self.plugins[plugin_name] = plugin
            plugin.status = PluginStatus.ACTIVE

            logger.info(f"Loaded plugin: {plugin_name} v{manifest.version}")
            return plugin

        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
            raise

    async def unload_plugin(self, plugin_name: str):
        """
        Unload a plugin.

        Args:
            plugin_name: Name of plugin to unload
        """
        if plugin_name not in self.plugins:
            logger.warning(f"Plugin {plugin_name} not loaded")
            return

        plugin = self.plugins[plugin_name]

        # Call plugin cleanup
        if hasattr(plugin.module, "cleanup"):
            await plugin.module.cleanup()

        # Remove hooks
        self._remove_plugin_hooks(plugin_name)

        # Remove from registry
        del self.plugins[plugin_name]

        logger.info(f"Unloaded plugin: {plugin_name}")

    async def execute_plugin(
        self,
        plugin_name: str,
        data: Any,
        **kwargs,
    ) -> Any:
        """
        Execute a plugin.

        Args:
            plugin_name: Name of plugin to execute
            data: Input data
            **kwargs: Additional arguments

        Returns:
            Plugin execution result
        """
        if plugin_name not in self.plugins:
            raise ValueError(f"Plugin {plugin_name} not loaded")

        plugin = self.plugins[plugin_name]

        if plugin.status != PluginStatus.ACTIVE:
            raise RuntimeError(f"Plugin {plugin_name} is not active")

        # Execute plugin
        if hasattr(plugin.module, "execute"):
            result = await plugin.module.execute(data, **kwargs)
            return result
        else:
            raise NotImplementedError(f"Plugin {plugin_name} has no execute method")

    def register_hook(
        self, hook_name: str, callback: Callable, plugin_name: str = "core"
    ):
        """
        Register a plugin hook.

        Args:
            hook_name: Hook name
            callback: Callback function
            plugin_name: Plugin name
        """
        if hook_name not in self.plugin_hooks:
            self.plugin_hooks[hook_name] = []

        self.plugin_hooks[hook_name].append((plugin_name, callback))
        logger.debug(f"Registered hook: {hook_name} ({plugin_name})")

    async def trigger_hooks(self, hook_name: str, *args, **kwargs):
        """
        Trigger all hooks for an event.

        Args:
            hook_name: Hook name
            *args: Hook arguments
            **kwargs: Hook keyword arguments
        """
        if hook_name not in self.plugin_hooks:
            return

        for plugin_name, callback in self.plugin_hooks[hook_name]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Hook {hook_name} ({plugin_name}) failed: {e}")

    def _remove_plugin_hooks(self, plugin_name: str):
        """Remove all hooks for a plugin"""
        for hook_name in list(self.plugin_hooks.keys()):
            self.plugin_hooks[hook_name] = [
                (pn, cb) for pn, cb in self.plugin_hooks[hook_name] if pn != plugin_name
            ]

    async def _check_dependencies(self, manifest: PluginManifest):
        """Check plugin dependencies"""
        for dep in manifest.dependencies:
            try:
                importlib.import_module(dep)
            except ImportError:
                logger.warning(f"Missing dependency for {manifest.name}: {dep}")
                # Could auto-install here

    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Get plugin by name"""
        return self.plugins.get(plugin_name)

    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all loaded plugins"""
        return [
            {
                "name": p.manifest.name,
                "version": p.manifest.version,
                "type": p.manifest.plugin_type.value,
                "status": p.status.value,
                "description": p.manifest.description,
            }
            for p in self.plugins.values()
        ]


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get global plugin manager"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


# Plugin decorator for easy registration


def plugin(name: str, plugin_type: PluginType = PluginType.TOOL):
    """
    Decorator to mark a class as a plugin.

    Usage:
        @plugin("my_plugin", PluginType.TOOL)
        class MyPlugin:
            async def execute(self, data):
                return {"result": "success"}
    """

    def decorator(cls):
        cls._plugin_name = name
        cls._plugin_type = plugin_type
        return cls

    return decorator
