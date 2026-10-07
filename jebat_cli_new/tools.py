"""
JEBAT — tool definitions for the agent loop.
Native tools: read_file, write_file, search_files, terminal, list_dir.
"""

from __future__ import annotations

import json, os, subprocess, time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field, ValidationError


# ─── Atomic Agents Pydantic Schemas ──────────────────────────────

class ReadFileInput(BaseModel):
    path: str = Field(..., description="Absolute or relative file path")
    offset: int = Field(default=1, ge=1, description="Start line (1-indexed)")
    limit: int = Field(default=200, ge=1, le=2000, description="Max lines to return")


class WriteFileInput(BaseModel):
    path: str = Field(..., description="File path to write")
    content: str = Field(..., description="Full file content")


class SearchFilesInput(BaseModel):
    pattern: str = Field(..., description="Glob or regex pattern")
    path: str = Field(default=".", description="Directory to search in")
    target: str = Field(default="files", description="Target: 'files' or 'content'")
    file_glob: str = Field(default="", description="Filter files by extension")
    limit: int = Field(default=50, ge=1, le=500, description="Max results")


class TerminalInput(BaseModel):
    command: str = Field(..., description="Shell command to execute")
    timeout: int = Field(default=120, ge=1, le=600, description="Max seconds")
    workdir: Optional[str] = Field(default=None, description="Working directory")


class ListDirInput(BaseModel):
    path: str = Field(default=".", description="Directory path")
    pattern: str = Field(default="*", description="Glob filter pattern")


TOOL_SCHEMAS: Dict[str, type[BaseModel]] = {
    "read_file": ReadFileInput,
    "write_file": WriteFileInput,
    "search_files": SearchFilesInput,
    "terminal": TerminalInput,
    "list_dir": ListDirInput,
}


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
    path = args.get("path") or args.get("filename") or ""
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


def _lsp_path(args):
    from pathlib import Path as _P
    raw = args.get("path") or ""
    return _P(raw).expanduser() if raw else None


def handle_lsp_definition(args):
    from jebat_cli_new import lsp
    path = _lsp_path(args)
    if not path or not path.exists():
        return f"Error: file not found: {args.get('path')}"
    client, err = lsp.get_client(path)
    if not client:
        return f"Error: {err}"
    res = client.definition(path, int(args.get("line", 1)), int(args.get("column", 1)))
    return lsp.format_locations(res)


def handle_lsp_references(args):
    from jebat_cli_new import lsp
    path = _lsp_path(args)
    if not path or not path.exists():
        return f"Error: file not found: {args.get('path')}"
    client, err = lsp.get_client(path)
    if not client:
        return f"Error: {err}"
    res = client.references(path, int(args.get("line", 1)), int(args.get("column", 1)))
    return lsp.format_locations(res)


def handle_lsp_hover(args):
    from jebat_cli_new import lsp
    path = _lsp_path(args)
    if not path or not path.exists():
        return f"Error: file not found: {args.get('path')}"
    client, err = lsp.get_client(path)
    if not client:
        return f"Error: {err}"
    res = client.hover(path, int(args.get("line", 1)), int(args.get("column", 1)))
    if not res or not res.get("contents"):
        return "no result"
    contents = res["contents"]
    return contents if isinstance(contents, str) else contents.get("value", str(contents))


def handle_lsp_diagnostics(args):
    from jebat_cli_new import lsp
    path = _lsp_path(args)
    if not path or not path.exists():
        return f"Error: file not found: {args.get('path')}"
    client, err = lsp.get_client(path)
    if not client:
        return f"Error: {err}"
    diags = client.diagnostics(path)
    if not diags:
        return "no diagnostics"
    sev = {1: "error", 2: "warning", 3: "info", 4: "hint"}
    out = []
    for d in diags[:40]:
        rng = (d.get("range") or {}).get("start", {})
        out.append(f"  {sev.get(d.get('severity'), '?')} "
                   f"{rng.get('line', 0) + 1}:{rng.get('character', 0) + 1} "
                   f"{d.get('message', '')}")
    return "\n".join(out)


HANDLERS: Dict[str, Callable[[Dict[str, Any]], str]] = {
    "read_file": handle_read_file,
    "write_file": handle_write_file,
    "search_files": handle_search_files,
    "terminal": handle_terminal,
    "list_dir": handle_list_dir,
    "lsp_definition": handle_lsp_definition,
    "lsp_references": handle_lsp_references,
    "lsp_hover": handle_lsp_hover,
    "lsp_diagnostics": handle_lsp_diagnostics,
}


_LSP_PARAMS = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "File path"},
        "line": {"type": "integer", "description": "1-indexed line", "default": 1},
        "column": {"type": "integer", "description": "1-indexed column", "default": 1},
    },
    "required": ["path"],
}

TOOL_DEFINITIONS.extend([
    {
        "name": "lsp_definition",
        "description": "Find where the symbol at a position is defined (language server).",
        "parameters": _LSP_PARAMS,
    },
    {
        "name": "lsp_references",
        "description": "Find all references to the symbol at a position (language server).",
        "parameters": _LSP_PARAMS,
    },
    {
        "name": "lsp_hover",
        "description": "Get type/documentation info for the symbol at a position.",
        "parameters": _LSP_PARAMS,
    },
    {
        "name": "lsp_diagnostics",
        "description": "Report errors and warnings for a file from its language server.",
        "parameters": {"type": "object", "properties": {"path": _LSP_PARAMS["properties"]["path"]},
                       "required": ["path"]},
    },
])


def _add_shared_registry_tools() -> None:
    """Expose shared registry definitions without replacing native CLI tools."""
    from jebat_cli_new.tool_bridge import shared_tool_definitions

    existing = {definition["name"] for definition in TOOL_DEFINITIONS}
    for definition in shared_tool_definitions():
        name = definition["name"]
        if name not in existing:
            TOOL_DEFINITIONS.append(definition)


_add_shared_registry_tools()


def _preview_write_card(path: str, content: str, width: int = 78) -> str:
    """Build a preview card for an impending file write."""
    from jebat_cli_new.theme import C, render_diff

    p = Path(path)
    if p.exists():
        try:
            old = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            old = ""
        card = render_diff(old, content, path, width=width)
        verb = "OVERWRITE"
    else:
        lines = content.splitlines()
        shown = "\n".join(lines[:14])
        more = f"\n… +{len(lines) - 14} more lines" if len(lines) > 14 else ""
        card = f"{C.CYAN}new file{C.RESET} {path}\n{C.DIM}{'─' * 60}{C.RESET}\n{shown}{more}"
        verb = "CREATE"
    return f"{C.BOLD}[{verb}]{C.RESET} {card}"


_ALWAYS_APPROVED: set = set()


def prompt_tool_approval(tool: str, preview: str) -> str:
    """Ask once / always / no for a tool call. Returns 'yes'|'always'|'no'."""
    from jebat_cli_new.theme import cprint, C

    cprint(f"\n╭─ ⚒ {tool} wants to act {C.DIM}(y = once, a = always this session, n = no){C.RESET}", C.YELLOW)
    print(preview)
    try:
        ans = input("╰─ allow? [y/a/n]: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print()
        return "no"
    if ans in ("a", "always"):
        _ALWAYS_APPROVED.add(tool)
        return "always"
    return "yes" if ans in ("y", "yes", "") else "no"


def execute_tool(name: str, arguments: Dict[str, Any], yolo: bool = False) -> str:
    """Execute a tool with optional safety checks.
    
    Args:
        name: Tool name
        arguments: Tool arguments
        yolo: If True, skip safety confirmations
    """
    if name not in HANDLERS:
        from jebat_cli_new import extensions as ext

        if ext.has_tool(name):
            return ext.run_tool(name, arguments)
        from jebat_cli_new.tool_bridge import execute_shared_tool

        return execute_shared_tool(name, arguments, yolo=yolo)

    handler = HANDLERS.get(name)
    if not handler:
        return f"Unknown tool: {name}"

    from jebat_cli_new import extensions as _ext

    arguments = _ext.before_tool(name, arguments)

    # Atomic Agents-style schema validation
    if name in TOOL_SCHEMAS:
        schema_cls = TOOL_SCHEMAS[name]
        try:
            validated = schema_cls(**arguments)
            arguments = validated.model_dump(exclude_unset=False)
        except ValidationError as err:
            err_msgs = [f"{e['loc'][0]}: {e['msg']}" for e in err.errors()]
            return f"[TOOL_SCHEMA_ERROR for {name}]: Invalid parameters ({'; '.join(err_msgs)}). Please fix arguments to match schema and retry."
    
    # Safety checks for dangerous operations
    if not yolo:
        from jebat_cli_new.safety import is_dangerous_command, is_dangerous_file, confirm_action, classify_command_action

        if name == "terminal":
            cmd = arguments.get("command", "")
            dangerous, reason = is_dangerous_command(cmd)
            if dangerous:
                if not confirm_action(f"Dangerous command detected: {reason}", f"Command: {cmd}"):
                    return f"Command blocked by safety: {reason}"
            # Staged approval (claude-code style): read-only commands run free;
            # write/execute commands confirm once per stage per session.
            stage = classify_command_action(cmd)
            if stage and not _stage_approved(stage):
                if not confirm_action(
                    f"[staged:{stage}] first {stage} command this session", f"Command: {cmd}"
                ):
                    return f"Command blocked by safety: staged approval denied for '{stage}'"
            _remember_stage(stage, cmd)
        
        if name == "write_file":
            path = arguments.get("path", "")
            dangerous, reason = is_dangerous_file(path)
            if dangerous:
                if not confirm_action(f"Dangerous file modification: {reason}", f"File: {path}"):
                    return f"File write blocked by safety: {reason}"
            # Preview card + always-allow (kilocode style). yolo or a prior
            # 'always' for this tool skips the prompt entirely.
            if "write_file" not in _ALWAYS_APPROVED:
                preview = _preview_write_card(path, arguments.get("content", ""))
                verdict = prompt_tool_approval("write_file", preview)
                if verdict == "no":
                    return "File write blocked by user (preview declined)"
    
    return _ext.after_tool(name, arguments, handler(arguments))
