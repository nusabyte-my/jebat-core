from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from apps.api.llm.config import JebatLLMConfig, load_llm_config
from apps.api.llm.providers import generate_with_failover

from .copilot import build_security_copilot_prompt
from .models import (
    CommandRun,
    CopilotChatRequest,
    CopilotChatResponse,
    CopilotMessage,
    CreateFindingRequest,
    CreateRunRequest,
    CreateSessionRequest,
    CreateTargetRequest,
    ExecuteCommandRequest,
    Finding,
    RunStatus,
    SecurityConsoleSnapshot,
    SecuritySession,
    SessionStatus,
    Target,
)
from .parsers import parse_command_output
from .sqlite_store import SecurityConsoleSQLiteStore


@dataclass
class SecurityConsoleService:
    sqlite_path: Path = field(
        default_factory=lambda: Path(
            os.getenv("JEBAT_SECURITY_CONSOLE_DB", ".jebat/security_console.db")
        )
    )
    storage_path: Path = field(
        default_factory=lambda: Path(
            os.getenv("JEBAT_SECURITY_CONSOLE_STATE", ".jebat/security_console_state.json")
        )
    )
    targets: dict[str, Target] = field(default_factory=dict)
    sessions: dict[str, SecuritySession] = field(default_factory=dict)
    findings: dict[str, list[Finding]] = field(default_factory=dict)
    runs: dict[str, list[CommandRun]] = field(default_factory=dict)
    messages: dict[str, list[CopilotMessage]] = field(default_factory=dict)
    store: SecurityConsoleSQLiteStore | None = None

    def __post_init__(self) -> None:
        self.store = SecurityConsoleSQLiteStore(self.sqlite_path)
        self._load_state()
        if not self.targets:
            workspace = self.create_target(
                CreateTargetRequest(
                    name="Local Workspace",
                    type="workspace",
                    scope="Current repository and local security tooling",
                    tags=["local", "repo"],
                    engagement_mode="manual",
                    allowed_tools=["rg", "nmap", "httpx", "nuclei", "ffuf", "python"],
                )
            )
            self.create_session(
                CreateSessionRequest(
                    target_id=workspace.id,
                    operator="bootstrap",
                    provider="ollama",
                    model="qwen2.5-coder:7b",
                    notes="Default local security workspace session",
                )
            )
            self._save_state()

    def list_targets(self) -> list[Target]:
        return list(self.targets.values())

    def create_target(self, request: CreateTargetRequest) -> Target:
        target = Target(**request.model_dump())
        self.targets[target.id] = target
        self._persist_target(target)
        return target

    def list_sessions(self, status: str | None = None, query: str | None = None) -> list[SecuritySession]:
        items = list(self.sessions.values())
        if status:
            items = [item for item in items if item.status.value == status]
        if query:
            needle = query.strip().lower()
            items = [
                item
                for item in items
                if needle in item.id.lower()
                or needle in item.target_id.lower()
                or needle in item.model.lower()
                or needle in item.status.value.lower()
                or needle in item.operator.lower()
                or needle in item.notes.lower()
            ]
        return sorted(items, key=lambda item: item.started_at, reverse=True)

    def get_session(self, session_id: str) -> SecuritySession | None:
        return self.sessions.get(session_id)

    def create_session(self, request: CreateSessionRequest) -> SecuritySession:
        if request.target_id not in self.targets:
            raise KeyError(f"unknown target: {request.target_id}")
        session = SecuritySession(
            **request.model_dump(),
            status=SessionStatus.ACTIVE,
        )
        self.sessions[session.id] = session
        self.findings.setdefault(session.id, [])
        self.runs.setdefault(session.id, [])
        self.messages.setdefault(session.id, [])
        self._persist_session(session)
        return session

    def list_findings(
        self,
        session_id: str,
        severity: str | None = None,
        source_tool: str | None = None,
        query: str | None = None,
    ) -> list[Finding]:
        items = list(self.findings.get(session_id, []))
        return self._filter_findings(items, severity=severity, source_tool=source_tool, query=query)

    def create_finding(self, session_id: str, request: CreateFindingRequest) -> Finding:
        session = self._require_session(session_id)
        finding = Finding(
            session_id=session.id,
            target_id=session.target_id,
            **request.model_dump(),
        )
        self.findings.setdefault(session_id, []).append(finding)
        self._persist_finding(finding)
        return finding

    def list_all_findings(
        self,
        severity: str | None = None,
        source_tool: str | None = None,
        query: str | None = None,
    ) -> list[Finding]:
        items = [item for rows in self.findings.values() for item in rows]
        return self._filter_findings(items, severity=severity, source_tool=source_tool, query=query)

    def list_runs(self, session_id: str, tool: str | None = None, status: str | None = None) -> list[CommandRun]:
        items = list(self.runs.get(session_id, []))
        if tool:
            items = [item for item in items if item.tool.lower() == tool.lower()]
        if status:
            items = [item for item in items if item.status.value == status]
        return sorted(items, key=lambda item: item.started_at, reverse=True)

    def create_run(self, session_id: str, request: CreateRunRequest) -> CommandRun:
        session = self._require_session(session_id)
        run = CommandRun(
            session_id=session.id,
            **request.model_dump(),
        )
        if run.status in {RunStatus.COMPLETE, RunStatus.FAILED}:
            run.ended_at = run.started_at
        self.runs.setdefault(session_id, []).append(run)
        self._persist_run(run)
        return run

    def execute_command(self, session_id: str, request: ExecuteCommandRequest) -> CommandRun:
        session = self._require_session(session_id)
        target = self.targets[session.target_id]
        self._validate_command_request(target, request)
        cwd = request.cwd or os.getcwd()
        run = CommandRun(
            session_id=session.id,
            tool=request.tool,
            command=request.command,
            status=RunStatus.RUNNING,
        )
        self.runs.setdefault(session_id, []).append(run)
        self._persist_run(run)
        try:
            completed = subprocess.run(
                request.command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=request.timeout_seconds,
            )
            run.stdout = completed.stdout or ""
            run.stderr = completed.stderr or ""
            run.exit_code = completed.returncode
            run.status = RunStatus.COMPLETE if completed.returncode == 0 else RunStatus.FAILED
        except subprocess.TimeoutExpired as exc:
            run.stdout = exc.stdout or ""
            run.stderr = (exc.stderr or "") + f"\nCommand timed out after {request.timeout_seconds}s"
            run.exit_code = None
            run.status = RunStatus.FAILED
        run.ended_at = run.started_at
        self._persist_run(run)
        parsed_findings = parse_command_output(
            tool=request.tool,
            command=request.command,
            stdout=run.stdout,
            stderr=run.stderr,
        )
        for parsed in parsed_findings:
            self.create_finding(session_id, parsed)
        return run

    async def chat(self, session_id: str, request: CopilotChatRequest) -> CopilotChatResponse:
        session = self._require_session(session_id)
        target = self.targets[session.target_id]
        history = self.messages.setdefault(session_id, [])
        history.append(
            CopilotMessage(
                session_id=session_id,
                role="user",
                provider="operator",
                model="manual",
                content=request.message,
            )
        )
        self._persist_message(history[-1])
        system_prompt, prompt = build_security_copilot_prompt(
            session=session,
            target=target,
            user_message=request.message,
            mode=request.mode,
            findings=self.list_findings(session_id),
            runs=self.list_runs(session_id),
        )
        provider_config = self._build_security_llm_config(session)
        response_text, provider_used = await generate_with_failover(
            provider_config,
            prompt=prompt,
            system_prompt=system_prompt,
        )
        assistant_message = CopilotMessage(
            session_id=session_id,
            role="assistant",
            provider=provider_used,
            model=provider_config.model,
            content=response_text,
        )
        history.append(assistant_message)
        self._persist_message(assistant_message)
        return CopilotChatResponse(
            session=session,
            provider=provider_used,
            model=provider_config.model,
            response=response_text,
            messages=history[-6:],
        )

    def snapshot(self) -> SecurityConsoleSnapshot:
        all_findings = self.list_all_findings()
        all_runs = [item for items in self.runs.values() for item in items]
        return SecurityConsoleSnapshot(
            targets=sorted(self.list_targets(), key=lambda item: item.created_at, reverse=True),
            sessions=self.list_sessions(),
            findings=all_findings,
            runs=sorted(all_runs, key=lambda item: item.started_at, reverse=True),
        )

    def summary(self) -> dict[str, object]:
        findings = self.list_all_findings()
        runs = [item for items in self.runs.values() for item in items]
        return {
            "target_count": len(self.targets),
            "session_count": len(self.sessions),
            "finding_count": len(findings),
            "run_count": len(runs),
            "tools": sorted({item.source_tool for item in findings if item.source_tool}),
        }

    def _require_session(self, session_id: str) -> SecuritySession:
        session = self.sessions.get(session_id)
        if session is None:
            raise KeyError(f"unknown session: {session_id}")
        return session

    def _validate_command_request(self, target: Target, request: ExecuteCommandRequest) -> None:
        tool = request.tool.strip().lower()
        command = request.command.strip()
        if not command:
            raise ValueError("command cannot be empty")

        if target.allowed_tools and tool not in {item.lower() for item in target.allowed_tools}:
            raise ValueError(f"tool '{request.tool}' is not allowed for target '{target.name}'")

        blocked_patterns = [
            r"(^|\s)rm\s+-rf\b",
            r"(^|\s)mkfs\b",
            r"(^|\s)shutdown\b",
            r"(^|\s)reboot\b",
            r"(^|\s)poweroff\b",
            r"(^|\s)dd\s+if=",
            r":\(\)\s*\{",
            r"(^|\s)chmod\s+-R\s+777\b",
        ]
        for pattern in blocked_patterns:
            if re.search(pattern, command):
                raise ValueError("command blocked by security guardrail")

        if target.type == "workspace":
            allowed_workspace_prefixes = (
                "python ",
                "python3 ",
                "rg ",
                "ls ",
                "pwd",
                "find ",
                "cat ",
                "sed ",
                "nmap ",
                "httpx ",
                "nuclei ",
                "ffuf ",
            )
            if not command.startswith(allowed_workspace_prefixes):
                raise ValueError("workspace session only allows local inspection and approved security tooling")
            return

        if tool in {"httpx", "nuclei", "ffuf", "nmap", "curl", "wget"}:
            scope_terms = {
                target.scope.strip(),
                target.name.strip(),
            }
            compact_scope = target.scope.replace("https://", "").replace("http://", "").strip().rstrip("/")
            if compact_scope:
                scope_terms.add(compact_scope)
                scope_terms.add(compact_scope.split("/")[0])
            scope_terms = {term for term in scope_terms if term}
            if not any(term in command for term in scope_terms):
                raise ValueError(
                    "command does not appear scoped to the current target; include the target host or scope explicitly"
                )

    def _load_state(self) -> None:
        if self.store and not self.store.is_empty():
            data = self.store.load_all()
            self._hydrate(data)
            return
        if not self.storage_path.exists():
            return
        data = json.loads(self.storage_path.read_text(encoding="utf-8"))
        self._hydrate(data)
        if self.store:
            self.store.replace_all(
                {
                    "targets": [item.model_dump(mode="json") for item in self.targets.values()],
                    "sessions": [item.model_dump(mode="json") for item in self.sessions.values()],
                    "findings": {
                        session_id: [item.model_dump(mode="json") for item in items]
                        for session_id, items in self.findings.items()
                    },
                    "runs": {
                        session_id: [item.model_dump(mode="json") for item in items]
                        for session_id, items in self.runs.items()
                    },
                    "messages": {
                        session_id: [item.model_dump(mode="json") for item in items]
                        for session_id, items in self.messages.items()
                    },
                }
            )

    def _hydrate(self, data: dict[str, object]) -> None:
        self.targets = {
            item["id"]: Target.model_validate(item)
            for item in data.get("targets", [])
        }
        self.sessions = {
            item["id"]: SecuritySession.model_validate(item)
            for item in data.get("sessions", [])
        }
        self.findings = {
            session_id: [Finding.model_validate(item) for item in items]
            for session_id, items in data.get("findings", {}).items()
        }
        self.runs = {
            session_id: [CommandRun.model_validate(item) for item in items]
            for session_id, items in data.get("runs", {}).items()
        }
        self.messages = {
            session_id: [CopilotMessage.model_validate(item) for item in items]
            for session_id, items in data.get("messages", {}).items()
        }

    def _save_state(self) -> None:
        payload = {
            "targets": [item.model_dump(mode="json") for item in self.targets.values()],
            "sessions": [item.model_dump(mode="json") for item in self.sessions.values()],
            "findings": {
                session_id: [item.model_dump(mode="json") for item in items]
                for session_id, items in self.findings.items()
            },
            "runs": {
                session_id: [item.model_dump(mode="json") for item in items]
                for session_id, items in self.runs.items()
            },
            "messages": {
                session_id: [item.model_dump(mode="json") for item in items]
                for session_id, items in self.messages.items()
            },
        }
        if self.store:
            self.store.replace_all(payload)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _persist_target(self, target: Target) -> None:
        if self.store:
            self.store.upsert_target(target.model_dump(mode="json"))
        self._write_json_snapshot()

    def _persist_session(self, session: SecuritySession) -> None:
        if self.store:
            self.store.upsert_session(session.model_dump(mode="json"))
        self._write_json_snapshot()

    def _persist_finding(self, finding: Finding) -> None:
        if self.store:
            self.store.upsert_finding(finding.session_id, finding.model_dump(mode="json"))
        self._write_json_snapshot()

    def _persist_run(self, run: CommandRun) -> None:
        if self.store:
            self.store.upsert_run(run.session_id, run.model_dump(mode="json"))
        self._write_json_snapshot()

    def _persist_message(self, message: CopilotMessage) -> None:
        if self.store:
            self.store.upsert_message(message.session_id, message.model_dump(mode="json"))
        self._write_json_snapshot()

    def _write_json_snapshot(self) -> None:
        payload = {
            "targets": [item.model_dump(mode="json") for item in self.targets.values()],
            "sessions": [item.model_dump(mode="json") for item in self.sessions.values()],
            "findings": {
                session_id: [item.model_dump(mode="json") for item in items]
                for session_id, items in self.findings.items()
            },
            "runs": {
                session_id: [item.model_dump(mode="json") for item in items]
                for session_id, items in self.runs.items()
            },
            "messages": {
                session_id: [item.model_dump(mode="json") for item in items]
                for session_id, items in self.messages.items()
            },
        }
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _filter_findings(
        self,
        items: list[Finding],
        severity: str | None = None,
        source_tool: str | None = None,
        query: str | None = None,
    ) -> list[Finding]:
        filtered = items
        if severity:
            filtered = [item for item in filtered if item.severity.value == severity]
        if source_tool:
            filtered = [item for item in filtered if item.source_tool.lower() == source_tool.lower()]
        if query:
            needle = query.strip().lower()
            filtered = [
                item
                for item in filtered
                if needle in item.title.lower()
                or needle in item.category.lower()
                or needle in item.source_tool.lower()
                or needle in (item.asset or "").lower()
                or needle in item.evidence_summary.lower()
            ]
        return sorted(filtered, key=lambda item: item.created_at, reverse=True)

    def _build_security_llm_config(self, session: SecuritySession) -> JebatLLMConfig:
        base = load_llm_config()
        provider = session.provider or "ollama"
        if provider != "ollama":
            provider = "ollama"
        model = session.model or "qwen2.5-coder:7b"
        return JebatLLMConfig(
            provider=provider,
            model=model,
            temperature=base.temperature,
            max_tokens=base.max_tokens,
            ollama_host=base.ollama_host,
            fallback_providers=("local",),
            history_path=base.history_path,
        )


_service = SecurityConsoleService()


def get_security_console_service() -> SecurityConsoleService:
    return _service
