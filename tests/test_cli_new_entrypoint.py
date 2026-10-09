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
    # Assert the live package version so this test survives version bumps.
    from jebat_cli_new import __version__ as cli_version

    assert f"v{cli_version}".encode() in completed.stdout


@pytest.mark.unit
def test_subcommand_flags_survive_as_residual() -> None:
    """Subcommand-owned flags (`--transport`, `--name`) reach `main` untouched.

    Regression: the global parser rejected unknown flags anywhere on the line,
    so `jebat mcp serve --transport stdio` and `jebat agentix auto ... --name X`
    (i.e. the IDE configs and the solution foundry) died with argparse exit 2.
    """
    from jebat_cli_new import cli

    _, residual = cli.parse(["--no-extensions", "mcp", "serve", "--transport", "stdio"])
    assert residual == ["mcp", "serve", "--transport", "stdio"]

    _, residual = cli.parse(
        ["--no-extensions", "agentix", "auto", "watch", "notes", "--name", "digest", "--dir", "out"]
    )
    assert residual == ["agentix", "auto", "watch", "notes", "--name", "digest", "--dir", "out"]

    # Leading global flags stay global; the subcommand tail stays intact.
    ns, residual = cli.parse(["--no-extensions", "--yolo", "agentix", "run", "x", "--verbose"])
    assert ns.yolo is True
    assert residual == ["agentix", "run", "x", "--verbose"]

    # `--help` after a subcommand belongs to the subcommand.
    _, residual = cli.parse(["--no-extensions", "learning", "--help"])
    assert residual == ["learning", "--help"]
