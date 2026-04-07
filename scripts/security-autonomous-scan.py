#!/usr/bin/env python3
"""
Serangan Autonomous — JEBAT Codebase Security Scanner
Adapted from IBM/agentic-ai-cyberres + raphabot/awesome-cybersecurity-agentic-ai

Runs on JEBAT session startup to scan the entire codebase for vulnerabilities.
"""

import os
import re
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────

WORKSPACE = os.environ.get("JEBAT_WORKSPACE", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORT_DIR = os.path.join(WORKSPACE, "security", "scan-reports")
EXCLUDED_DIRS = {"node_modules", ".next", "out", ".git", "jebat-core", ".claude", ".gemini", "__pycache__"}
EXCLUDED_FILES = {"package-lock.json", "yarn.lock", "Pipfile.lock"}

# Secret patterns (from IBM agentic-ai-cyberres adapted patterns)
SECRET_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']([A-Za-z0-9_\-]{16,})["\']', "API Key"),
    (r'(?i)(secret|secret[_-]?key)\s*[:=]\s*["\']([A-Za-z0-9_\-]{16,})["\']', "Secret Key"),
    (r'(?i)(password|passwd|pwd)\s*[:=]\s*["\'](.{4,})["\']', "Password"),
    (r'(?i)(token|auth[_-]?token|access[_-]?token)\s*[:=]\s*["\']([A-Za-z0-9_\-\.]{16,})["\']', "Token"),
    (r'AKIA[0-9A-Z]{16}', "AWS Access Key"),
    (r'ghp_[A-Za-z0-9]{36}', "GitHub Personal Token"),
    (r'sk-[A-Za-z0-9]{32,}', "OpenAI/Anthropic Key"),
    (r'(?i)private[_-]?key\s*[:=]\s*["\'](.{16,})["\']', "Private Key"),
]

# Security vulnerability patterns
SECURITY_PATTERNS = [
    # SQL Injection
    (r'(?i)(execute|query|cursor\.execute)\s*\(\s*["\'].*%s.*["\']\s*,', "SQL Injection Risk", "HIGH"),
    (r'(?i)(execute|query)\s*\(\s*f["\']', "SQL Injection Risk (f-string)", "HIGH"),

    # Command Injection
    (r'(?i)(subprocess\.(call|run|Popen|os\.system|os\.popen))\s*\(.*shell\s*=\s*True', "Command Injection Risk", "CRITICAL"),
    (r'(?i)os\.system\s*\(', "Command Injection Risk (os.system)", "HIGH"),

    # Path Traversal
    (r'(?i)open\s*\(\s*(?:os\.path\.)?join\s*\(.*request\.|input\(|params\[', "Path Traversal Risk", "MEDIUM"),

    # SSRF
    (r'(?i)(requests\.get|requests\.post|urllib\.request)\s*\(\s*(?!["\']https?://)', "SSRF Risk", "MEDIUM"),

    # XSS
    (r'(?i)innerHTML\s*=\s*(?!["\'])', "XSS Risk", "HIGH"),
    (r'(?i)dangerouslySetInnerHTML', "XSS Risk (React)", "MEDIUM"),

    # Deserialization
    (r'(?i)pickle\.loads?\s*\(', "Unsafe Deserialization", "CRITICAL"),
    (r'(?i)yaml\.load\s*\([^,)]+\s*\)', "Unsafe YAML Load", "HIGH"),
    (r'(?i)eval\s*\(', "Code Injection via # TODO: Replace eval() with safe alternative
# eval()", "CRITICAL"),
    (r'(?i)exec\s*\(', "Code Injection via # TODO: Replace exec() with safe alternative
# exec()", "CRITICAL"),

    # Weak Crypto
    (r'(?i)hashlib\.md5\s*\(', "Weak Hash (MD5)", "MEDIUM"),
    (r'(?i)hashlib\.sha1\s*\(', "Weak Hash (SHA1)", "LOW"),
]

# ─── Scanners ─────────────────────────────────────────────────────────────────

def find_files(root, extensions):
    """Find all files with given extensions, excluding specified dirs."""
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Exclude dirs
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for f in filenames:
            if f in EXCLUDED_FILES:
                continue
            if any(f.endswith(ext) for ext in extensions):
                files.append(os.path.join(dirpath, f))
    return files


def scan_secrets(files):
    """Scan for exposed secrets and credentials."""
    findings = []
    for filepath in files:
        try:
            with open(filepath, "r", errors="ignore") as fh:
                for line_num, line in enumerate(fh, 1):
                    for pattern, name in SECRET_PATTERNS:
                        if re.search(pattern, line):
                            rel_path = os.path.relpath(filepath, WORKSPACE)
                            findings.append({
                                "file": rel_path,
                                "line": line_num,
                                "issue": f"Exposed {name}",
                                "severity": "CRITICAL" if any(k in name for k in ["AWS", "GitHub", "OpenAI", "Private Key"]) else "HIGH",
                            })
        except (PermissionError, UnicodeDecodeError):
            pass
    return findings


def scan_code_patterns(files):
    """Scan for security vulnerability patterns in code."""
    findings = []
    for filepath in files:
        try:
            with open(filepath, "r", errors="ignore") as fh:
                for line_num, line in enumerate(fh, 1):
                    for pattern, name, severity in SECURITY_PATTERNS:
                        if re.search(pattern, line):
                            rel_path = os.path.relpath(filepath, WORKSPACE)
                            findings.append({
                                "file": rel_path,
                                "line": line_num,
                                "issue": name,
                                "severity": severity,
                            })
        except (PermissionError, UnicodeDecodeError):
            pass
    return findings


def scan_dependencies():
    """Check for known vulnerable dependencies."""
    findings = []

    # npm audit
    try:
        result = subprocess.run(
            ["npm", "audit", "--json"],
            capture_output=True, text=True, cwd=WORKSPACE, timeout=60
        )
        if result.returncode != 0:
            data = json.loads(result.stdout)
            vulnerabilities = data.get("vulnerabilities", {})
            for pkg, vuln in vulnerabilities.items():
                severity = vuln.get("severity", "medium").upper()
                findings.append({
                    "file": "package.json",
                    "line": 0,
                    "issue": f"Vulnerable dependency: {pkg} ({vuln.get('title', vuln.get('via', 'unknown'))})",
                    "severity": severity if severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW") else "MEDIUM",
                })
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass

    # pip-audit
    try:
        result = subprocess.run(
            ["pip-audit", "--format", "json"],
            capture_output=True, text=True, cwd=WORKSPACE, timeout=120
        )
        if result.stdout.strip():
            data = json.loads(result.stdout)
            for vuln in data:
                findings.append({
                    "file": "requirements.txt",
                    "line": 0,
                    "issue": f"Vulnerable dependency: {vuln.get('name', 'unknown')} — {vuln.get('id', 'unknown')}",
                    "severity": "HIGH",
                })
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass

    return findings


def scan_infrastructure():
    """Check infrastructure configs for security issues."""
    findings = []

    # Docker compose checks
    compose_path = os.path.join(WORKSPACE, "docker-compose.yml")
    if os.path.exists(compose_path):
        with open(compose_path) as f:
            content = f.read()
        if "privileged: true" in content:
            findings.append({"file": "docker-compose.yml", "line": 0, "issue": "Container running in privileged mode", "severity": "HIGH"})
        if "network_mode: host" in content:
            findings.append({"file": "docker-compose.yml", "line": 0, "issue": "Container using host network", "severity": "MEDIUM"})

    # Nginx checks
    nginx_path = "/etc/nginx/sites-enabled/jebat.online"
    if os.path.exists(nginx_path):
        with open(nginx_path) as f:
            content = f.read()
        if "autoindex on" in content:
            findings.append({"file": "nginx config", "line": 0, "issue": "Directory listing enabled", "severity": "MEDIUM"})
        if "server_tokens on" in content:
            findings.append({"file": "nginx config", "line": 0, "issue": "Server version exposed", "severity": "LOW"})

    return findings


# ─── Report ────────────────────────────────────────────────────────────────────

def generate_report(all_findings):
    """Generate a markdown security report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    sorted_findings = sorted(all_findings, key=lambda x: severity_order.get(x["severity"], 4))

    counts = {}
    for f in sorted_findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1

    total_files = sum(len(find_files(WORKSPACE, exts)) for exts in [
        (".py", ".js", ".ts", ".tsx", ".jsx"),
        (".json", ".yml", ".yaml", ".toml", ".env"),
        (".md",),
    ])

    # Determine overall risk
    if counts.get("CRITICAL", 0) > 0:
        risk = "CRITICAL"
    elif counts.get("HIGH", 0) > 2:
        risk = "HIGH"
    elif counts.get("MEDIUM", 0) > 5:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    report = f"""# 🔒 JEBAT Security Scan Report

**Date:** {timestamp}
**Scope:** Full workspace codebase ({WORKSPACE})
**Scanner:** Serangan Autonomous Agent (adapted from IBM agentic-ai-cyberres)
**Files Scanned:** ~{total_files}
**Tool Catalog:** [awesome-cybersecurity-agentic-ai](https://github.com/raphabot/awesome-cybersecurity-agentic-ai)

## Executive Summary

| Severity | Count |
|----------|-------|
| 🔴 Critical | {counts.get("CRITICAL", 0)} |
| 🟠 High | {counts.get("HIGH", 0)} |
| 🟡 Medium | {counts.get("MEDIUM", 0)} |
| 🟢 Low | {counts.get("LOW", 0)} |
| **Total** | **{len(sorted_findings)}** |

**Overall Risk Level: {risk}**

"""

    # Group by severity
    for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        items = [f for f in sorted_findings if f["severity"] == severity]
        if not items:
            continue
        report += f"\n## {severity} Issues\n\n"
        report += "| File | Line | Issue |\n|------|------|-------|\n"
        for item in items:
            report += f"| `{item['file']}` | {item['line']} | {item['issue']} |\n"

    report += f"""
## Recommendations

"""
    if counts.get("CRITICAL", 0) > 0:
        report += "1. **IMMEDIATE:** Remove all exposed secrets, keys, and tokens from tracked files\n"
    if counts.get("HIGH", 0) > 0:
        report += "2. **URGENT:** Fix command injection, SQL injection, and unsafe eval/exec patterns\n"
    if counts.get("MEDIUM", 0) > 0:
        report += "3. **RECOMMENDED:** Address SSRF, path traversal, and weak crypto patterns\n"
    report += "4. **ONGOING:** Run this scan on every session startup and before every commit\n"

    return report


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("⚔️  Serangan Autonomous — Security Scan Starting...")
    print(f"   Workspace: {WORKSPACE}")

    # Phase 1: Secret detection
    print("\n[1/4] Scanning for exposed secrets...")
    code_files = find_files(WORKSPACE, (".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yml", ".yaml", ".toml", ".env", ".sh"))
    secrets = scan_secrets(code_files)
    print(f"   Found {len(secrets)} potential secret exposures")

    # Phase 2: Code patterns
    print("\n[2/4] Scanning for vulnerability patterns...")
    code_patterns = scan_code_patterns(code_files)
    print(f"   Found {len(code_patterns)} code vulnerability patterns")

    # Phase 3: Dependencies
    print("\n[3/4] Checking dependencies...")
    deps = scan_dependencies()
    print(f"   Found {len(deps)} dependency vulnerabilities")

    # Phase 4: Infrastructure
    print("\n[4/4] Checking infrastructure configs...")
    infra = scan_infrastructure()
    print(f"   Found {len(infra)} infrastructure issues")

    # Combine and report
    all_findings = secrets + code_patterns + deps + infra
    report = generate_report(all_findings)

    # Save report
    os.makedirs(REPORT_DIR, exist_ok=True)
    report_file = os.path.join(REPORT_DIR, f"scan-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md")
    with open(report_file, "w") as f:
        f.write(report)

    print(f"\n🔒 Scan complete. Report saved to: {report_file}")

    # Summary
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    counts = {}
    for finding in all_findings:
        counts[finding["severity"]] = counts.get(finding["severity"], 0) + 1

    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if counts.get(sev, 0) > 0:
            emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(sev, "")
            print(f"   {emoji} {sev}: {counts[sev]}")

    if not all_findings:
        print("   ✅ No issues found. Codebase looks clean!")

    return 0 if not counts.get("CRITICAL", 0) else 1


if __name__ == "__main__":
    sys.exit(main())
