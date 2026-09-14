"""Machine-facing direct tool command contracts."""

import json

import pytest

from jebat_cli_new.tool_command import run_tool_command


@pytest.mark.unit
def test_tool_list_json_is_machine_readable(capsys: pytest.CaptureFixture[str]) -> None:
    """Given the tool list command, JSON output contains registered tool names."""
    status = run_tool_command(["list", "--json"])

    payload = json.loads(capsys.readouterr().out)

    assert status == 0
    assert {item["name"] for item in payload} >= {"file_read", "memory_search"}


@pytest.mark.unit
def test_tool_call_json_returns_tool_envelope(capsys: pytest.CaptureFixture[str]) -> None:
    """Given a safe file-read call, JSON output contains the selected tool result."""
    status = run_tool_command(
        ["call", "file_read", "--args", json.dumps({"path": "README.md", "limit": 1}), "--json", "--yolo"]
    )

    payload = json.loads(capsys.readouterr().out)

    assert status == 0
    assert payload["tool"] == "file_read"
    assert "README.md" in payload["result"]
