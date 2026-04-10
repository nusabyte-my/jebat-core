from __future__ import annotations

import asyncio

try:
    from rich.console import Console

    RICH_AVAILABLE = True
except ImportError:  # pragma: no cover
    RICH_AVAILABLE = False
    Console = None  # type: ignore[assignment]

from apps.api.features.security_console.models import (
    CopilotChatRequest,
    CreateFindingRequest,
    CreateSessionRequest,
    CreateTargetRequest,
    ExecuteCommandRequest,
    TargetType,
)
from apps.api.features.security_console.service import get_security_console_service

from .views import render_findings, render_overview, render_runs


class SecurityConsoleCLI:
    def __init__(self) -> None:
        self.service = get_security_console_service()
        self.console = Console() if RICH_AVAILABLE else None

    async def run(self) -> int:
        self._print_overview()
        while True:
            command = input(
                "\nserangan> choose: [list|new-target|new-session|runs|run|findings|add-finding|ask|quit] "
            ).strip()
            if command in {"quit", "exit", "q"}:
                return 0
            if command == "list":
                self._print_overview()
                continue
            if command == "new-target":
                await self._new_target()
                continue
            if command == "new-session":
                await self._new_session()
                continue
            if command == "findings":
                self._show_findings()
                continue
            if command == "runs":
                self._show_runs()
                continue
            if command == "run":
                await self._run_command()
                continue
            if command == "add-finding":
                await self._add_finding()
                continue
            if command == "ask":
                await self._ask_copilot()
                continue
            print("Unknown command.")

    def _print_overview(self) -> None:
        if self.console:
            render_overview(self.console, self.service.list_targets(), self.service.list_sessions())
            return
        print("Serangan Console")
        for target in self.service.list_targets():
            print(f"- target {target.id}: {target.name} [{target.type.value}]")
        for session in self.service.list_sessions():
            print(f"- session {session.id}: target={session.target_id} model={session.model}")

    async def _new_target(self) -> None:
        name = input("target name: ").strip()
        scope = input("scope: ").strip()
        raw_type = input("type [workspace/web/api/host/container]: ").strip().lower() or "workspace"
        target = self.service.create_target(
            CreateTargetRequest(
                name=name,
                scope=scope,
                type=TargetType(raw_type),
                tags=["manual"],
                engagement_mode="manual",
                allowed_tools=["rg", "httpx", "nuclei", "ffuf", "python"],
            )
        )
        print(f"Created target {target.id}")

    async def _new_session(self) -> None:
        target_id = input("target id: ").strip()
        model = input("ollama model [qwen2.5-coder:7b]: ").strip() or "qwen2.5-coder:7b"
        session = self.service.create_session(
            CreateSessionRequest(
                target_id=target_id,
                provider="ollama",
                model=model,
                operator="local-operator",
            )
        )
        print(f"Created session {session.id}")

    def _show_findings(self) -> None:
        session_id = input("session id: ").strip()
        findings = self.service.list_findings(session_id)
        if self.console:
            render_findings(self.console, findings)
            return
        for finding in findings:
            print(f"- {finding.severity.value}: {finding.title}")

    def _show_runs(self) -> None:
        session_id = input("session id: ").strip()
        runs = self.service.list_runs(session_id)
        if self.console:
            render_runs(self.console, runs)
            return
        for run in runs:
            print(f"- {run.tool}: {run.command} [{run.status.value}]")

    async def _run_command(self) -> None:
        session_id = input("session id: ").strip()
        tool = input("tool: ").strip() or "shell"
        command = input("command: ").strip()
        cwd = input("cwd [.]: ").strip() or "."
        before_count = len(self.service.list_findings(session_id))
        run = self.service.execute_command(
            session_id,
            ExecuteCommandRequest(tool=tool, command=command, cwd=cwd),
        )
        after_count = len(self.service.list_findings(session_id))
        print(f"\n[{run.status.value}] exit={run.exit_code}")
        if run.stdout.strip():
            print(run.stdout[:4000])
        if run.stderr.strip():
            print(run.stderr[:4000])
        promoted = after_count - before_count
        if promoted > 0:
            print(f"\nAuto-promoted {promoted} finding(s) from command output.")

    async def _add_finding(self) -> None:
        session_id = input("session id: ").strip()
        title = input("title: ").strip()
        severity = input("severity [low|medium|high|critical|info]: ").strip().lower() or "medium"
        evidence = input("evidence summary: ").strip()
        finding = self.service.create_finding(
            session_id,
            CreateFindingRequest(
                title=title,
                severity=severity,
                evidence_summary=evidence,
                source_tool="manual",
            ),
        )
        print(f"Created finding {finding.id}")

    async def _ask_copilot(self) -> None:
        session_id = input("session id: ").strip()
        message = input("ask ollama: ").strip()
        response = await self.service.chat(
            session_id,
            CopilotChatRequest(message=message, mode="suggest_next_step"),
        )
        print(f"\n[{response.provider}/{response.model}]")
        print(response.response)


def main() -> int:
    return asyncio.run(SecurityConsoleCLI().run())
