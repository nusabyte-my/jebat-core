from __future__ import annotations

from .models import CommandRun, Finding, SecuritySession, Target


def build_security_copilot_prompt(
    session: SecuritySession,
    target: Target,
    user_message: str,
    mode: str,
    findings: list[Finding],
    runs: list[CommandRun],
) -> tuple[str, str]:
    finding_lines = [
        f"- {finding.severity.value.upper()}: {finding.title} ({finding.category})"
        for finding in findings[:8]
    ] or ["- No findings recorded yet."]
    run_lines = [
        f"- {run.tool}: {run.command} [status={run.status.value} exit={run.exit_code}]"
        for run in runs[:8]
    ] or ["- No command runs recorded yet."]

    system_prompt = (
        "You are JEBAT Serangan Copilot operating in a cybersecurity console. "
        "Default to Ollama-local reasoning, be concise, and never claim to have executed "
        "commands yourself. Recommend next steps, triage findings, and explain risk in "
        "operator language. Do not encourage out-of-scope or destructive actions."
    )
    prompt = (
        f"Mode: {mode}\n"
        f"Session: {session.id}\n"
        f"Target: {target.name} ({target.type.value})\n"
        f"Scope: {target.scope}\n"
        f"Engagement mode: {target.engagement_mode}\n"
        f"Allowed tools: {', '.join(target.allowed_tools) or 'not specified'}\n\n"
        f"Recent findings:\n{chr(10).join(finding_lines)}\n\n"
        f"Recent command runs:\n{chr(10).join(run_lines)}\n\n"
        f"Operator request:\n{user_message}\n\n"
        "Return a concise answer with:\n"
        "1. assessment\n"
        "2. next commands or checks\n"
        "3. cautions\n"
    )
    return system_prompt, prompt
