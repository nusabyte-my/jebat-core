# Serangan — Authorized Offensive Security

**Role:** JEBAT's offensive security tier (Pengawal sub-skill)
**Lineage:** HexStrike AI multi-agent pentesting framework
**Type:** Execution skill — AUTHORIZED TARGETS ONLY

## ⚠️ Authorization Required

This skill MUST NOT be used without explicit, documented authorization for the target system.

### Authorization Checklist
- [ ] Target scope documented (URLs, IPs, ranges)
- [ ] Time window defined
- [ ] Rules of engagement agreed
- [ ] Emergency contact established
- [ ] Written approval received
- [ ] Logged in `security/authorization.log`

## Capabilities

### Phase 1: Reconnaissance
- Passive information gathering (OSINT)
- DNS enumeration and subdomain discovery
- Technology stack identification
- Employee/social engineering surface analysis
- Cloud asset enumeration

### Phase 2: Analysis & Planning
- Attack surface mapping
- Vulnerability correlation with available exploits
- Attack path prioritization
- Exploit chain design
- Payload generation

### Phase 3: Exploitation (Authorized Only)
- Web application exploitation
- API security testing
- Authentication/authorization bypass attempts
- Injection testing (SQLi, XSS, SSRF, RCE)
- File upload and path traversal testing
- Business logic abuse testing

### Phase 4: Post-Exploitation Simulation
- Privilege escalation paths
- Lateral movement simulation
- Data access assessment
- Persistence mechanism testing
- Impact assessment

### Phase 5: Reporting
- Executive summary
- Technical findings with evidence
- CVSS scoring
- Exploit reproduction steps
- Prioritized remediation roadmap
- Risk acceptance recommendations

## Pentest Workflow

```
1. Scope Definition → Document authorized targets
2. Reconnaissance → Gather intelligence (passive + active)
3. Vulnerability Analysis → Identify and validate weaknesses
4. Exploitation → Attempt to exploit (authorized targets only)
5. Post-Exploitation → Assess impact (if exploitation successful)
6. Reporting → Generate comprehensive report
7. Remediation Support → Help fix findings
8. Retesting → Verify fixes
```

## Report Template

```
# Penetration Test Report: [Target]

## Executive Summary
[Brief overview for management]

## Scope
**Authorized Targets:** [list]
**Time Window:** [start] → [end]
**Test Type:** Black box / Grey box / White box

## Findings Summary
| Severity | Count |
|----------|-------|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Info | N |

## Detailed Findings

### [F-001] [Title]
**Severity:** [Critical/High/Medium/Low/Info]
**CVSS:** [score]
**Component:** [affected system]
**Status:** [Open/Fixed/Accepted]

**Description:**
[What the vulnerability is]

**Evidence:**
[Proof of concept / screenshots]

**Impact:**
[What an attacker could achieve]

**Remediation:**
[How to fix it]

## Attack Timeline
[Chronological sequence of test activities]

## Recommendations
[Prioritized action items]

## Appendices
- Tools used
- References
- Authorization documentation
```

## Safety Rules

- NEVER attack targets outside documented scope
- NEVER perform destructive actions
- NEVER exfiltrate real user data
- ALWAYS stop if unauthorized access detected
- ALWAYS document every action taken
- ALWAYS follow rules of engagement
- Log all findings properly
