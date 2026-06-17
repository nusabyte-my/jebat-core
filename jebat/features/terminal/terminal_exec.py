"""JEBAT Terminal Execution — shell commands with safety, timeout, background processes, and PTY.

Features:
- Foreground execution with timeout and safety classification
- Background processes with lifecycle management (list, log, kill, write)
- PTY mode for interactive CLI tools
- Safety tier system (auto, confirm, dangerous)
- Output capture with size limits
"""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from jebat.features.security import (
    classify_command,
    write_audit,
    AuditEntry,
    prompt_confirm,
    is_sandbox,
)
from jebat.tools import register_tool

# ── Background Process Manager ───────────────────────────────────────────

_processes: dict[str, "_BgProcess"] = {}
_MAX_OUTPUT_BYTES = 100_000


@dataclass
class _BgProcess:
    session_id: str
    command: str
    process: asyncio.subprocess.Process
    created_at: float = 0.0
    stdout_lines: list[str] = field(default_factory=list)
    stderr_lines: list[str] = field(default_factory=list)
    return_code: int | None = None
    running: bool = True
    pty: bool = False
    workdir: str = ""

    def add_stdout(self, text: str) -> None:
        self.stdout_lines.append(text)
        total = sum(len(l) for l in self.stdout_lines)
        if total > _MAX_OUTPUT_BYTES:
            self.stdout_lines = self.stdout_lines[-100:]  # Keep last 100

    def add_stderr(self, text: str) -> None:
        self.stderr_lines.append(text)


# ── Foreground Execution ──────────────────────────────────────────────────

@register_tool(
    "terminal",
    schema={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Shell command to execute"},
            "timeout": {"type": "integer", "default": 180, "description": "Max seconds"},
            "workdir": {"type": "string", "description": "Working directory"},
            "pty": {"type": "boolean", "default": False, "description": "PTY mode for interactive tools"},
        },
        "required": ["command"],
    },
    safety_tier="auto",
    timeout=600,
    max_output=100_000,
    description="Execute a shell command with safety checks and timeout.",
)
async def terminal(
    command: str,
    timeout: int = 180,
    workdir: str | None = None,
    pty: bool = False,
) -> dict[str, Any]:
    """Execute a shell command with safety checks and timeout.

    Returns dict with keys: output, exit_code, error, duration_ms.
    """
    start = time.time()

    # Safety check
    tier = classify_command(command)
    if is_sandbox():
        return {
            "output": f"[SANDBOX] Would execute: {command}",
            "exit_code": 0,
            "error": None,
            "duration_ms": 0,
        }

    approved = prompt_confirm("terminal", {"command": command}, tier)
    if not approved:
        return {"output": "(cancelled)", "exit_code": -1, "error": "User cancelled", "duration_ms": 0}

    # For PTY mode, delegate to subprocess with PTY
    if pty:
        return await _execute_pty(command, timeout, workdir)

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=workdir or os.getcwd(),
            shell=True,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            duration = int((time.time() - start) * 1000)
            entry = AuditEntry(
                timestamp=datetime.now().isoformat(),
                tool="terminal",
                params={"command": command[:100]},
                result_preview="TIMEOUT",
                duration_ms=duration,
                safety_tier=tier,
                approved=True,
            )
            write_audit(entry)
            return {
                "output": f"[TIMEOUT after {timeout}s]",
                "exit_code": -1,
                "error": "Timeout",
                "duration_ms": duration,
            }

        stdout = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
        stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""

        # Truncate output if too large
        if len(stdout) > _MAX_OUTPUT_BYTES:
            stdout = stdout[:_MAX_OUTPUT_BYTES] + f"\n... [truncated, {len(stdout)} total bytes]"

        duration = int((time.time() - start) * 1000)

        # Audit
        write_audit(AuditEntry(
            timestamp=datetime.now().isoformat(),
            tool="terminal",
            params={"command": command[:100], "workdir": workdir},
            result_preview=stdout[:100],
            duration_ms=duration,
            safety_tier=tier,
            approved=True,
        ))

        return {
            "output": stdout,
            "stderr": stderr,
            "exit_code": proc.returncode or 0,
            "error": stderr if stderr and proc.returncode else None,
            "duration_ms": duration,
        }

    except Exception as e:
        duration = int((time.time() - start) * 1000)
        return {
            "output": "",
            "exit_code": -1,
            "error": str(e),
            "duration_ms": duration,
        }


async def _execute_pty(command: str, timeout: int, workdir: str | None = None) -> dict[str, Any]:
    """Execute command in PTY mode for interactive tools."""
    import pty as pty_module
    import select

    master_fd, slave_fd = pty_module.openpty()
    proc = await asyncio.create_subprocess_exec(
        "bash", "-c", command,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        cwd=workdir or os.getcwd(),
    )
    os.close(slave_fd)

    output = []
    start = time.time()
    try:
        while True:
            r, _, _ = select.select([master_fd], [], [], 0.1)
            if r:
                data = os.read(master_fd, 4096)
                if not data:
                    break
                output.append(data.decode("utf-8", errors="replace"))
            if time.time() - start > timeout:
                proc.kill()
                break
            if proc.returncode is not None:
                # Drain remaining output
                while True:
                    r, _, _ = select.select([master_fd], [], [], 0.1)
                    if not r:
                        break
                    data = os.read(master_fd, 4096)
                    if not data:
                        break
                    output.append(data.decode("utf-8", errors="replace"))
                break
    finally:
        os.close(master_fd)

    stdout = "".join(output)
    return {
        "output": stdout[-_MAX_OUTPUT_BYTES:] if len(stdout) > _MAX_OUTPUT_BYTES else stdout,
        "exit_code": proc.returncode or 0,
        "error": None,
        "duration_ms": int((time.time() - start) * 1000),
    }


# ── Background Execution ─────────────────────────────────────────────────

@register_tool(
    "terminal_bg",
    schema={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Command to run in background"},
            "workdir": {"type": "string", "description": "Working directory"},
            "notify_on_complete": {"type": "boolean", "default": False, "description": "Notify when done"},
        },
        "required": ["command"],
    },
    safety_tier="confirm",
    timeout=10,
    description="Run a command in the background. Returns a process session_id.",
)
async def terminal_bg(command: str, workdir: str | None = None, notify_on_complete: bool = False) -> dict[str, Any]:
    """Start a background process. Returns session_id for lifecycle management."""
    session_id = f"bg_{int(time.time())}"

    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=workdir or os.getcwd(),
        shell=True,
    )

    bg = _BgProcess(
        session_id=session_id,
        command=command,
        process=proc,
        created_at=time.time(),
        workdir=workdir or os.getcwd(),
    )
    _processes[session_id] = bg

    # Start background reader
    asyncio.create_task(_bg_reader(bg, notify_on_complete))

    return {
        "session_id": session_id,
        "command": command,
        "pid": proc.pid,
        "status": "started",
    }


async def _bg_reader(bg: _BgProcess, notify: bool = False) -> None:
    """Read stdout/stderr from a background process."""
    try:
        while True:
            line = await bg.process.stdout.readline()
            if not line:
                break
            bg.add_stdout(line.decode("utf-8", errors="replace").rstrip())
    except Exception:
        pass

    bg.return_code = await bg.process.wait()
    bg.running = False


# ── Process Management ────────────────────────────────────────────────────

@register_tool(
    "process_list",
    schema={},
    safety_tier="auto",
    timeout=5,
    description="List all background processes.",
)
async def process_list() -> dict[str, Any]:
    """List all background processes with their status."""
    processes = []
    for sid, bg in _processes.items():
        processes.append({
            "session_id": sid,
            "command": bg.command[:60],
            "pid": bg.process.pid,
            "running": bg.running,
            "return_code": bg.return_code,
            "created_at": datetime.fromtimestamp(bg.created_at).isoformat() if bg.created_at else "",
            "stdout_lines": len(bg.stdout_lines),
        })
    return {"processes": processes, "count": len(processes)}


@register_tool(
    "process_log",
    schema={
        "type": "object",
        "properties": {
            "session_id": {"type": "string", "description": "Process session_id"},
            "tail": {"type": "integer", "default": 50, "description": "Last N lines"},
        },
        "required": ["session_id"],
    },
    safety_tier="auto",
    timeout=5,
    description="View output of a background process.",
)
async def process_log(session_id: str, tail: int = 50) -> dict[str, Any]:
    """Get the output log of a background process."""
    bg = _processes.get(session_id)
    if bg is None:
        return {"error": f"Process not found: {session_id}"}

    lines = bg.stdout_lines[-tail:]
    return {
        "session_id": session_id,
        "running": bg.running,
        "return_code": bg.return_code,
        "output": "\n".join(lines),
        "total_lines": len(bg.stdout_lines),
        "showing": len(lines),
    }


@register_tool(
    "process_kill",
    schema={
        "type": "object",
        "properties": {
            "session_id": {"type": "string", "description": "Process session_id"},
        },
        "required": ["session_id"],
    },
    safety_tier="confirm",
    timeout=5,
    description="Kill a background process.",
)
async def process_kill(session_id: str) -> dict[str, Any]:
    """Kill a background process."""
    bg = _processes.get(session_id)
    if bg is None:
        return {"error": f"Process not found: {session_id}"}

    try:
        bg.process.kill()
        bg.running = False
        return {"session_id": session_id, "status": "killed"}
    except ProcessLookupError:
        return {"session_id": session_id, "status": "already exited"}


@register_tool(
    "process_write",
    schema={
        "type": "object",
        "properties": {
            "session_id": {"type": "string"},
            "data": {"type": "string", "description": "Data to write to stdin"},
            "newline": {"type": "boolean", "default": True, "description": "Append newline"},
        },
        "required": ["session_id", "data"],
    },
    safety_tier="confirm",
    timeout=5,
    description="Send data to a background process's stdin.",
)
async def process_write(session_id: str, data: str, newline: bool = True) -> dict[str, Any]:
    """Write data to a background process's stdin."""
    bg = _processes.get(session_id)
    if bg is None:
        return {"error": f"Process not found: {session_id}"}

    try:
        payload = (data + "\n") if newline else data
        bg.process.stdin.write(payload.encode())
        await bg.process.stdin.drain()
        return {"session_id": session_id, "sent": len(payload), "status": "ok"}
    except Exception as e:
        return {"session_id": session_id, "error": str(e)}