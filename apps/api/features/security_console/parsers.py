from __future__ import annotations

import json
import re
from typing import Iterable

from .models import CreateFindingRequest, Severity


def parse_command_output(tool: str, command: str, stdout: str, stderr: str) -> list[CreateFindingRequest]:
    combined = "\n".join(part for part in [stdout, stderr] if part).strip()
    if not combined:
        return []

    lowered_tool = tool.lower()
    findings: list[CreateFindingRequest] = []
    if lowered_tool in {"nmap", "network"}:
        findings.extend(_parse_nmap_output(command, combined))
    if lowered_tool in {"httpx", "web"}:
        findings.extend(_parse_httpx_output(combined))
    if lowered_tool in {"nuclei", "vuln"}:
        findings.extend(_parse_nuclei_output(combined))
    if lowered_tool in {"ffuf", "content"}:
        findings.extend(_parse_ffuf_output(combined))
    if lowered_tool in {"serangan", "scanner", "security-autonomous-scan"}:
        findings.extend(_parse_serangan_report(combined))
    return _dedupe_findings(findings)


def _parse_nmap_output(command: str, text: str) -> list[CreateFindingRequest]:
    findings: list[CreateFindingRequest] = []
    host_match = re.search(r"Nmap scan report for\s+(.+)", text)
    asset = host_match.group(1).strip() if host_match else None
    for match in re.finditer(r"(?m)^(\d+)/(tcp|udp)\s+open\s+([^\s]+)", text):
        port, protocol, service = match.groups()
        severity = Severity.INFO
        if service in {"ssh", "redis", "mongodb", "mysql", "postgresql"}:
            severity = Severity.MEDIUM
        findings.append(
            CreateFindingRequest(
                title=f"Open {protocol.upper()} port {port} running {service}",
                severity=severity,
                confidence=0.92,
                category="network-exposure",
                asset=asset,
                evidence_summary=f"Detected from nmap output for command: {command}",
                remediation="Confirm the service is expected, restricted, and not internet-exposed beyond scope.",
                source_tool="nmap",
                metadata={
                    "protocol": protocol,
                    "port": int(port),
                    "service": service,
                    "parser": "nmap-text",
                },
            )
        )
    return findings


def _parse_httpx_output(text: str) -> list[CreateFindingRequest]:
    json_findings = _parse_httpx_json_output(text)
    if json_findings:
        return json_findings
    findings: list[CreateFindingRequest] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        status_match = re.search(r"\[(\d{3})\]", line)
        if not status_match:
            continue
        status_code = int(status_match.group(1))
        if status_code >= 400:
            continue
        tech = ", ".join(re.findall(r"\[([A-Za-z0-9._ -]+)\]", line)[1:])
        findings.append(
            CreateFindingRequest(
                title=f"Reachable HTTP surface returned {status_code}",
                severity=Severity.INFO,
                confidence=0.75,
                category="web-surface",
                evidence_summary=line[:400],
                remediation="Validate exposed hosts and remove unintended public endpoints.",
                source_tool="httpx",
                asset=line.split()[0],
                metadata={
                    "status_code": status_code,
                    "parser": "httpx-text",
                },
            )
        )
        if tech:
            findings.append(
                CreateFindingRequest(
                    title=f"Technology fingerprint identified: {tech}",
                    severity=Severity.LOW,
                    confidence=0.62,
                    category="fingerprint",
                    evidence_summary=line[:400],
                    remediation="Review whether version or stack disclosure is acceptable for this target.",
                    source_tool="httpx",
                    asset=line.split()[0],
                    metadata={
                        "technologies": tech.split(", "),
                        "status_code": status_code,
                        "parser": "httpx-text",
                    },
                )
            )
    return findings


def _parse_nuclei_output(text: str) -> list[CreateFindingRequest]:
    findings: list[CreateFindingRequest] = []
    severity_map = {
        "critical": Severity.CRITICAL,
        "high": Severity.HIGH,
        "medium": Severity.MEDIUM,
        "low": Severity.LOW,
        "info": Severity.INFO,
    }
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("{"):
            try:
                findings.extend(_nuclei_json_findings(json.loads(line), severity_map))
            except json.JSONDecodeError:
                continue
            continue
        match = re.search(r"\[([a-z]+)\]\s+\[([^\]]+)\]\s+\[([^\]]+)\]\s+(.+)", line, re.IGNORECASE)
        if match:
            severity_name, template_id, matcher_name, asset = match.groups()
            findings.append(
                CreateFindingRequest(
                    title=f"Nuclei match: {template_id}",
                    severity=severity_map.get(severity_name.lower(), Severity.MEDIUM),
                    confidence=0.88,
                    category="template-match",
                    asset=asset,
                    evidence_summary=f"Matcher {matcher_name} reported: {line[:300]}",
                    remediation="Verify impact and patch or restrict the exposed target.",
                    source_tool="nuclei",
                    metadata={
                        "template_id": template_id,
                        "matcher_name": matcher_name,
                        "parser": "nuclei-text",
                    },
                )
            )
    return findings


def _parse_ffuf_output(text: str) -> list[CreateFindingRequest]:
    json_findings = _parse_ffuf_json_output(text)
    if json_findings:
        return json_findings
    findings: list[CreateFindingRequest] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or "::" not in line:
            continue
        status_match = re.search(r"Status:\s*(\d{3})", line)
        size_match = re.search(r"Size:\s*(\d+)", line)
        path = line.split()[0]
        status_code = int(status_match.group(1)) if status_match else 0
        if status_code and status_code not in {200, 204, 301, 302, 307, 401, 403}:
            continue
        severity = Severity.MEDIUM if status_code in {200, 204} else Severity.LOW
        findings.append(
            CreateFindingRequest(
                title=f"Discovered content path {path}",
                severity=severity,
                confidence=0.82,
                category="content-discovery",
                asset=path,
                evidence_summary=f"{line[:400]} size={size_match.group(1) if size_match else 'unknown'}",
                remediation="Review whether this path should be accessible and enforce auth or removal if not needed.",
                source_tool="ffuf",
                metadata={
                    "status_code": status_code,
                    "size": int(size_match.group(1)) if size_match else None,
                    "path": path,
                    "parser": "ffuf-text",
                },
            )
        )
    return findings


def _parse_serangan_report(text: str) -> list[CreateFindingRequest]:
    findings: list[CreateFindingRequest] = []
    for match in re.finditer(r"\|\s*[🔴🟠🟡🟢]?\s*(Critical|High|Medium|Low)\s*\|\s*(\d+)\s*\|", text, re.IGNORECASE):
        severity_name, count = match.groups()
        if int(count) <= 0:
            continue
        severity = {
            "critical": Severity.CRITICAL,
            "high": Severity.HIGH,
            "medium": Severity.MEDIUM,
            "low": Severity.LOW,
        }[severity_name.lower()]
        findings.append(
            CreateFindingRequest(
                title=f"Serangan report recorded {count} {severity_name.lower()} findings",
                severity=severity,
                confidence=0.95,
                category="workspace-scan",
                evidence_summary=f"Summary row from Serangan report: {severity_name}={count}",
                remediation="Inspect the underlying report entries and create targeted remediation tasks.",
                source_tool="serangan",
                metadata={
                    "count": int(count),
                    "parser": "serangan-report",
                },
            )
        )
    issue_pattern = re.compile(r"(?m)^\|\s*([^|]+)\s*\|\s*(\d+)\s*\|\s*([^|]+)\s*\|\s*(CRITICAL|HIGH|MEDIUM|LOW)\s*\|")
    for file_path, line_no, issue, severity_name in issue_pattern.findall(text):
        findings.append(
            CreateFindingRequest(
                title=issue.strip(),
                severity=Severity(severity_name.lower()),
                confidence=0.9,
                category="workspace-scan",
                asset=file_path.strip(),
                evidence_summary=f"Reported at line {line_no}",
                remediation="Review the flagged file and patch the vulnerable pattern or secret exposure.",
                source_tool="serangan",
                metadata={
                    "line": int(line_no),
                    "parser": "serangan-report",
                },
            )
        )
    return findings


def _dedupe_findings(findings: Iterable[CreateFindingRequest]) -> list[CreateFindingRequest]:
    deduped: list[CreateFindingRequest] = []
    seen: set[tuple[str, str, str]] = set()
    for finding in findings:
        key = (finding.title, finding.asset or "", finding.source_tool)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(finding)
    return deduped


def _parse_httpx_json_output(text: str) -> list[CreateFindingRequest]:
    findings: list[CreateFindingRequest] = []
    for item in _iter_json_objects(text):
        url = str(item.get("url") or item.get("input") or "").strip()
        if not url:
            continue
        status_code = int(item.get("status_code") or 0)
        if status_code and status_code < 400:
            findings.append(
                CreateFindingRequest(
                    title=f"Reachable HTTP surface returned {status_code}",
                    severity=Severity.INFO,
                    confidence=0.82,
                    category="web-surface",
                    asset=url,
                    evidence_summary=f"title={item.get('title', '')} webserver={item.get('webserver', '')}".strip(),
                    remediation="Validate exposed hosts and remove unintended public endpoints.",
                    source_tool="httpx",
                    metadata={
                        "status_code": status_code,
                        "title": item.get("title"),
                        "webserver": item.get("webserver"),
                        "scheme": item.get("scheme"),
                        "port": item.get("port"),
                        "parser": "httpx-json",
                    },
                )
            )
        technologies = item.get("tech") or item.get("technologies") or []
        if isinstance(technologies, list) and technologies:
            findings.append(
                CreateFindingRequest(
                    title=f"Technology fingerprint identified: {', '.join(str(t) for t in technologies)}",
                    severity=Severity.LOW,
                    confidence=0.74,
                    category="fingerprint",
                    asset=url,
                    evidence_summary=f"status={status_code} title={item.get('title', '')}".strip(),
                    remediation="Review whether version or stack disclosure is acceptable for this target.",
                    source_tool="httpx",
                    metadata={
                        "technologies": [str(t) for t in technologies],
                        "status_code": status_code,
                        "webserver": item.get("webserver"),
                        "parser": "httpx-json",
                    },
                )
            )
    return findings


def _parse_ffuf_json_output(text: str) -> list[CreateFindingRequest]:
    findings: list[CreateFindingRequest] = []
    for item in _iter_json_objects(text, ffuf_results_key="results"):
        url = str(item.get("url") or item.get("input") or "").strip()
        path = str(item.get("input") or item.get("path") or url).strip()
        status_code = int(item.get("status") or item.get("status_code") or 0)
        if status_code and status_code not in {200, 204, 301, 302, 307, 401, 403}:
            continue
        severity = Severity.MEDIUM if status_code in {200, 204} else Severity.LOW
        findings.append(
            CreateFindingRequest(
                title=f"Discovered content path {path}",
                severity=severity,
                confidence=0.88,
                category="content-discovery",
                asset=url or path,
                evidence_summary=f"status={status_code} words={item.get('words')} lines={item.get('lines')} length={item.get('length')}",
                remediation="Review whether this path should be accessible and enforce auth or removal if not needed.",
                source_tool="ffuf",
                metadata={
                    "status_code": status_code,
                    "words": item.get("words"),
                    "lines": item.get("lines"),
                    "length": item.get("length"),
                    "path": path,
                    "parser": "ffuf-json",
                },
            )
        )
    return findings


def _nuclei_json_findings(data: dict, severity_map: dict[str, Severity]) -> list[CreateFindingRequest]:
    info = data.get("info", {})
    severity = severity_map.get(str(info.get("severity", "medium")).lower(), Severity.MEDIUM)
    return [
        CreateFindingRequest(
            title=str(info.get("name", data.get("template-id", "Nuclei finding"))),
            severity=severity,
            confidence=0.9,
            category="template-match",
            asset=str(data.get("host") or data.get("matched-at") or ""),
            evidence_summary=str(data.get("matcher-name") or data.get("matched-at") or data.get("template-id") or "")[:400],
            remediation="Validate the matched template result and patch the affected surface.",
            source_tool="nuclei",
            metadata={
                "template_id": data.get("template-id"),
                "matcher_name": data.get("matcher-name"),
                "matched_at": data.get("matched-at"),
                "host": data.get("host"),
                "parser": "nuclei-json",
            },
        )
    ]


def _iter_json_objects(text: str, ffuf_results_key: str | None = None) -> list[dict]:
    stripped = text.strip()
    if not stripped:
        return []
    objects: list[dict] = []
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        if ffuf_results_key and isinstance(parsed.get(ffuf_results_key), list):
            objects.extend(item for item in parsed[ffuf_results_key] if isinstance(item, dict))
        else:
            objects.append(parsed)
        return objects
    if isinstance(parsed, list):
        objects.extend(item for item in parsed if isinstance(item, dict))
        return objects
    for line in stripped.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            objects.append(item)
    return objects
