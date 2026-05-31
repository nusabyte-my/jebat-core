"""JEBAT Sandbox — Docker isolation for code_exec and terminal commands.

Safety-critical code runs inside a disposable Docker container:
  - No host filesystem access (except mounted project dir)
  - Network isolation (no internet by default)
  - Resource limits (CPU, memory, timeout)
  - Auto-destroy after execution

This is the TukangBesi forge — dangerous work happens in containment.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class SandboxResult:
    """Result from sandboxed execution."""
    stdout: str = ""
    stderr: str = ""
    exit_code: int = -1
    timed_out: bool = False
    container_id: str = ""
    duration_ms: int = 0
    files_created: list[str] = field(default_factory=list)


# ── Docker Container Sandbox ─────────────────────────────────────────────

DEFAULT_DOCKER_IMAGE = "python:3.11-slim"
DEFAULT_TIMEOUT = 60  # seconds
DEFAULT_MEMORY_LIMIT = "512m"
DEFAULT_CPU_LIMIT = 1.0


def check_docker_available() -> bool:
    """Check if Docker daemon is running and accessible."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def sandbox_exec_python(
    code: str,
    timeout: int = DEFAULT_TIMEOUT,
    memory: str = DEFAULT_MEMORY_LIMIT,
    cpu: float = DEFAULT_CPU_LIMIT,
    mount_dir: str | None = None,
    network: bool = False,
    docker_image: str = DEFAULT_DOCKER_IMAGE,
    env_vars: dict[str, str] | None = None,
) -> SandboxResult:
    """Execute Python code inside a Docker sandbox.

    Args:
        code: Python code to execute
        timeout: Max execution time in seconds
        memory: Docker memory limit (e.g. '512m', '1g')
        cpu: CPU limit as float (1.0 = 1 core)
        mount_dir: Host directory to mount as /workspace (read-only by default)
        network: Allow network access inside container
        docker_image: Docker image to use
        env_vars: Environment variables to pass into container

    Returns:
        SandboxResult with stdout, stderr, exit_code
    """
    if not check_docker_available():
        return SandboxResult(
            stderr="Docker not available. Install Docker or run without sandbox.",
            exit_code=-1,
        )

    # Write code to temp file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", prefix="jebat_sandbox_",
        delete=False, dir=mount_dir or tempfile.gettempdir(),
    ) as f:
        f.write(code)
        script_path = f.name

    script_name = os.path.basename(script_path)
    mount_host = mount_dir or tempfile.gettempdir()

    # Build docker run command
    cmd = [
        "docker", "run",
        "--rm",  # Auto-remove container after execution
        f"--memory={memory}",
        f"--cpus={cpu}",
        f"--stop-timeout={timeout}",
        "--name", f"jebat_sandbox_{int(time.time())}",
    ]

    # Mount directory
    if mount_dir:
        cmd.extend(["-v", f"{mount_host}:/workspace:ro"])
    else:
        cmd.extend(["-v", f"{mount_host}:/tmp:ro"])

    # Network isolation
    if not network:
        cmd.append("--network=none")

    # Environment variables
    if env_vars:
        for key, value in env_vars.items():
            cmd.extend(["-e", f"{key}={value}"])

    # The actual execution
    cmd.extend([docker_image, "python", f"/workspace/{script_name}" if mount_dir else f"/tmp/{script_name}"])

    start_time = time.time()
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout + 15,  # Extra time for container startup
        )
        duration_ms = int((time.time() - start_time) * 1000)

        # Clean up temp file
        try:
            os.unlink(script_path)
        except OSError:
            pass

        return SandboxResult(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            timed_out=False,
            duration_ms=duration_ms,
        )
    except subprocess.TimeoutExpired as e:
        duration_ms = int((time.time() - start_time) * 1000)
        # Kill the container
        container_name = f"jebat_sandbox_{int(start_time)}"
        subprocess.run(["docker", "kill", container_name], capture_output=True, timeout=5)

        # Clean up temp file
        try:
            os.unlink(script_path)
        except OSError:
            pass

        return SandboxResult(
            stdout=e.stdout or "",
            stderr=e.stderr or "",
            exit_code=-1,
            timed_out=True,
            duration_ms=duration_ms,
        )


def sandbox_exec_command(
    command: str,
    timeout: int = DEFAULT_TIMEOUT,
    memory: str = DEFAULT_MEMORY_LIMIT,
    mount_dir: str | None = None,
    network: bool = False,
    docker_image: str = "alpine:latest",
) -> SandboxResult:
    """Execute a shell command inside a Docker sandbox.

    Args:
        command: Shell command to execute
        timeout: Max execution time in seconds
        memory: Docker memory limit
        mount_dir: Host directory to mount as /workspace
        network: Allow network access
        docker_image: Docker image (default: alpine for fast startup)

    Returns:
        SandboxResult with stdout, stderr, exit_code
    """
    if not check_docker_available():
        return SandboxResult(
            stderr="Docker not available.",
            exit_code=-1,
        )

    cmd = [
        "docker", "run",
        "--rm",
        f"--memory={memory}",
        f"--stop-timeout={timeout}",
    ]

    if mount_dir:
        cmd.extend(["-v", f"{mount_dir}:/workspace"])
    if not network:
        cmd.append("--network=none")

    cmd.extend([docker_image, "sh", "-c", command])

    start_time = time.time()
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout + 15,
        )
        duration_ms = int((time.time() - start_time) * 1000)

        return SandboxResult(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            timed_out=False,
            duration_ms=duration_ms,
        )
    except subprocess.TimeoutExpired as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return SandboxResult(
            stdout=e.stdout or "",
            stderr=e.stderr or "",
            exit_code=-1,
            timed_out=True,
            duration_ms=duration_ms,
        )


def sandbox_build_image(
    dockerfile_path: str,
    tag: str = "jebat-sandbox:latest",
) -> dict[str, Any]:
    """Build a custom sandbox Docker image from a Dockerfile.

    Args:
        dockerfile_path: Path to Dockerfile
        tag: Image tag

    Returns:
        Dict with build status and image ID
    """
    if not check_docker_available():
        return {"status": "error", "message": "Docker not available"}

    cmd = [
        "docker", "build",
        "-t", tag,
        "-f", dockerfile_path,
        os.path.dirname(dockerfile_path) or ".",
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=300,
        )
        if result.returncode == 0:
            # Extract image ID from output
            image_id = ""
            for line in result.stdout.splitlines():
                if "Successfully built" in line:
                    image_id = line.split()[-1]
            return {"status": "built", "image_id": image_id, "tag": tag}
        else:
            return {"status": "error", "message": result.stderr[-500:]}
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Build timed out (5min limit)"}


# ── Sandbox Registry ─────────────────────────────────────────────────────

SANDBOX_TOOLS: dict[str, dict[str, Any]] = {
    "sandbox_exec_python": {
        "description": "Execute Python code in a Docker sandbox (isolated, resource-limited)",
        "safety": "auto",
        "handler": sandbox_exec_python,
        "parameters": {
            "code": {"type": "string", "description": "Python code to execute"},
            "timeout": {"type": "integer", "description": "Max execution time (seconds)", "default": 60},
            "memory": {"type": "string", "description": "Memory limit (e.g. '512m')", "default": "512m"},
            "network": {"type": "boolean", "description": "Allow network access", "default": False},
        },
    },
    "sandbox_exec_command": {
        "description": "Execute shell command in a Docker sandbox (isolated, resource-limited)",
        "safety": "auto",
        "handler": sandbox_exec_command,
        "parameters": {
            "command": {"type": "string", "description": "Shell command to execute"},
            "timeout": {"type": "integer", "description": "Max execution time (seconds)", "default": 60},
            "network": {"type": "boolean", "description": "Allow network access", "default": False},
        },
    },
    "sandbox_build_image": {
        "description": "Build a custom sandbox Docker image from a Dockerfile",
        "safety": "confirm",
        "handler": sandbox_build_image,
        "parameters": {
            "dockerfile_path": {"type": "string", "description": "Path to Dockerfile"},
            "tag": {"type": "string", "description": "Image tag", "default": "jebat-sandbox:latest"},
        },
    },
    "check_docker_available": {
        "description": "Check if Docker daemon is running and accessible",
        "safety": "auto",
        "handler": check_docker_available,
        "parameters": {},
    },
}


def list_sandbox_tools() -> list[dict[str, str]]:
    """List all sandbox tools."""
    return [
        {"name": name, "description": info["description"], "safety": info["safety"]}
        for name, info in SANDBOX_TOOLS.items()
    ]


# ── Tool Registration ────────────────────────────────────────────────────

from jebat.tools import register_tool  # noqa: E402 (intentional late import for tool wiring)

# sandbox_run: execute Python code in a Docker container
register_tool(
    "sandbox_run",
    handler=sandbox_exec_python,
    description="Execute Python code in an isolated Docker sandbox with resource limits, optional network access, and configurable timeout/image",
    schema={
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Python code to execute inside the sandbox"},
            "timeout": {"type": "integer", "description": "Max execution time in seconds", "default": 60},
            "image": {"type": "string", "description": "Docker image to use", "default": "python:3.11-slim"},
            "network": {"type": "boolean", "description": "Allow network access inside container", "default": False},
        },
        "required": ["code"],
    },
)

# sandbox_check: verify Docker daemon is available
register_tool(
    "sandbox_check",
    handler=check_docker_available,
    description="Check if the Docker daemon is running and accessible on this system",
    schema={
        "type": "object",
        "properties": {},
        "required": [],
    },
)

# sandbox_cleanup: remove old sandbox containers
def _cleanup_containers(max_age_hours: int = 24) -> dict[str, Any]:
    """Remove sandbox containers older than the specified age."""
    if not check_docker_available():
        return {"status": "error", "message": "Docker not available", "removed": 0}
    try:
        result = subprocess.run(
            [
                "docker", "container", "prune",
                "--filter", f"until={max_age_hours}h",
                "--filter", "label=jebat-sandbox",
                "--force",
            ],
            capture_output=True, text=True, timeout=30,
        )
        return {"status": "ok", "removed": result.stdout.strip(), "stderr": result.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Cleanup timed out", "removed": 0}

register_tool(
    "sandbox_cleanup",
    handler=_cleanup_containers,
    description="Remove old JEBAT sandbox Docker containers to free up disk space",
    schema={
        "type": "object",
        "properties": {
            "max_age_hours": {"type": "integer", "description": "Maximum age of containers to keep, in hours", "default": 24},
        },
        "required": [],
    },
)