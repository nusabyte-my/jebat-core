"""Typed command-argument contracts for the canonical CLI."""

import pytest

from jebat_cli_new.cli_args import parse_chat_options, parse_code_options


@pytest.mark.unit
def test_code_options_preserve_prompt_and_provider_overrides() -> None:
    """Given code flags mixed with prompt words, parsing keeps both contracts."""
    options = parse_code_options(
        ["--provider", "work", "Fix", "the", "bug", "--model", "coder", "--plan"]
    )

    assert options.prompt_parts == ("Fix", "the", "bug")
    assert options.provider == "work"
    assert options.model == "coder"
    assert options.plan is True


@pytest.mark.unit
def test_code_options_reject_missing_override_value() -> None:
    """Given a value-taking flag without a value, parsing fails explicitly."""
    with pytest.raises(ValueError, match="requires a value"):
        parse_code_options(["--provider"])


@pytest.mark.unit
def test_canonical_agent_accepts_provider_and_model_overrides() -> None:
    """Given parsed code overrides, the canonical agent exposes matching inputs."""
    from inspect import signature

    from jebat_cli_new.jebat import Agent

    parameters = signature(Agent.step).parameters

    assert {"provider", "model"} <= parameters.keys()


@pytest.mark.unit
def test_chat_options_preserve_provider_and_model_overrides() -> None:
    """Given chat flags mixed with a message, parsing keeps the message intact."""
    options = parse_chat_options(["--provider", "work", "Explain", "this", "--model", "chat"])

    assert options.prompt_parts == ("Explain", "this")
    assert options.provider == "work"
    assert options.model == "chat"


@pytest.mark.unit
def test_canonical_agent_chat_accepts_provider_and_model_overrides() -> None:
    """Given chat overrides, the canonical agent exposes matching inputs."""
    from inspect import signature

    from jebat_cli_new.jebat import Agent

    parameters = signature(Agent.chat).parameters

    assert {"provider", "model"} <= parameters.keys()
