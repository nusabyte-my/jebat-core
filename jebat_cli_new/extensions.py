"""Extensions — .py files that add slash commands, tools and hooks.

An extension is any module exposing `register(api)`. Discovery order:

  1. explicit paths from `-e/--extension`
  2. ~/.jebat/extensions/*.py
  3. <cwd>/.jebat/extensions/*.py

The `api` handed to `register()` is deliberately tiny — four verbs:

    api.command("/name", handler, help="...")   handler(arg, ctx) -> str|None
    api.tool("name", handler)                   handler(args) -> str
    api.before_tool(fn)                         fn(name, args) -> args|None
    api.after_tool(fn)                          fn(name, args, result) -> result|None
    api.on_start(fn)                            fn(ctx) -> None

Example ~/.jebat/extensions/hello.py:

    def register(api):
        api.command("/hello", lambda arg, ctx: f"hello {arg or 'world'}",
                    help="Say hello")
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

HOME_DIR = Path.home() / ".jebat" / "extensions"
PROJECT_DIR_NAME = Path(".jebat") / "extensions"

# name -> (handler, help)
COMMANDS: Dict[str, tuple] = {}
# name -> handler
TOOLS: Dict[str, Callable] = {}
_BEFORE: List[Callable] = []
_AFTER: List[Callable] = []
_START: List[Callable] = []
LOADED: List[str] = []
ERRORS: List[str] = []


class ExtensionAPI:
    """The surface an extension's register() receives."""

    def __init__(self, source: str):
        self.source = source

    def command(self, name: str, handler: Callable, help: str = "") -> None:
        if not name.startswith("/"):
            name = "/" + name
        COMMANDS[name] = (handler, help or f"extension: {self.source}")

    def tool(self, name: str, handler: Callable) -> None:
        TOOLS[name] = handler

    def before_tool(self, fn: Callable) -> None:
        _BEFORE.append(fn)

    def after_tool(self, fn: Callable) -> None:
        _AFTER.append(fn)

    def on_start(self, fn: Callable) -> None:
        _START.append(fn)


def _load_file(path: Path) -> None:
    mod_name = f"jebat_ext_{path.stem}"
    try:
        spec = importlib.util.spec_from_file_location(mod_name, path)
        if spec is None or spec.loader is None:
            ERRORS.append(f"{path}: not importable")
            return
        module = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = module
        spec.loader.exec_module(module)
    except Exception as exc:
        ERRORS.append(f"{path}: {type(exc).__name__}: {exc}")
        return

    register = getattr(module, "register", None)
    if not callable(register):
        ERRORS.append(f"{path}: no register(api)")
        return
    try:
        register(ExtensionAPI(path.stem))
    except Exception as exc:
        ERRORS.append(f"{path}: register() raised {type(exc).__name__}: {exc}")
        return
    LOADED.append(str(path))


def discover(explicit: Optional[List[str]] = None, cwd: Optional[Path] = None) -> None:
    """Load every extension found. Safe to call more than once."""
    paths: List[Path] = []
    for raw in explicit or []:
        p = Path(raw).expanduser()
        if p.is_dir():
            paths.extend(sorted(p.glob("*.py")))
        elif p.exists():
            paths.append(p)
        else:
            ERRORS.append(f"{raw}: not found")

    for directory in (HOME_DIR, (cwd or Path.cwd()) / PROJECT_DIR_NAME):
        if directory.is_dir():
            paths.extend(sorted(f for f in directory.glob("*.py")
                                if not f.name.startswith("_")))

    seen = set()
    for path in paths:
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        _load_file(path)


# ── Runtime entry points ────────────────────────────────────────────────────

def has_command(name: str) -> bool:
    return name.lower() in COMMANDS


def run_command(name: str, arg: str, ctx: Any) -> Optional[str]:
    entry = COMMANDS.get(name.lower())
    if not entry:
        return None
    try:
        return entry[0](arg, ctx)
    except Exception as exc:
        return f"extension {name} failed: {type(exc).__name__}: {exc}"


def has_tool(name: str) -> bool:
    return name in TOOLS


def run_tool(name: str, args: Dict[str, Any]) -> str:
    try:
        return str(TOOLS[name](args))
    except Exception as exc:
        return f"Error: extension tool {name}: {type(exc).__name__}: {exc}"


def before_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    for fn in _BEFORE:
        try:
            updated = fn(name, args)
            if isinstance(updated, dict):
                args = updated
        except Exception:
            continue
    return args


def after_tool(name: str, args: Dict[str, Any], result: str) -> str:
    for fn in _AFTER:
        try:
            updated = fn(name, args, result)
            if isinstance(updated, str):
                result = updated
        except Exception:
            continue
    return result


def start(ctx: Any) -> None:
    for fn in _START:
        try:
            fn(ctx)
        except Exception:
            continue


def command_entries() -> List[tuple]:
    """(name, help) pairs for the REPL command list and picker."""
    return [(name, entry[1]) for name, entry in sorted(COMMANDS.items())]


def summary() -> str:
    lines = [f"  {len(LOADED)} extension(s) loaded"]
    for path in LOADED:
        lines.append(f"    {Path(path).name}")
    for err in ERRORS:
        lines.append(f"    ! {err}")
    if COMMANDS:
        lines.append("  commands: " + ", ".join(sorted(COMMANDS)))
    if TOOLS:
        lines.append("  tools: " + ", ".join(sorted(TOOLS)))
    if not LOADED and not ERRORS:
        lines.append(f"  drop .py files in {HOME_DIR}")
    return "\n".join(lines)
