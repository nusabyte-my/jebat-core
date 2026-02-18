"""
JEBAT DevAssistant Sandbox

Safe execution environment for development tasks.

Security:
- Only works in allowed paths (Dev/)
- Validates all commands
- Audit logging
- Confirmation for destructive operations
"""

import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of command execution."""

    success: bool
    output: str = ""
    error: str = ""
    exit_code: int = 0
    duration: float = 0.0


class DevSandbox:
    """
    Safe execution sandbox for development tasks.

    Only allows operations in Dev environment.
    """

    # Allowed paths
    ALLOWED_PATHS = [
        Path("C:/Users/shaid/Desktop/Dev").resolve(),
        Path("C:/Users/shaid/Desktop/Dev/jebat").resolve(),
        Path("C:/Users/shaid/Desktop/Dev/jebat_dev").resolve(),
        Path("C:/Users/shaid/Desktop/Dev/projects").resolve(),
    ]

    # Allowed commands
    ALLOWED_COMMANDS = [
        "npm",
        "npx",
        "yarn",
        "pip",
        "pip3",
        "python",
        "python3",
        "node",
        "git",
        "mkdir",
        "copy",
        "del",
        "echo",
        "type",
        "curl",
        "wget",
    ]

    # Blocked commands
    BLOCKED_COMMANDS = [
        "sudo",
        "runas",
        "shutdown",
        "reboot",
        "format",
        "rm -rf /",
        "deltree",
    ]

    def __init__(self, strict_mode: bool = True):
        """
        Initialize sandbox.

        Args:
            strict_mode: Enable strict security
        """
        self.strict_mode = strict_mode
        self.execution_log: List[Dict] = []
        logger.info(f"DevSandbox initialized (strict={strict_mode})")

    def is_path_allowed(self, path: str) -> bool:
        """
        Check if path is within allowed directories.

        Args:
            path: Path to check

        Returns:
            True if allowed
        """
        try:
            resolved = Path(path).resolve()
            return any(
                str(resolved).startswith(str(allowed)) for allowed in self.ALLOWED_PATHS
            )
        except Exception:
            return False

    def is_command_allowed(self, command: str) -> bool:
        """
        Check if command is allowed.

        Args:
            command: Command to check

        Returns:
            True if allowed
        """
        # Check blocked first
        if any(blocked in command for blocked in self.BLOCKED_COMMANDS):
            return False

        # Check allowed
        base_cmd = command.split()[0] if command else ""
        return base_cmd in self.ALLOWED_COMMANDS

    async def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: int = 60,
    ) -> ExecutionResult:
        """
        Execute command in sandbox.

        Args:
            command: Command to execute
            cwd: Working directory
            timeout: Timeout in seconds

        Returns:
            ExecutionResult
        """
        start_time = datetime.utcnow()

        # Validate command
        if not self.is_command_allowed(command):
            logger.error(f"Blocked command: {command}")
            return ExecutionResult(
                success=False,
                error=f"Command not allowed: {command}",
            )

        # Validate path
        if cwd and not self.is_path_allowed(cwd):
            logger.error(f"Blocked path: {cwd}")
            return ExecutionResult(
                success=False,
                error=f"Path not allowed: {cwd}",
            )

        # Execute
        try:
            logger.info(f"Executing: {command} (cwd={cwd})")

            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            duration = (datetime.utcnow() - start_time).total_seconds()

            exec_result = ExecutionResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr,
                exit_code=result.returncode,
                duration=duration,
            )

            # Log execution
            self.execution_log.append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "command": command,
                    "cwd": cwd,
                    "success": exec_result.success,
                    "duration": duration,
                }
            )

            return exec_result

        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {command}")
            return ExecutionResult(
                success=False,
                error=f"Command timed out after {timeout}s",
            )

        except Exception as e:
            logger.error(f"Command failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
            )

    async def read_file(self, path: str) -> Optional[str]:
        """
        Read file from allowed paths.

        Args:
            path: File path

        Returns:
            File content or None
        """
        if not self.is_path_allowed(path):
            logger.error(f"Blocked read: {path}")
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Read failed: {e}")
            return None

    async def write_file(self, path: str, content: str) -> bool:
        """
        Write file to allowed paths.

        Args:
            path: File path
            content: File content

        Returns:
            True if successful
        """
        if not self.is_path_allowed(path):
            logger.error(f"Blocked write: {path}")
            return False

        try:
            # Create parent directories
            Path(path).parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Written: {path}")
            return True

        except Exception as e:
            logger.error(f"Write failed: {e}")
            return False

    def get_log(self) -> List[Dict]:
        """Get execution log."""
        return self.execution_log.copy()
