"""
Keris — Sentinel Security Module

Autonomous pentest orchestrator for air-gapped threat reconnaissance
and CVE correlation. Named after the Malay dagger — precise, lethal,
and culturally significant.

Wraps the existing PentestEngine + PentestOrchestrator with
Keris-specific workflows: threat intelligence, CVE correlation,
air-gapped scanning, and executive security briefings.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from jebat.features.pentest.pentest_core import PentestEngine, PentestResult, SCAN_PROFILES
from jebat.features.pentest.pentest_orchestrator import PentestOrchestrator
from jebat.llm.chat_runtime import generate_chat_reply


# ─── Keris Identity ─────────────────────────────────────────────

KERIS_IDENTITY = (
    "You are Keris — the JEBAT Sentinel Security agent. "
    "You are an autonomous pentest orchestrator specializing in "
    "air-gapped threat reconnaissance and CVE correlation. "
    "You analyze scan results, correlate vulnerabilities with CVE databases, "
    "assess risk severity using CVSS scoring, and generate actionable "
    "security briefings with remediation steps. "
    "Be precise, thorough, and prioritize critical findings."
)


# ─── Threat Intelligence ───────────────────────────────────────

@dataclass
class ThreatFinding:
    """A single threat finding from reconnaissance."""
    finding_id: str
    title: str
    severity: str  # critical, high, medium, low, info
    cvss_score: float | None = None
    cve_ids: list[str] = field(default_factory=list)
    description: str = ""
    affected_component: str = ""
    remediation: str = ""
    references: list[str] = field(default_factory=list)
    discovered_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def risk_level(self) -> str:
        if self.cvss_score and self.cvss_score >= 9.0:
            return "CRITICAL"
        elif self.cvss_score and self.cvss_score >= 7.0:
            return "HIGH"
        elif self.cvss_score and self.cvss_score >= 4.0:
            return "MEDIUM"
        elif self.cvss_score and self.cvss_score >= 0.1:
            return "LOW"
        return "INFO"


@dataclass
class SecurityBriefing:
    """Executive security briefing from a pentest engagement."""
    briefing_id: str
    target: str
    scan_date: str
    findings: list[ThreatFinding]
    overall_risk: str
    executive_summary: str
    recommendations: list[str]
    scan_metadata: dict[str, Any] = field(default_factory=dict)
    provider: str = ""


# ─── Keris Store ────────────────────────────────────────────────

class KerisStore:
    """Persistent storage for Keris scan results and briefings."""

    def __init__(self, data_dir: str | Path | None = None) -> None:
        self.data_dir = Path(data_dir or "~/.jebat/sentinel").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.scans_file = self.data_dir / "scans.jsonl"
        self.briefings_file = self.data_dir / "briefings.jsonl"

    def save_scan(self, result: PentestResult) -> None:
        """Save scan result."""
        record = {
            "target": result.target,
            "scan_type": result.scan_type,
            "start_time": result.start_time,
            "end_time": result.end_time,
            "duration_seconds": result.duration_seconds,
            "severity": result.severity,
            "score": result.score,
            "vulnerabilities": result.vulnerabilities,
            "cve_findings": result.cve_findings,
            "summary": result.summary,
        }
        with self.scans_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def save_briefing(self, briefing: SecurityBriefing) -> None:
        """Save security briefing."""
        record = {
            "briefing_id": briefing.briefing_id,
            "target": briefing.target,
            "scan_date": briefing.scan_date,
            "overall_risk": briefing.overall_risk,
            "executive_summary": briefing.executive_summary,
            "recommendations": briefing.recommendations,
            "finding_count": len(briefing.findings),
            "provider": briefing.provider,
        }
        with self.briefings_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def get_scan_history(self, limit: int = 20) -> list[dict]:
        """Load recent scan history."""
        if not self.scans_file.exists():
            return []
        scans = []
        for line in self.scans_file.read_text(encoding="utf-8").splitlines():
            if line.strip():
                scans.append(json.loads(line))
        return scans[-limit:]

    def get_briefing_history(self, limit: int = 10) -> list[dict]:
        """Load recent briefings."""
        if not self.briefings_file.exists():
            return []
        briefings = []
        for line in self.briefings_file.read_text(encoding="utf-8").splitlines():
            if line.strip():
                briefings.append(json.loads(line))
        return briefings[-limit:]


# ─── Keris Engine ───────────────────────────────────────────────

class KerisSentinel:
    """
    Keris — Autonomous Pentest Orchestrator.

    Combines PentestEngine scanning with LLM-driven analysis,
    CVE correlation, and executive security briefings.
    """

    def __init__(
        self,
        data_dir: str | Path | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> None:
        self.store = KerisStore(data_dir=data_dir)
        self.pentest = PentestEngine()
        self.orchestrator = PentestOrchestrator()
        self.provider = provider
        self.model = model

    async def scan(
        self,
        target: str,
        profile: str = "standard",
        use_orchestrator: bool = True,
    ) -> tuple[PentestResult, str]:
        """
        Run a pentest scan against a target.

        Args:
            target: Domain or IP to scan
            profile: Scan profile (quick, standard, full, vuln)
            use_orchestrator: Use swarm orchestration for deeper analysis

        Returns:
            Tuple of (PentestResult, used_provider)
        """
        if profile not in SCAN_PROFILES:
            raise ValueError(f"Unknown profile: {profile}. Available: {list(SCAN_PROFILES.keys())}")

        if use_orchestrator:
            result = await self.orchestrator.run_orchestrated_scan(target, profile)
        else:
            result = await self.pentest.run_scan(target, profile)

        # Save scan
        self.store.save_scan(result)

        return result, ""

    async def analyze(
        self,
        result: PentestResult,
    ) -> tuple[SecurityBriefing, str]:
        """
        Analyze scan results and generate a security briefing.

        Args:
            result: PentestResult from a completed scan

        Returns:
            Tuple of (SecurityBriefing, used_provider)
        """
        # Build analysis prompt
        findings_text = ""
        if result.vulnerabilities:
            for i, vuln in enumerate(result.vulnerabilities[:20], 1):
                findings_text += f"  {i}. {vuln.get('title', 'Unknown')} [{vuln.get('severity', 'unknown')}]\n"
                if vuln.get("cve"):
                    findings_text += f"     CVE: {vuln['cve']}\n"
                if vuln.get("description"):
                    findings_text += f"     {vuln['description'][:200]}\n"

        if result.cve_findings:
            findings_text += "\nCVE Correlations:\n"
            for cve in result.cve_findings[:10]:
                findings_text += f"  - {cve.get('id', 'N/A')}: {cve.get('description', 'N/A')[:150]}\n"

        prompt = f"""Analyze this pentest result for {result.target} and generate a security briefing.

Scan Type: {result.scan_type}
Duration: {result.duration_seconds:.0f}s
Overall Score: {result.score}/100
Severity: {result.severity}

Findings:
{findings_text if findings_text else "No specific vulnerabilities found."}

Nmap Results:
{json.dumps(result.nmap_result, indent=2)[:1000] if result.nmap_result else "N/A"}

SSL Results:
{json.dumps(result.ssl_result, indent=2)[:500] if result.ssl_result else "N/A"}

Generate a security briefing with:
1. Executive Summary (2-3 sentences, risk level)
2. Critical/High Findings (top 5 with CVE IDs if any)
3. Remediation Priorities (ordered by risk)
4. Compliance Notes (OWASP Top 10 mapping if applicable)
5. Overall Risk Assessment (CRITICAL/HIGH/MEDIUM/LOW)

Be specific about CVE IDs and CVSS scores where available."""

        response_text, used_provider, _ = await generate_chat_reply(
            prompt=prompt,
            preset="default",
            provider_override=self.provider,
            model_override=self.model,
            system_prompt_override=KERIS_IDENTITY,
        )

        # Parse findings
        findings = []
        for i, vuln in enumerate(result.vulnerabilities[:20]):
            findings.append(ThreatFinding(
                finding_id=f"find-{uuid.uuid4().hex[:8]}",
                title=vuln.get("title", f"Finding {i+1}"),
                severity=vuln.get("severity", "info"),
                cvss_score=vuln.get("cvss_score"),
                cve_ids=[vuln["cve"]] if vuln.get("cve") else [],
                description=vuln.get("description", ""),
                affected_component=vuln.get("component", ""),
            ))

        # Determine overall risk
        risk = "LOW"
        if any(f.severity == "critical" for f in findings):
            risk = "CRITICAL"
        elif any(f.severity == "high" for f in findings):
            risk = "HIGH"
        elif any(f.severity == "medium" for f in findings):
            risk = "MEDIUM"

        # Extract recommendations
        recommendations = []
        for line in response_text.split("\n"):
            line = line.strip()
            if line.startswith("- ") or line.startswith("• "):
                rec = line.lstrip("- •").strip()
                if rec and len(rec) > 10:
                    recommendations.append(rec)

        briefing = SecurityBriefing(
            briefing_id=f"brief-{uuid.uuid4().hex[:8]}",
            target=result.target,
            scan_date=result.end_time,
            findings=findings,
            overall_risk=risk,
            executive_summary=response_text[:500],
            recommendations=recommendations[:10],
            scan_metadata={
                "profile": result.scan_type,
                "duration": result.duration_seconds,
                "score": result.score,
            },
            provider=used_provider,
        )

        self.store.save_briefing(briefing)

        return briefing, used_provider

    async def quick_assessment(self, target: str) -> tuple[SecurityBriefing, str]:
        """
        Quick security assessment — fast scan + analysis.
        Returns a briefing in under 60 seconds.
        """
        result, _ = await self.scan(target, profile="quick", use_orchestrator=False)
        briefing, provider = await self.analyze(result)
        return briefing, provider

    def get_history(self, limit: int = 10) -> dict[str, Any]:
        """Get scan and briefing history."""
        return {
            "scans": self.store.get_scan_history(limit),
            "briefings": self.store.get_briefing_history(limit),
        }

    def format_briefing(self, briefing: SecurityBriefing) -> str:
        """Format a security briefing for display."""
        severity_colors = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢",
            "INFO": "🔵",
        }

        lines = [
            f"🛡️  KERIS Security Briefing",
            f"   Target: {briefing.target}",
            f"   Date: {briefing.scan_date[:10]}",
            f"   Risk: {severity_colors.get(briefing.overall_risk, '⚪')} {briefing.overall_risk}",
            f"   Findings: {len(briefing.findings)}",
            "",
            "Executive Summary:",
            briefing.executive_summary,
            "",
        ]

        if briefing.findings:
            lines.append("Top Findings:")
            for finding in briefing.findings[:10]:
                icon = severity_colors.get(finding.severity, "⚪")
                cve = f" ({', '.join(finding.cve_ids)})" if finding.cve_ids else ""
                cvss = f" CVSS:{finding.cvss_score}" if finding.cvss_score else ""
                lines.append(f"  {icon} {finding.title}{cve}{cvss}")
            lines.append("")

        if briefing.recommendations:
            lines.append("Recommendations:")
            for rec in briefing.recommendations[:5]:
                lines.append(f"  → {rec}")

        return "\n".join(lines)


# ─── CLI Entry Point ────────────────────────────────────────────

def main():
    """CLI entry point for Keris Sentinel."""
    import asyncio

    print("\n🛡️  Keris — Sentinel Security")
    print("   Autonomous Pentest Orchestrator")
    print("   Type 'quit' to exit\n")

    sentinel = KerisSentinel()

    async def run():
        while True:
            try:
                target = input("Target: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n👋 Shutting down Keris.")
                break

            if not target:
                continue
            if target.lower() in ("quit", "exit", "q"):
                print("\n👋 Shutting down Keris.")
                break
            if target.lower() == "history":
                history = sentinel.get_history(5)
                print(f"\n📜 Recent scans: {len(history['scans'])}")
                for s in history["scans"]:
                    print(f"   [{s['severity']}] {s['target']} ({s['scan_type']})")
                continue

            print(f"\n🔍 Scanning {target}...\n")
            result, _ = await sentinel.scan(target, profile="quick", use_orchestrator=False)
            print(f"   Scan complete: {result.severity} (score: {result.score}/100)")

            print(f"\n📊 Analyzing results...\n")
            briefing, provider = await sentinel.analyze(result)
            print(sentinel.format_briefing(briefing))

    asyncio.run(run())


if __name__ == "__main__":
    main()
