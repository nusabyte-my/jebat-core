"""Test terminal executor."""

import sys
import pytest

from jebat.terminal.executor import TerminalExecutor


@pytest.mark.asyncio
async def test_run_simple_command() -> None:
    exec = TerminalExecutor()
    result = await exec.run("echo hello")
    assert result["exit_code"] == 0
    assert "hello" in result["output"]
    assert result["duration_ms"] >= 0


@pytest.mark.asyncio
async def test_run_with_timeout() -> None:
    exec = TerminalExecutor()
    # Sleep longer than timeout — must be killed
    result = await exec.run(f'{sys.executable} -c "import time; time.sleep(10)"', timeout=1)
    assert result["exit_code"] == -1
    assert "TIMEOUT" in result["output"]


@pytest.mark.asyncio
async def test_run_nonexistent_command() -> None:
    exec = TerminalExecutor()
    result = await exec.run("nonexistent_command_xyz_12345")
    # On Windows/MSYS, subprocess runs via bash — it exits with code 1, not FileNotFoundError
    assert result.get("error") is not None or result["exit_code"] != 0


@pytest.mark.asyncio
async def test_run_bad_workdir() -> None:
    exec = TerminalExecutor()
    result = await exec.run("echo test", workdir="/does/not/exist")
    assert "error" in result
    assert "does not exist" in str(result["error"])


@pytest.mark.asyncio
async def test_background_start_poll_wait() -> None:
    exec = TerminalExecutor()
    start_result = await exec.start_bg("echo hello_bg")
    session_id = start_result["session_id"]
    assert start_result["status"] == "running"

    # Wait a tiny bit for process to finish
    import asyncio
    await asyncio.sleep(0.2)

    poll = await exec.poll(session_id)
    assert poll["status"] in ("running", "done")

    wait = await exec.wait(session_id)
    assert wait["status"] == "done"
    assert "hello_bg" in wait["output"]


@pytest.mark.asyncio
async def test_background_kill() -> None:
    exec = TerminalExecutor()
    # Start a long-running process
    start_result = await exec.start_bg(f'{sys.executable} -c "import time; time.sleep(30)"')
    session_id = start_result["session_id"]

    # Kill it
    kill = await exec.kill(session_id)
    assert kill["status"] == "killed"


@pytest.mark.asyncio
async def test_bg_nonexistent_session() -> None:
    exec = TerminalExecutor()
    poll = await exec.poll("bad_session_id")
    assert "error" in poll


@pytest.mark.asyncio
async def test_list_background_processes() -> None:
    exec = TerminalExecutor()
    await exec.start_bg(f'{sys.executable} -c "import time; time.sleep(30)"')
    result = exec.list_bg()
    assert "processes" in result
    assert len(result["processes"]) > 0