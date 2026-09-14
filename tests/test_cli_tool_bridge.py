"""Contracts for exposing the shared JEBAT tool registry to the CLI agent."""

import subprocess
import sys

import pytest


@pytest.mark.unit
def test_cli_tool_definitions_include_shared_registry_tools() -> None:
    """Given the canonical CLI tools, shared registry tools are discoverable."""
    from jebat_cli_new.tools import TOOL_DEFINITIONS

    names = {definition["name"] for definition in TOOL_DEFINITIONS}

    assert {"file_read", "memory_search", "browser_snapshot"} <= names


@pytest.mark.unit
def test_tool_registry_bootstrap_is_silent_for_machine_consumers() -> None:
    """Given a clean interpreter, loading shared tools writes no protocol noise."""
    completed = subprocess.run(
        [sys.executable, "-c", "from jebat_cli_new.tool_bridge import shared_tool_definitions; shared_tool_definitions()"],
        capture_output=True,
        check=False,
        text=True,
    )

    assert completed.returncode == 0
    assert completed.stdout == ""
