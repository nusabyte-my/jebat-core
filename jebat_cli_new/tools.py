"""
JEBAT — tool definitions for the agent loop.
Native tools: read_file, write_file, search_files, terminal, list_dir.
"""

from __future__ import annotations

import json, os, subprocess, time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ToolDef:
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable[[Dict[str, Any]], str]


TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "read_file",
        "description": "Read a file from disk. Returns content with line numbers.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute or relative file path"},
                "offset": {"type": "integer", "description": "Start line (1-indexed)", "default": 1},
                "limit": {"type": "integer", "description": "Max lines to return", "default": 200},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file, creating parent dirs if needed. Overwrites existing content.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Full file content"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "search_files",
        "description": "Search for files by glob pattern or grep inside file contents.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob or regex pattern"},
                "path": {"type": "string", "description": "Directory to search in", "default": "."},
                "target": {"type": "string", "enum": ["files", "content"], "default": "files"},
                "file_glob": {"type": "string", "description": "Filter files by extension"},
                "limit": {"type": "integer", "default": 50},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "terminal",
        "description": "Execute a shell command. Returns stdout, stderr, and exit code.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
                "timeout": {"type": "integer", "description": "Max seconds", "default": 120},
                "workdir": {"type": "string", "description": "Working directory"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "list_dir",
        "description": "List directory contents with file sizes and modification times.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path", "default": "."},
                "pattern": {"type": "string", "description": "Glob filter pattern"},
            },
        },
    },
]


def handle_read_file(args: Dict[str, Any]) -> str:
    path = args.get("path", "")
    offset = args.get("offset", 1)
    limit = args.get("limit", 200)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        total = len(lines)
        start = max(0, offset - 1)
        end = min(total, start + limit)
        out = []
        for i, line in enumerate(lines[start:end], start=start + 1):
            out.append(f"{i:6d} | {line.rstrip()}")
        result = "\n".join(out)
        if end < total:
            result += f"\n... ({total - end} more lines)"
        return result
    except Exception as e:
        return f"Error reading {path}: {e}"


def handle_write_file(args: Dict[str, Any]) -> str:
    path = args.get("path", "")
    content = args.get("content", "")
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Written {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error writing {path}: {e}"


def handle_search_files(args: Dict[str, Any]) -> str:
    import fnmatch
    pattern = args.get("pattern", "")
    search_path = args.get("path", ".")
    target = args.get("target", "files")
    file_glob = args.get("file_glob", "")
    limit = args.get("limit", 50)

    if target == "files":
        matches = []
        for root, dirs, files in os.walk(search_path):
            for f in files:
                if file_glob and not fnmatch.fnmatch(f, file_glob):
                    continue
                if fnmatch.fnmatch(f, pattern) or pattern in f:
                    matches.append(os.path.join(root, f))
                if len(matches) >= limit:
                    return "\n".join(matches)
        return "\n".join(matches) if matches else "No files found"
    else:
        # content search (grep-like)
        import re
        matches = []
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            regex = re.compile(re.escape(pattern), re.IGNORECASE)

        for root, dirs, files in os.walk(search_path):
            for f in files:
                if file_glob and not fnmatch.fnmatch(f, file_glob):
                    continue
                fp = os.path.join(root, f)
                try:
                    with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                        for i, line in enumerate(fh, 1):
                            if regex.search(line):
                                matches.append(f"{fp}:{i}: {line.rstrip()}")
                                if len(matches) >= limit:
                                    return "\n".join(matches)
                except Exception:
                    continue
        return "\n".join(matches) if matches else "No matches found"


def handle_terminal(args: Dict[str, Any]) -> str:
    cmd = args.get("command", "")
    timeout = args.get("timeout", 120)
    workdir = args.get("workdir") or None
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=workdir,
        )
        out = ""
        if result.stdout:
            out += result.stdout
        if result.stderr:
            out += f"\nSTDERR:\n{result.stderr}" if out else result.stderr
        out += f"\n[exit {result.returncode}]"
        return out.strip()
    except subprocess.TimeoutExpired:
        return f"Timeout after {timeout}s"
    except Exception as e:
        return f"Error: {e}"


def handle_list_dir(args: Dict[str, Any]) -> str:
    import fnmatch
    path = args.get("path", ".")
    pattern = args.get("pattern", "*")
    try:
        entries = []
        for entry in sorted(os.listdir(path)):
            if not fnmatch.fnmatch(entry, pattern):
                continue
            full = os.path.join(path, entry)
            is_dir = os.path.isdir(full)
            try:
                size = os.path.getsize(full) if not is_dir else 0
                mt = os.path.getmtime(full)
            except Exception:
                size = 0
                mt = 0
            kind = "d" if is_dir else "f"
            size_str = f"{size:>10,}" if not is_dir else "       dir"
            entries.append(f"  {kind} {size_str}  {entry}")
        return "\n".join(entries) if entries else "Empty directory"
    except Exception as e:
        return f"Error listing {path}: {e}"


HANDLERS: Dict[str, Callable[[Dict[str, Any]], str]] = {
    "read_file": handle_read_file,
    "write_file": handle_write_file,
    "search_files": handle_search_files,
    "terminal": handle_terminal,
    "list_dir": handle_list_dir,
}


def execute_tool(name: str, arguments: Dict[str, Any], yolo: bool = False) -> str:
    """Execute a tool with optional safety checks.
    
    Args:
        name: Tool name
        arguments: Tool arguments
        yolo: If True, skip safety confirmations
    """
    handler = HANDLERS.get(name)
    if not handler:
        return f"Unknown tool: {name}"
    
    # Safety checks for dangerous operations
    if not yolo:
        from jebat_cli_new.safety import is_dangerous_command, is_dangerous_file, confirm_action
        
        if name == "terminal":
            cmd = arguments.get("command", "")
            dangerous, reason = is_dangerous_command(cmd)
            if dangerous:
                if not confirm_action(f"Dangerous command detected: {reason}", f"Command: {cmd}"):
                    return f"Command blocked by safety: {reason}"
        
        if name == "write_file":
            path = arguments.get("path", "")
            dangerous, reason = is_dangerous_file(path)
            if dangerous:
                if not confirm_action(f"Dangerous file modification: {reason}", f"File: {path}"):
                    return f"File write blocked by safety: {reason}"
    
    return handler(arguments)
