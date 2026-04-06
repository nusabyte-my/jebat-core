# JEBAT System Build Plan

**Date:** 2026-04-07
**Status:** In Progress — Building All Phases
**Scope:** Full productization of JEBATCore into a shippable platform

---

## External Skill Adaptations

### Adopted Repos

| Repo | What We Take | JEBAT Adaptation |
|------|-------------|-----------------|
| [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem) | Persistent memory compression, vector search, progressive disclosure, privacy controls | **Hikmat Memory Engine** — Replace file-based memory with SQLite+Chroma, add 3-layer MCP search (compact→timeline→full), auto-capture observations on tool use |
| [umputun/ralphex](https://github.com/umputun/ralphex) | Autonomous plan execution, 5-agent parallel review, git worktree isolation, Docker sandbox | **Tukang Execution Engine** — Plan parser → task runner → quality/security/testing/simplicity/doc review pipeline → external reviewer → auto-commit |
| [skills.sh](https://skills.sh/) | 150+ skills across design, dev, security, marketing, SEO, cloud | **Skill Catalog Expansion** — Add 40+ high-value skills: shadcn/ui, better-auth, systematic-debugging, test-driven-dev, subagent-driven-dev, web-testing, playwright, tailwind-design-system, api-design, code-review, security-best-practices, data-analysis, workflow-automation |
| [slgoodrich/agents](https://github.com/slgoodrich/agents) | 7 PM specialist agents, RICE/Kano prioritization, PRD generation, market analysis | **Penganalisis + Strategi Produk Expansion** — Add market-analyst, research-ops, roadmap-builder, feature-prioritizer, requirements-engineer, launch-planner, context-scanner |
| [automazeio/ccpm](https://github.com/automazeio/ccpm) | Spec-driven PM workflow, GitHub-native state tracking, parallel agent orchestration | **Syahbandar Project Manager** — 5-phase workflow (Brainstorm→Document→Plan→Execute→Track), PRD→epic→task decomposition, GitHub issue sync, worktree isolation |

### Cybersecurity Lineage Rebrand

| Origin | Lineage | JEBAT Rebrand |
|--------|---------|---------------|
| HexSecGPT | Personal hacker assistant + custom AI model | **Sentinel** → **Pengawal** (Guardian) |
| HexStrike AI | Multi-agent pentesting framework (recon→analysis→exploit→report) | Offensive layer → **Serangan** (Strike) |
| Pentagi | Pentesting AI assistant | Defensive layer → **Perisai** (Shield) |

### New Cybersec Skill: Pengawal (CyberSec Assistant)

**Three-tier architecture:**

1. **Perisai (Shield)** — Defensive
   - Vulnerability scanning & assessment
   - Security configuration audit
   - Threat modeling & risk analysis
   - Compliance checking (OWASP, CIS)
   - Incident response playbooks

2. **Pengawal (Guardian)** — Monitoring
   - Real-time threat detection
   - Log analysis & anomaly detection
   - Memory-integrated threat learning (M4 procedural)
   - Automated alert triage
   - Security posture dashboard

3. **Serangan (Strike)** — Offensive (authorized only)
   - Automated recon & enumeration
   - Exploit chain generation
   - Proof-of-concept execution
   - Post-exploitation simulation
   - Comprehensive pentest reporting

**Skills added to catalog:**
- `pengawal` — Main cybersec assistant (routing)
- `perisai` — Defensive security
- `serangan` — Authorized pentesting
- `threat-model` — STRIDE/DREAD analysis
- `incident-response` — IR playbook execution
- `compliance-audit` — OWASP/CIS/ISO27001 checks
- `exploit-research` — CVE/POC database search
- `report-gen` — Pentest report generation

---

## Build Plan

### Phase 1: Landing Page ✅

### Phase 2: Onboarding Dashboard

### Phase 3: Dev Tools / IDE Adapters

### Phase 4: NPX CLI Rebrand (`@nusabyte/jebat`)

### Phase 5: AI Assistant CLI

### Phase 6: End-User Test Dashboard

### Phase 7: Enhancement Roadmap

---

## Execution Order

```
Phase 1: Landing Page
Phase 2: Onboarding Dashboard
Phase 3: Dev Tools / IDE Adapters
Phase 4: NPX CLI Rebrand
Phase 5: AI Assistant CLI
Phase 6: Test Dashboard
Phase 7: External skill adaptation + cybersec assistant
```

---

## Total Scope

| Phase | Outcome |
|-------|---------|
| 1. Landing Page | Production landing page with live status |
| 2. Onboarding Dashboard | Setup wizard + gateway dashboard + provider config |
| 3. Dev Tools | Enhanced adapters + IDE context installer |
| 4. NPX CLI Rebrand | `@nusabyte/jebat` published to NPM |
| 5. AI Assistant CLI | Full interactive chat CLI with multi-provider |
| 6. Test Dashboard | Public demo page with chat |
| 7. Skill Expansion | 40+ new skills from skills.sh, 7 PM agents, CCPM, ralphex, claude-mem |
| 8. CyberSec Assistant | Pengawal (3-tier: Perisai/Pengawal/Serangan) |
