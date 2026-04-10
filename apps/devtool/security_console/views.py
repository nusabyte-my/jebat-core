from __future__ import annotations

from typing import Iterable

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:  # pragma: no cover
    RICH_AVAILABLE = False
    Console = object  # type: ignore[assignment]
    Panel = object  # type: ignore[assignment]
    Table = object  # type: ignore[assignment]

from apps.api.features.security_console.models import CommandRun, Finding, SecuritySession, Target


def render_overview(console: Console, targets: Iterable[Target], sessions: Iterable[SecuritySession]) -> None:
    if not RICH_AVAILABLE:
        return
    target_table = Table(title="Targets")
    target_table.add_column("ID", style="cyan")
    target_table.add_column("Name")
    target_table.add_column("Type")
    target_table.add_column("Scope", overflow="fold")
    for target in targets:
        target_table.add_row(target.id, target.name, target.type.value, target.scope)

    session_table = Table(title="Sessions")
    session_table.add_column("ID", style="green")
    session_table.add_column("Target")
    session_table.add_column("Status")
    session_table.add_column("Model")
    for session in sessions:
        session_table.add_row(session.id, session.target_id, session.status.value, session.model)

    console.print(Panel.fit("Serangan Console\nLocal-first security operations with Ollama copilot", border_style="red"))
    console.print(target_table)
    console.print(session_table)


def render_findings(console: Console, findings: Iterable[Finding]) -> None:
    if not RICH_AVAILABLE:
        return
    finding_table = Table(title="Findings")
    finding_table.add_column("Severity")
    finding_table.add_column("Title")
    finding_table.add_column("Category")
    finding_table.add_column("Confidence")
    finding_table.add_column("Tool")
    for finding in findings:
        finding_table.add_row(
            finding.severity.value.upper(),
            finding.title,
            finding.category,
            f"{finding.confidence:.2f}",
            finding.source_tool,
        )
    console.print(finding_table)


def render_runs(console: Console, runs: Iterable[CommandRun]) -> None:
    if not RICH_AVAILABLE:
        return
    run_table = Table(title="Command Runs")
    run_table.add_column("Tool")
    run_table.add_column("Command", overflow="fold")
    run_table.add_column("Status")
    run_table.add_column("Exit")
    for run in runs:
        run_table.add_row(
            run.tool,
            run.command,
            run.status.value,
            "" if run.exit_code is None else str(run.exit_code),
        )
    console.print(run_table)
