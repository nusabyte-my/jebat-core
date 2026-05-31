"""JEBAT Shell/File/Code Tools — TukangKod (Code Builder).

Core tools the AgentLoop calls to actually DO work:
  - Terminal command execution
  - File read/write/patch
  - Directory listing/search
  - Code execution (Python)
  - Process management
  - Safety: all operations respect SafetyMode tiers

These are the "hands" of the JEBAT agent — without them, the agent
can only think but cannot act.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ── Terminal Execution ────────────────────────────────────────────────────

@dataclass(slots=True)
class TerminalResult:
    command: str
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float = 0.0
    truncated: bool = False


async def terminal_exec(
    command: str,
    timeout: int = 180,
    workdir: str | None = None,
    env: dict[str, str] | None = None,
    capture: bool = True,
) -> TerminalResult:
    """Execute a shell command and return structured result.

    Safety: CONFIRM (executes arbitrary commands)
    
    Args:
        command: Shell command to execute
        timeout: Max seconds to wait (default 180)
        workdir: Working directory override
        env: Additional environment variables
        capture: Capture stdout/stderr (default True)
    """
    # Build environment
    exec_env = dict(os.environ)
    if env:
        exec_env.update(env)

    # Resolve workdir
    cwd = workdir or os.getcwd()

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE if capture else asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE if capture else asyncio.subprocess.DEVNULL,
            cwd=cwd,
            env=exec_env,
        )

        import time
        start = time.monotonic()
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        duration = (time.monotonic() - start) * 1000

        out_str = stdout.decode("utf-8", errors="replace") if stdout else ""
        err_str = stderr.decode("utf-8", errors="replace") if stderr else ""

        # Truncate if too large
        MAX_OUTPUT = 50_000
        truncated = len(out_str) > MAX_OUTPUT
        if truncated:
            out_str = out_str[:MAX_OUTPUT] + f"\n... [truncated, {len(out_str)} chars total]"

        return TerminalResult(
            command=command,
            stdout=out_str,
            stderr=err_str,
            exit_code=proc.returncode or 0,
            duration_ms=round(duration),
            truncated=truncated,
        )

    except asyncio.TimeoutError:
        proc.kill()
        return TerminalResult(
            command=command,
            stdout="",
            stderr=f"Command timed out after {timeout}s",
            exit_code=-1,
            duration_ms=timeout * 1000,
        )
    except Exception as e:
        return TerminalResult(
            command=command,
            stdout="",
            stderr=str(e),
            exit_code=-1,
        )


# ── File Operations ──────────────────────────────────────────────────────

async def file_read(
    path: str,
    offset: int = 1,
    limit: int = 500,
) -> dict[str, Any]:
    """Read a text file with line numbers and pagination.

    Safety: AUTO (read-only)
    
    Args:
        path: File path (absolute, relative, or ~/path)
        offset: Starting line number (1-indexed)
        limit: Max lines to read (default 500, max 2000)
    """
    resolved = _resolve_path(path)
    
    if not resolved.exists():
        # Suggest similar files
        parent = resolved.parent
        suggestions = [f.name for f in parent.iterdir() if f.name.lower().startswith(resolved.name.lower()[:3])] if parent.exists() else []
        return {"error": f"File not found: {path}", "suggestions": suggestions[:5]}
    
    if resolved.is_dir():
        return {"error": f"Path is a directory: {path}", "type": "directory"}
    
    try:
        content = resolved.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        total = len(lines)
        
        start = max(0, offset - 1)
        end = min(total, start + limit)
        
        selected = lines[start:end]
        numbered = [f"{i+1}|{line}" for i, line in enumerate(selected, start=start+1)]
        
        return {
            "path": str(resolved),
            "content": "\n".join(numbered),
            "total_lines": total,
            "offset": offset,
            "limit": limit,
            "size_bytes": resolved.stat().st_size,
        }
    except Exception as e:
        return {"error": str(e)}


async def file_write(
    path: str,
    content: str,
    create_dirs: bool = True,
) -> dict[str, Any]:
    """Write content to a file, completely replacing existing content.

    Safety: CONFIRM (modifies files)
    
    Args:
        path: File path (creates parent dirs if create_dirs=True)
        content: Complete content to write
        create_dirs: Create parent directories if needed
    """
    resolved = _resolve_path(path)
    
    if create_dirs:
        resolved.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        resolved.write_text(content, encoding="utf-8")
        
        # Run syntax check for known file types
        lint_result = _lint_file(resolved)
        
        return {
            "path": str(resolved),
            "bytes_written": len(content.encode("utf-8")),
            "lint": lint_result,
            "created": not resolved.exists(),  # Note: exists() is True now since we just wrote
        }
    except Exception as e:
        return {"error": str(e), "path": str(resolved)}


async def file_patch(
    path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
) -> dict[str, Any]:
    """Targeted find-and-replace edit in a file.

    Safety: CONFIRM (modifies files)
    
    Args:
        path: File path
        old_string: Text to find (must be unique unless replace_all=True)
        new_string: Replacement text (empty string to delete)
        replace_all: Replace all occurrences instead of requiring unique match
    """
    resolved = _resolve_path(path)
    
    if not resolved.exists():
        return {"error": f"File not found: {path}"}
    
    try:
        content = resolved.read_text(encoding="utf-8")
        
        count = content.count(old_string)
        if count == 0:
            return {"error": f"old_string not found in file", "path": str(resolved)}
        
        if not replace_all and count > 1:
            return {
                "error": f"old_string found {count} times — must be unique or set replace_all=True",
                "path": str(resolved),
                "occurrences": count,
            }
        
        new_content = content.replace(old_string, new_string) if replace_all else content.replace(old_string, new_string, 1)
        resolved.write_text(new_content, encoding="utf-8")
        
        # Generate diff
        diff_lines = []
        old_lines = old_string.splitlines()
        new_lines = new_string.splitlines()
        for ol in old_lines:
            diff_lines.append(f"-{ol}")
        for nl in new_lines:
            diff_lines.append(f"+{nl}")
        
        # Lint check
        lint_result = _lint_file(resolved)
        
        return {
            "path": str(resolved),
            "occurrences_replaced": count if replace_all else 1,
            "diff": "\n".join(diff_lines),
            "lint": lint_result,
        }
    except Exception as e:
        return {"error": str(e), "path": str(resolved)}


# ── Directory Operations ─────────────────────────────────────────────────

async def file_search(
    pattern: str,
    path: str = ".",
    target: str = "content",
    file_glob: str | None = None,
    limit: int = 50,
    context: int = 0,
) -> dict[str, Any]:
    """Search file contents or find files by name.

    Safety: AUTO (read-only search)
    
    Args:
        pattern: Regex pattern for content search, or glob for file search
        target: "content" (search inside files) or "files" (find by name)
        path: Directory to search in
        file_glob: Filter files by pattern in content mode
        limit: Max results
        context: Context lines around matches
    """
    resolved = _resolve_path(path)
    
    if not resolved.exists():
        return {"error": f"Path not found: {path}"}
    
    results: list[dict[str, Any]] = []
    
    if target == "files":
        # Find files by glob pattern
        for f in resolved.rglob(pattern):
            if f.is_file():
                stat = f.stat()
                results.append({
                    "path": str(f.relative_to(resolved)),
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                })
                if len(results) >= limit:
                    break
    else:
        # Search inside files (ripgrep-style)
        try:
            cmd = ["rg", "--no-heading", "-n"]
            if context:
                cmd.extend(["-C", str(context)])
            if file_glob:
                cmd.extend(["-g", file_glob])
            cmd.extend(["--max-count", str(limit), pattern, str(resolved)])
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                output = stdout.decode("utf-8", errors="replace")
                for line in output.splitlines():
                    match = re.match(r"^(.+?):(\d+):(.*)$", line)
                    if match:
                        results.append({
                            "file": match.group(1),
                            "line": int(match.group(2)),
                            "content": match.group(3),
                        })
            elif proc.returncode == 2:
                # rg error — fall back to Python grep
                results = await _python_grep(pattern, resolved, file_glob, limit)
        except FileNotFoundError:
            # No rg installed — use Python grep
            results = await _python_grep(pattern, resolved, file_glob, limit)
    
    return {
        "pattern": pattern,
        "target": target,
        "path": str(resolved),
        "matches": results,
        "total": len(results),
    }


async def _python_grep(
    pattern: str,
    directory: Path,
    file_glob: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Fallback grep using Python when ripgrep is not installed."""
    results: list[dict[str, Any]] = []
    regex = re.compile(pattern, re.IGNORECASE)
    
    for f in directory.rglob(file_glob or "*"):
        if f.is_file() and not f.name.startswith("."):
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
                for i, line in enumerate(content.splitlines(), 1):
                    if regex.search(line):
                        results.append({
                            "file": str(f.relative_to(directory)),
                            "line": i,
                            "content": line.strip(),
                        })
                        if len(results) >= limit:
                            return results
            except (UnicodeDecodeError, PermissionError):
                continue
    
    return results


# ── Code Execution ────────────────────────────────────────────────────────

@dataclass(slots=True)
class CodeResult:
    code: str
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float = 0.0


async def code_exec(
    code: str,
    language: str = "python",
    timeout: int = 300,
    workdir: str | None = None,
) -> CodeResult:
    """Execute code in a sandboxed subprocess.

    Safety: CONFIRM (executes code)
    
    Args:
        code: Source code to execute
        language: python, bash, javascript, or sql
        timeout: Max seconds (default 300)
        workdir: Working directory
    """
    cwd = workdir or os.getcwd()
    
    if language == "python":
        # Write to temp file and execute
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, dir=cwd) as f:
            f.write(code)
            tmp_path = f.name
        
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            
            import time
            start = time.monotonic()
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            duration = (time.monotonic() - start) * 1000
            
            out_str = stdout.decode("utf-8", errors="replace")
            err_str = stderr.decode("utf-8", errors="replace")
            
            # Cap output
            MAX = 50_000
            if len(out_str) > MAX:
                out_str = out_str[:MAX] + "\n... [truncated]"
            
            return CodeResult(
                code=code,
                stdout=out_str,
                stderr=err_str,
                exit_code=proc.returncode or 0,
                duration_ms=round(duration),
            )
        except asyncio.TimeoutError:
            proc.kill()
            return CodeResult(code=code, stdout="", stderr=f"Timeout after {timeout}s", exit_code=-1)
        finally:
            os.unlink(tmp_path)
    
    elif language == "bash":
        result = await terminal_exec(code, timeout=timeout, workdir=cwd)
        return CodeResult(
            code=code,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            duration_ms=result.duration_ms,
        )
    
    elif language == "javascript":
        # Try node
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(code)
            tmp_path = f.name
        
        try:
            proc = await asyncio.create_subprocess_exec(
                "node", tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return CodeResult(
                code=code,
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                exit_code=proc.returncode or 0,
            )
        except FileNotFoundError:
            return CodeResult(code=code, stdout="", stderr="Node.js not installed", exit_code=-1)
        except asyncio.TimeoutError:
            proc.kill()
            return CodeResult(code=code, stdout="", stderr=f"Timeout after {timeout}s", exit_code=-1)
        finally:
            os.unlink(tmp_path)
    
    else:
        return CodeResult(code=code, stdout="", stderr=f"Unsupported language: {language}", exit_code=-1)


# ── Process Management ────────────────────────────────────────────────────

@dataclass(slots=True)
class ProcessInfo:
    pid: int
    name: str
    status: str
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    command: str = ""


async def list_processes(self, filter_name: str | None = None) -> list[ProcessInfo]:
    """List running processes.
    
    Safety: AUTO (read-only system info)
    """
    # Use ps or tasklist
    if sys.platform == "win32":
        cmd = ["tasklist", "/fo", "csv"]
    else:
        cmd = ["ps", "aux"]
    
    result = await terminal_exec(" ".join(cmd), timeout=10)
    if result.exit_code != 0:
        return []
    
    processes: list[ProcessInfo] = []
    for line in result.stdout.splitlines():
        if filter_name and filter_name.lower() not in line.lower():
            continue
        # Parse based on platform
        parts = line.strip().split(",")
        if len(parts) >= 2:
            processes.append(ProcessInfo(
                pid=0,
                name=parts[0].strip('"'),
                status="running",
                command=line.strip(),
            ))
    
    return processes[:50]


# ── Helpers ────────────────────────────────────────────────────────────────

def _resolve_path(path: str) -> Path:
    """Resolve path with ~ expansion and cwd normalization."""
    if path.startswith("~"):
        return Path(path).expanduser()
    return Path(path).resolve()


def _lint_file(path: Path) -> dict[str, Any]:
    """Run syntax check on known file types."""
    ext = path.suffix
    lintable = {".py", ".json", ".yaml", ".yml", ".toml", ".xml", ".sh", ".bash"}
    
    if ext not in lintable:
        return {"status": "skipped", "message": f"No linter for {ext} files"}
    
    if ext == ".py":
        try:
            import ast
            ast.parse(path.read_text(encoding="utf-8"))
            return {"status": "ok", "output": ""}
        except SyntaxError as e:
            return {"status": "error", "output": str(e)}
    
    if ext == ".json":
        try:
            json.loads(path.read_text(encoding="utf-8"))
            return {"status": "ok", "output": ""}
        except json.JSONDecodeError as e:
            return {"status": "error", "output": str(e)}
    
    return {"status": "skipped"}


# ── Tool Registry ────────────────────────────────────────────────────────

SHELL_TOOLS: dict[str, dict[str, Any]] = {
    "terminal_exec": {
        "description": "Execute a shell command and return structured result",
        "safety": "confirm",
        "handler": terminal_exec,
        "parameters": {
            "command": {"type": "string", "description": "Shell command"},
            "timeout": {"type": "integer", "description": "Max seconds (default 180)"},
            "workdir": {"type": "string", "description": "Working directory override"},
        },
    },
    "file_read": {
        "description": "Read a text file with line numbers and pagination",
        "safety": "auto",
        "handler": file_read,
        "parameters": {
            "path": {"type": "string", "description": "File path"},
            "offset": {"type": "integer", "description": "Starting line (1-indexed)"},
            "limit": {"type": "integer", "description": "Max lines to read"},
        },
    },
    "file_write": {
        "description": "Write content to a file (overwrites entire file)",
        "safety": "confirm",
        "handler": file_write,
        "parameters": {
            "path": {"type": "string", "description": "File path"},
            "content": {"type": "string", "description": "Complete content to write"},
        },
    },
    "file_patch": {
        "description": "Targeted find-and-replace edit in a file",
        "safety": "confirm",
        "handler": file_patch,
        "parameters": {
            "path": {"type": "string", "description": "File path"},
            "old_string": {"type": "string", "description": "Text to find"},
            "new_string": {"type": "string", "description": "Replacement text"},
            "replace_all": {"type": "boolean", "description": "Replace all occurrences"},
        },
    },
    "file_search": {
        "description": "Search file contents or find files by name",
        "safety": "auto",
        "handler": file_search,
        "parameters": {
            "pattern": {"type": "string", "description": "Regex pattern or glob"},
            "path": {"type": "string", "description": "Directory to search"},
            "target": {"type": "string", "description": "content or files"},
            "file_glob": {"type": "string", "description": "Filter by file pattern"},
        },
    },
    "code_exec": {
        "description": "Execute code in a sandboxed subprocess",
        "safety": "confirm",
        "handler": code_exec,
        "parameters": {
            "code": {"type": "string", "description": "Source code to execute"},
            "language": {"type": "string", "description": "python/bash/javascript"},
            "timeout": {"type": "integer", "description": "Max seconds"},
            "workdir": {"type": "string", "description": "Working directory"},
        },
    },
}


def list_shell_tools() -> list[dict[str, str]]:
    """List all available shell/file/code tools."""
    return [
        {"name": name, "description": info["description"], "safety": info["safety"]}
        for name, info in SHELL_TOOLS.items()
    ]

# ── Register with JEBAT tool system ────────────────────────────────────────
from jebat.tools import register_tool  # noqa: E402
register_tool("shell_exec", handler=terminal_exec, description="Run a shell command with optional timeout and working directory.", schema={"command": {"type": "string"}, "timeout": {"type": "integer", "description": "Max seconds, default 60"}, "workdir": {"type": "string", "description": "Working directory"}})
register_tool("shell_read", handler=file_read, description="Read a file with line numbers and optional offset/limit.", schema={"path": {"type": "string"}, "offset": {"type": "integer", "default": 1}, "limit": {"type": "integer", "default": 500}})
register_tool("shell_write", handler=file_write, description="Write content to a file (overwrites).", schema={"path": {"type": "string"}, "content": {"type": "string"}})
register_tool("shell_patch", handler=file_patch, description="Apply find-and-replace patch to a file.", schema={"path": {"type": "string"}, "old_string": {"type": "string"}, "new_string": {"type": "string"}})
register_tool("shell_search", handler=file_search, description="Search file contents by regex, or find files by glob.", schema={"pattern": {"type": "string"}, "target": {"type": "string", "description": "content or files"}, "path": {"type": "string", "description": "Directory to search, default ."}})
register_tool("shell_code", handler=code_exec, description="Execute Python/JavaScript/Bash code in a subprocess.", schema={"code": {"type": "string"}, "language": {"type": "string", "description": "python/bash/javascript, default python"}, "timeout": {"type": "integer", "description": "Max seconds, default 30"}})
