"""Async terminal executor — foreground and background subprocess execution.

Provides:
  - Foreground: run a command, get output + exit code, with timeout
  - Background: start/poll/wait/kill long-running processes
  - PTY mode for interactive CLI tools
"""

import asyncio
import os
import signal
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ProcessState:
    """Holds the state of a background process."""
    id: str
    command: str
    process: asyncio.subprocess.Process
    output: list[str] = field(default_factory=list)
    status: str = "running"  # running | done | killed | error
    exit_code: Optional[int] = None
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None
    workdir: Optional[str] = None


class TerminalExecutor:
    """Async terminal executor with foreground/background/PTY support."""

    _bg_processes: dict[str, ProcessState] = {}

    # --- Foreground ---

    async def run(
        self,
        command: str,
        timeout: int = 180,
        workdir: Optional[str] = None,
        pty: bool = False,
    ) -> dict:
        """Run a command in foreground and return output + exit code.

        Args:
            command: Shell command to execute.
            timeout: Max seconds to wait (default 180).
            workdir: Working directory for the command.
            pty: If True, use pseudo-terminal (for interactive tools).

        Returns:
            {"output": str, "exit_code": int, "duration_ms": int}
            or {"error": str}
        """
        cwd = Path(workdir).resolve() if workdir else None
        if cwd and not cwd.is_dir():
            return {"error": f"Working directory does not exist: {workdir}"}

        started = time.monotonic()
        try:
            if pty:
                proc = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    cwd=cwd,
                    start_new_session=True,  # PTY-like: isolate process group
                )
            else:
                proc = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    cwd=cwd,
                )

            try:
                stdout_bytes, _ = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                duration_ms = int((time.monotonic() - started) * 1000)
                return {
                    "output": "[TIMEOUT] Command exceeded timeout limit",
                    "exit_code": -1,
                    "duration_ms": duration_ms,
                }

            output = stdout_bytes.decode("utf-8", errors="replace").rstrip()
            duration_ms = int((time.monotonic() - started) * 1000)
            return {
                "output": output,
                "exit_code": proc.returncode or 0,
                "duration_ms": duration_ms,
            }

        except FileNotFoundError:
            return {"error": f"Command not found: {command.split()[0]}"}
        except Exception as e:
            return {"error": f"Execution failed: {e}"}

    # --- Background ---

    async def start_bg(
        self,
        command: str,
        workdir: Optional[str] = None,
    ) -> dict:
        """Start a command in the background. Returns a session_id."""
        session_id = str(uuid.uuid4())[:8]

        cwd = Path(workdir).resolve() if workdir else None
        if cwd and not cwd.is_dir():
            return {"error": f"Working directory does not exist: {workdir}"}

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=cwd,
            )
        except Exception as e:
            return {"error": f"Failed to start: {e}"}

        state = ProcessState(
            id=session_id,
            command=command,
            process=proc,
            workdir=workdir,
        )
        self._bg_processes[session_id] = state

        # Start background reader
        asyncio.ensure_future(self._read_bg_output(session_id))

        return {
            "session_id": session_id,
            "command": command,
            "status": "running",
        }

    async def poll(self, session_id: str) -> dict:
        """Check status of a background process."""
        state = self._bg_processes.get(session_id)
        if not state:
            return {"error": f"No background process with id: {session_id}"}

        return {
            "session_id": session_id,
            "status": state.status,
            "exit_code": state.exit_code,
            "output_tail": "\n".join(state.output[-20:]),
        }

    async def wait(self, session_id: str, timeout: int = 300) -> dict:
        """Block until a background process finishes."""
        state = self._bg_processes.get(session_id)
        if not state:
            return {"error": f"No background process with id: {session_id}"}

        if state.status != "running":
            return {
                "session_id": session_id,
                "status": state.status,
                "exit_code": state.exit_code,
                "output": "\n".join(state.output),
            }

        try:
            await asyncio.wait_for(state.process.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            state.process.kill()
            state.status = "killed"
            state.exit_code = -1
            state.finished_at = time.time()
            return {
                "session_id": session_id,
                "status": "killed",
                "error": "Timeout",
            }

        state.exit_code = state.process.returncode
        state.status = "done"
        state.finished_at = time.time()
        return {
            "session_id": session_id,
            "status": state.status,
            "exit_code": state.exit_code,
            "output": "\n".join(state.output),
        }

    async def kill(self, session_id: str) -> dict:
        """Kill a background process."""
        state = self._bg_processes.get(session_id)
        if not state:
            return {"error": f"No background process with id: {session_id}"}

        if state.status != "running":
            return {
                "session_id": session_id,
                "status": state.status,
                "message": "Process already finished",
            }

        try:
            state.process.kill()
            await state.process.wait()
        except Exception:
            pass

        state.status = "killed"
        state.exit_code = -1
        state.finished_at = time.time()
        return {"session_id": session_id, "status": "killed"}

    def list_bg(self) -> dict:
        """List all background processes."""
        return {
            "processes": [
                {
                    "session_id": s.id,
                    "command": s.command,
                    "status": s.status,
                }
                for s in self._bg_processes.values()
            ]
        }

    # --- Internals ---

    async def _read_bg_output(self, session_id: str) -> None:
        """Background reader task — reads stdout lines."""
        state = self._bg_processes.get(session_id)
        if not state:
            return

        try:
            while True:
                line_bytes = await state.process.stdout.readline()
                if not line_bytes:
                    break
                line = line_bytes.decode("utf-8", errors="replace").rstrip("\n")
                state.output.append(line)
        except Exception:
            pass

        # On EOF, mark done if not already killed
        if state.status == "running":
            state.status = "done"
            state.exit_code = state.process.returncode
            state.finished_at = time.time()


# Singleton
_executor: Optional[TerminalExecutor] = None


def get_executor() -> TerminalExecutor:
    global _executor
    if _executor is None:
        _executor = TerminalExecutor()
    return _executor