"""CLI entrypoint contracts for terminal and automation compatibility."""

import os
import subprocess
import sys

import pytest


@pytest.mark.unit
def test_help_survives_legacy_windows_console_encoding() -> None:
    """Given cp1252 stdout, help exits cleanly instead of crashing on symbols."""
    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "cp1252"

    completed = subprocess.run(
        [sys.executable, "-m", "jebat_cli_new", "--help"],
        capture_output=True,
        env=environment,
        check=False,
    )

    assert completed.returncode == 0
    assert b"v8.2.1" in completed.stdout
