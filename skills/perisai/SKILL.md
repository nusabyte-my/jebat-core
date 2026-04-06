# Perisai — Defensive Security Specialist

**Role:** JEBAT's defensive security tier (Pengawal sub-skill)
**Lineage:** HexSecGPT defensive patterns + Pentagi audit flows
**Type:** Execution skill

## Capabilities

### 1. Vulnerability Scanning
- Port scanning and service enumeration (nmap-style analysis)
- Web application vulnerability assessment
- Network security assessment
- Configuration weakness detection

### 2. Threat Modeling
- **STRIDE Analysis:** Spoofing, Tampering, Repudiation, Information Disclosure, DoS, Elevation
- **DREAD Scoring:** Damage, Reproducibility, Exploitability, Affected users, Discoverability
- Attack tree generation
- Attack surface mapping

### 3. Compliance Auditing
- **OWASP Top 10** checking
- **CIS Benchmarks** validation
- **ISO 27001** control mapping
- **SOC 2** readiness assessment
- **GDPR** data protection review

### 4. Security Configuration Audit
- Server hardening checklist
- Application security review
- Database security audit
- Cloud infrastructure review
- Container security assessment

### 5. Incident Response
- IR playbook execution
- Evidence collection and chain of custody
- Root cause analysis
- Containment strategies
- Recovery procedures

## Usage

```
Security scan [target]        → Full vulnerability assessment
Threat model [system]         → STRIDE + DREAD analysis
Compliance check [framework]  → Audit against framework
Audit [component]             → Configuration security review
Incident [description]        → IR playbook execution
```

## Output Templates

### Vulnerability Report
```
## Vulnerability Report: [Target]
**Scan Date:** [timestamp]
**Scope:** [authorized targets]

### Summary
- Critical: N
- High: N
- Medium: N
- Low: N
- Info: N

### Findings
| ID | CVSS | Title | Component | Status |
|----|------|-------|-----------|--------|
| V-001 | 9.1 | RCE via SQLi | /api/login | Open |

### Evidence
[Proof/description for each finding]

### Remediation
[Prioritized fix recommendations]
```

### Threat Model
```
## Threat Model: [System]

### System Overview
[Architecture and data flow]

### STRIDE Analysis
| Threat | Component | Mitigation | Risk |
|--------|-----------|------------|------|

### Attack Surface
[Entry points, trust boundaries]

### Top Risks
1. [Risk] — [Mitigation]
2. [Risk] — [Mitigation]
```

## Tools Reference

| Category | Tools (reference only) |
|----------|----------------------|
| Scanning | nmap, nikto, nuclei, trivy |
| SAST | semgrep, bandit, eslint-security |
| DAST | owasp-zap, burpsuite |
| Containers | trivy, grype, dockle |
| IaC | checkov, tfsec, terrascan |
| Secrets | gitleaks, trufflehog, detect-secrets |
