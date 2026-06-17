"""
File command — File system operations for JEBAT.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from jebat.features.fileops.file_ops import (
    file_read,
    file_write,
    file_patch,
    file_search,
    file_undo,
    file_tree,
)


async def _run_read(args: Any) -> int:
    result = await file_read(args.path, args.offset, args.limit)
    if "error" in result:
        print(f"Error: {result['error']}")
        return 1
    for line in result["lines"]:
        print(line)
    print(f"\nTotal lines: {result['total_lines']}, Showing: {result['showing']}")
    return 0


async def _run_write(args: Any) -> int:
    content = args.content
    if args.file:
        content = Path(args.file).read_text(encoding="utf-8")
    result = await file_write(args.path, content, args.force)
    if "error" in result:
        print(f"Error: {result['error']}")
        return 1
    print(f"{result['action'].capitalize()} {result['path']} ({result['bytes']} bytes, {result['lines']} lines)")
    if "diff" in result:
        print(f"\nDiff:\n{result['diff']}")
    return 0


async def _run_patch(args: Any) -> int:
    result = await file_patch(args.path, args.old_string, args.new_string, args.replace_all)
    if "error" in result:
        print(f"Error: {result['error']}")
        if "count" in result:
            print(f"Found {result['count']} occurrences")
        return 1
    print(f"Replaced {result['replaced']} occurrence(s) in {result['path']}")
    return 0


async def _run_search(args: Any) -> int:
    result = await file_search(args.pattern, args.path, args.file_glob, args.target, args.limit)
    if "error" in result:
        print(f"Error: {result['error']}")
        return 1
    for line in result["matches"]:
        print(line)
    print(f"\nTotal matches: {result['count']}")
    return 0


async def _run_undo(args: Any) -> int:
    result = await file_undo(args.path)
    if "error" in result:
        print(f"Error: {result['error']}")
        return 1
    print(f"Restored {result['path']} from {result['restored_from']}")
    print(f"Available backups: {result['available_backups']}")
    return 0


async def _run_tree(args: Any) -> int:
    result = await file_tree(args.path, args.depth, args.gitignore)
    if "error" in result:
        print(f"Error: {result['error']}")
        return 1
    print(result["tree"])
    return 0


async def _run_tool(args: Any, tool_name: str, func) -> int:
    """Run a file operation tool."""
    from jebat.tools import call_tool
    try:
        if tool_name == "file_read":
            result = await call_tool("file_read", path=args.path, offset=args.offset, limit=args.limit)
        elif tool_name == "file_write":
            content = args.content
            if args.file:
                content = Path(args.file).read_text(encoding="utf-8")
            result = await call_tool("file_write", path=args.path, content=content, force=args.force)
        elif tool_name == "file_patch":
            result = await call_tool("file_patch", path=args.path, old_string=args.old_string, new_string=args.new_string, replace_all=args.replace_all)
        elif tool_name == "file_search":
            result = await call_tool("file_search", pattern=args.pattern, path=args.path, file_glob=args.file_glob, target=args.target, limit=args.limit)
        elif tool_name == "file_undo":
            result = await call_tool("file_undo", path=args.path)
        elif tool_name == "file_tree":
            result = await call_tool("file_tree", path=args.path, depth=args.depth, gitignore=args.gitignore)
        else:
            print(f"Unknown tool: {tool_name}")
            return 1

        if "error" in result:
            print(f"Error: {result['error']}")
            return 1

        if tool_name == "file_read":
            for line in result["lines"]:
                print(line)
            print(f"\nTotal lines: {result['total_lines']}, Showing: {result['showing']}")
        elif tool_name == "file_write":
            print(f"{result['action'].capitalize()} {result['path']} ({result['bytes']} bytes, {result['lines']} lines)")
            if "diff" in result:
                print(f"\nDiff:\n{result['diff']}")
        elif tool_name == "file_patch":
            print(f"Replaced {result['replaced']} occurrence(s) in {result['path']}")
        elif tool_name == "file_search":
            for line in result["matches"]:
                print(line)
            print(f"\nTotal matches: {result['count']}")
        elif tool_name == "file_undo":
            print(f"Restored {result['path']} from {result['restored_from']}")
            print(f"Available backups: {result['available_backups']}")
        elif tool_name == "file_tree":
            print(result["tree"])

        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def file_command(args: Any) -> int:
    """File system operations."""
    import asyncio
    from jebat.tools import TOOL_REGISTRY

    # Ensure tools are loaded
    from jebat.core.agent_runtime import ToolDispatcher
    dispatcher = ToolDispatcher(None, None)
    dispatcher.ensure_tools_loaded()

    subcommand = getattr(args, "file_command", None)

    if subcommand == "read":
        return asyncio.run(_run_tool(args, "file_read", file_read))

    elif subcommand == "write":
        content = args.content
        if args.file:
            content = Path(args.file).read_text(encoding="utf-8")
        return asyncio.run(_run_tool(args, "file_write", file_write))

    elif subcommand == "patch":
        return asyncio.run(_run_tool(args, "file_patch", file_patch))

    elif subcommand == "search":
        return asyncio.run(_run_tool(args, "file_search", file_search))

    elif subcommand == "undo":
        return asyncio.run(_run_tool(args, "file_undo", file_undo))

    elif subcommand == "tree":
        return asyncio.run(_run_tool(args, "file_tree", file_tree))

    else:
        print("Usage: jebat file {read|write|patch|search|undo|tree} [args...]")
        print()
        print("Commands:")
        print("  read     Read a file with line numbers")
        print("  write    Write content to a file (overwrites)")
        print("  patch    Find and replace text in a file")
        print("  search   Search file contents or find files by name")
        print("  undo     Restore a file from backup")
        print("  tree     Show directory tree")
        return 1


__all__ = ["file_command"]