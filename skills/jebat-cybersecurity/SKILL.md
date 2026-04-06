---
name: jebat-cybersecurity
description: Defensive cybersecurity workflow for JEBAT. Use when reviewing security posture, auditing configurations, scanning for vulnerabilities, analyzing logs, checking compliance, researching CVEs, or producing remediation-focused security reports.
---

# JEBAT Cybersecurity Skill

Use this skill for **defensive security work**.

## Core workflow
1. classify the request as audit, review, vuln assessment, log analysis, or compliance check
2. inspect local configs, versions, logs, and architecture first
3. use safe diagnostics and external research as needed
4. produce findings with severity, evidence, impact, and remediation
5. hand remediation into hardening workflows when appropriate

## Read references when needed
- `references/audit-patterns.md` — audit focus and output structure

## Operational rules
- defensive by default
- separate audit from exploitation
- never blur authorization boundaries
- recommendations should be practical, not theatrical
