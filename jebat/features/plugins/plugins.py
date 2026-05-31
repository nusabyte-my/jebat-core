"""JEBAT Plugin System — Dynamic feature loading at runtime.

Load third-party JEBAT plugins from:
  - ~/.jebat/plugins/ (local directory)
  - pip packages (jebat-plugin-*)
  - Git repos (clone + load)

Plugin structure:
  jebat_plugin_example/
    __init__.py        # Must export: JEBAT_PLUGIN_META, JEBAT_PLUGIN_TOOLS
    plugin.py          # Plugin implementation

Plugin manifest (in __init__.py):
  JEBAT_PLUGIN_META = {
      "name": "example",
      "version": "0.1.0",
      "description": "Example JEBAT plugin",
      "author": "humm1ngb1rd",
      "tools": ["example_tool"],  # Tool names this plugin provides
  }

This is the TukangPlugin — modular extensions without core changes.
"""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from jebat.tools import register_tool

PLUGIN_DIR = os.path.expanduser("~/.jebat/plugins")
PIP_PREFIX = "jebat-plugin-"


@dataclass(slots=True)
class PluginMeta:
    """Plugin metadata from manifest."""
    name: str = ""
    version: str = "0.0.0"
    description: str = ""
    author: str = ""
    tools: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    source: str = ""  # local, pip, git


@dataclass(slots=True)
class PluginStatus:
    """Current status of a loaded plugin."""
    name: str = ""
    loaded: bool = False
    error: str = ""
    tools_registered: int = 0
    source: str = ""


# ── Plugin Discovery ──────────────────────────────────────────────────────

def discover_local_plugins() -> list[str]:
    """Discover plugins in ~/.jebat/plugins/ directory.

    Returns:
        List of plugin directory names
    """
    if not os.path.exists(PLUGIN_DIR):
        return []

    plugins = []
    for item in os.listdir(PLUGIN_DIR):
        plugin_path = os.path.join(PLUGIN_DIR, item)
        init_path = os.path.join(plugin_path, "__init__.py")
        if os.path.isdir(plugin_path) and os.path.exists(init_path):
            plugins.append(item)

    return sorted(plugins)


def discover_pip_plugins() -> list[str]:
    """Discover installed pip packages with jebat-plugin-* prefix.

    Returns:
        List of pip package names
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            return []

        packages = json.loads(result.stdout)
        return [
            pkg["name"] for pkg in packages
            if pkg["name"].startswith(PIP_PREFIX)
        ]
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        return []


# ── Plugin Loading ────────────────────────────────────────────────────────

def load_plugin(name: str, source: str = "local") -> PluginStatus:
    """Load a plugin and register its tools.

    Args:
        name: Plugin name
        source: Where to load from (local, pip, git)

    Returns:
        PluginStatus with load result
    """
    try:
        if source == "local":
            # Add plugin directory to sys.path temporarily
            plugin_path = os.path.join(PLUGIN_DIR, name)
            if not os.path.exists(plugin_path):
                return PluginStatus(name=name, error=f"Plugin directory not found: {plugin_path}")

            if plugin_path not in sys.path:
                sys.path.insert(0, plugin_path)

            module = importlib.import_module(name)

        elif source == "pip":
            # Import pip-installed package
            module = importlib.import_module(name.replace("-", "_"))

        else:
            return PluginStatus(name=name, error=f"Unknown source: {source}")

        # Check for plugin manifest
        meta = getattr(module, "JEBAT_PLUGIN_META", None)
        tools_dict = getattr(module, "JEBAT_PLUGIN_TOOLS", None)

        if meta is None:
            return PluginStatus(name=name, error="Plugin missing JEBAT_PLUGIN_META in __init__.py")

        if tools_dict is None:
            return PluginStatus(name=name, error="Plugin missing JEBAT_PLUGIN_TOOLS in __init__.py")

        # Register tools with JEBAT's tool registry
        registered_count = _register_plugin_tools(name, tools_dict)

        # Track as loaded
        if name not in _loaded_plugins:
            _loaded_plugins.append(name)

        return PluginStatus(
            name=name,
            loaded=True,
            tools_registered=registered_count,
            source=source,
        )

    except Exception as e:
        return PluginStatus(name=name, error=f"Load failed: {e}")


def _register_plugin_tools(plugin_name: str, tools_dict: dict[str, Any]) -> int:
    """Register plugin tools with JEBAT's global tool registry.

    Args:
        plugin_name: Plugin name for namespace
        tools_dict: Dict of tool_name → {description, handler, parameters}

    Returns:
        Number of tools registered
    """
    # Try to import JEBAT's tool registry
    try:
        from jebat.core.agent_loop import TOOL_REGISTRY
    except ImportError:
        # Registry not available yet — store locally
        global _PLUGIN_TOOL_REGISTRY
        for tool_name, tool_info in tools_dict.items():
            namespaced_name = f"plugin_{plugin_name}_{tool_name}"
            _PLUGIN_TOOL_REGISTRY[namespaced_name] = tool_info
        return len(tools_dict)

    # Register with namespace prefix
    for tool_name, tool_info in tools_dict.items():
        namespaced_name = f"plugin_{plugin_name}_{tool_name}"
        TOOL_REGISTRY[namespaced_name] = {
            "description": f"[{plugin_name}] {tool_info.get('description', '')}",
            "handler": tool_info.get("handler"),
            "parameters": tool_info.get("parameters", {}),
            "safety": tool_info.get("safety", "auto"),
            "plugin": plugin_name,
        }

    return len(tools_dict)


# Plugin tools stored when JEBAT registry isn't available yet
_PLUGIN_TOOL_REGISTRY: dict[str, Any] = {}

# Track loaded plugin names for plugin_list
_loaded_plugins: list[str] = []


def list_loaded() -> list[str]:
    """Return names of currently loaded plugins."""
    return list(_loaded_plugins)


def load_all_plugins() -> list[PluginStatus]:
    """Discover and load all available plugins.

    Returns:
        List of PluginStatus for each discovered plugin
    """
    statuses: list[PluginStatus] = []

    # Load local plugins
    for name in discover_local_plugins():
        status = load_plugin(name, source="local")
        statuses.append(status)

    # Load pip plugins
    for name in discover_pip_plugins():
        status = load_plugin(name, source="pip")
        statuses.append(status)

    return statuses


# ── Plugin Installation ───────────────────────────────────────────────────

def install_from_git(repo_url: str, name: str | None = None) -> PluginStatus:
    """Install a plugin from a Git repository.

    Args:
        repo_url: Git repository URL
        name: Plugin name (default: derived from repo URL)

    Returns:
        PluginStatus after installation and loading
    """
    if name is None:
        # Derive name from URL
        name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        if name.startswith(PIP_PREFIX):
            name = name[len(PIP_PREFIX):]

    plugin_path = os.path.join(PLUGIN_DIR, name)

    if os.path.exists(plugin_path):
        # Update existing plugin
        try:
            subprocess.run(
                ["git", "pull"],
                cwd=plugin_path, capture_output=True, timeout=30,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
    else:
        # Clone new plugin
        try:
            subprocess.run(
                ["git", "clone", repo_url, plugin_path],
                capture_output=True, timeout=60,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return PluginStatus(name=name, error=f"Git clone failed: {e}")

    # Load the installed plugin
    return load_plugin(name, source="local")


def install_from_pip(package: str) -> PluginStatus:
    """Install a plugin from pip.

    Args:
        package: pip package name (e.g. 'jebat-plugin-example')

    Returns:
        PluginStatus after installation and loading
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            return PluginStatus(
                name=package, error=f"pip install failed: {result.stderr[:500]}"
            )
    except subprocess.TimeoutExpired:
        return PluginStatus(name=package, error="pip install timed out")

    # Derive plugin name
    name = package.replace(PIP_PREFIX, "").replace("-", "_")

    # Load the installed plugin
    return load_plugin(name, source="pip")


def uninstall_plugin(name: str, source: str = "local") -> dict[str, str]:
    """Uninstall a plugin.

    Args:
        name: Plugin name
        source: Where the plugin was installed from (local, pip)

    Returns:
        Dict with status message
    """
    if source == "local":
        plugin_path = os.path.join(PLUGIN_DIR, name)
        if os.path.exists(plugin_path):
            import shutil
            shutil.rmtree(plugin_path)
            return {"status": "removed", "path": plugin_path}
        return {"status": "not_found", "path": plugin_path}

    elif source == "pip":
        package_name = PIP_PREFIX + name
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", "-y", package_name],
                capture_output=True, text=True, timeout=30,
            )
            return {"status": "uninstalled", "package": package_name}
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "pip uninstall timed out"}

    return {"status": "error", "message": f"Unknown source: {source}"}


# ── Plugin Tools Registry ─────────────────────────────────────────────────

PLUGIN_SYSTEM_TOOLS: dict[str, dict[str, Any]] = {
    "discover_plugins": {
        "description": "Discover available JEBAT plugins (local + pip)",
        "safety": "auto",
        "handler": lambda: {"local": discover_local_plugins(), "pip": discover_pip_plugins()},
        "parameters": {},
    },
    "load_plugin": {
        "description": "Load a plugin and register its tools",
        "safety": "confirm",
        "handler": load_plugin,
        "parameters": {
            "name": {"type": "string", "description": "Plugin name"},
            "source": {"type": "string", "description": "local, pip, or git"},
        },
    },
    "load_all_plugins": {
        "description": "Discover and load all available plugins",
        "safety": "confirm",
        "handler": load_all_plugins,
        "parameters": {},
    },
    "install_from_git": {
        "description": "Install a plugin from a Git repository",
        "safety": "confirm",
        "handler": install_from_git,
        "parameters": {
            "repo_url": {"type": "string", "description": "Git repo URL"},
            "name": {"type": "string", "description": "Plugin name (optional)"},
        },
    },
    "install_from_pip": {
        "description": "Install a plugin from pip",
        "safety": "confirm",
        "handler": install_from_pip,
        "parameters": {"package": {"type": "string", "description": "pip package name"}},
    },
    "uninstall_plugin": {
        "description": "Uninstall a plugin",
        "safety": "confirm",
        "handler": uninstall_plugin,
        "parameters": {
            "name": {"type": "string"},
            "source": {"type": "string", "default": "local"},
        },
    },
}


def list_plugin_tools() -> list[dict[str, str]]:
    """List all plugin system tools."""
    return [
        {"name": name, "description": info["description"], "safety": info["safety"]}
        for name, info in PLUGIN_SYSTEM_TOOLS.items()
    ]


# ── Registered Tools (for JEBAT tool dispatch) ─────────────────────────────

def _discover_all() -> dict[str, list[str]]:
    """Discover both local and pip plugins."""
    return {"local": discover_local_plugins(), "pip": discover_pip_plugins()}


register_tool(
    name="plugin_discover",
    handler=_discover_all,
    description="Scan for available JEBAT plugins (local ~/.jebat/plugins/ directory + pip packages with jebat-plugin-* prefix)",
    schema={},
)

register_tool(
    name="plugin_load",
    handler=load_plugin,
    description="Load a specific JEBAT plugin by name and register its tools",
    schema={
        "name": {"type": "string", "description": "Plugin name to load"},
        "source": {"type": "string", "description": "Source: local, pip, or git (default: local)"},
    },
)

register_tool(
    name="plugin_list",
    handler=list_loaded,
    description="List currently loaded JEBAT plugins",
    schema={},
)