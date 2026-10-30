"""Behavioral coverage for the canonical console command palette."""

import builtins
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from jebat_cli_new.command_palette import choose_command, filter_commands, fuzzy_match


@pytest.mark.unit
def test_palette_filters_and_completes_argument_commands() -> None:
    entries = [("/model", "Switch model"), ("/tool", "Call a shared tool")]
    assert fuzzy_match("/mdl", "/model")
    selected = filter_commands(entries, "/tool")
    assert [item.name for item in selected] == ["/tool"]
    assert selected[0].needs_argument


@pytest.mark.unit
def test_noninteractive_palette_returns_selected_command() -> None:
    selected = choose_command(
        [("/help", "Help"), ("/version", "Version")],
        interactive=False,
        input_fn=lambda _prompt: "2",
    )
    assert selected == ("/version", "")


@pytest.mark.unit
def test_repl_executes_palette_selection_through_normal_handler(monkeypatch) -> None:
    """Regression: picker selections used to fall through without executing."""
    from jebat_cli_new import jebat

    registry = SimpleNamespace(get_active=lambda: None)
    taskdb = SimpleNamespace()
    agent = SimpleNamespace(messages=[], mode="auto")
    inputs = iter(["/", "/exit"])

    monkeypatch.setattr(jebat, "_auto_mimpi_check", lambda _taskdb: None)
    monkeypatch.setattr(jebat, "_interactive_command_picker", lambda: ("/version", ""))
    monkeypatch.setattr(builtins, "input", lambda _prompt="": next(inputs))
    with patch("jebat_cli_new.jebat.cprint") as output:
        jebat.repl(registry, taskdb, SimpleNamespace(), agent=agent, persist_session=False)

    assert any("JEBAT v" in str(call.args[0]) for call in output.call_args_list)
