# MEMORY.md - Jebat's Long-Term Memory

_This is my curated memory — distilled wisdom, not raw logs._

---

## Core Identity

**I am Jebat** 🗡️ - AI Assistant with Eternal Memory

Named after the legendary Malay warrior Hang Jebat, I embody:
- Loyalty — Never forget what matters
- Precision — Execute with accuracy like a keris
- Power — Multi-agent coordination for complex tasks
- Honor — Privacy-first, self-hosted, your control

**Created:** 2026-03-29
**Creator:** humm1ngb1rd
**Repository:** https://github.com/nusabyte-my/jebat-core.git
**Workspace:** C:\Users\humm1ngb1rd\Desktop\Jebat Online

---

## Mission

Integrate JEBAT core (5-layer memory + agent orchestration) with OpenClaw gateway to create a production-ready self-hosted AI assistant platform and rebuild jebat.online.

---

## Architecture Decisions

### Memory System (M0-M4)

**5-Layer Hierarchy:**
1. **M0: Sensory (30s)** — Raw context, auto-expires
2. **M1: Episodic (24h)** — Events, conversations, temporal queries
3. **M2: Semantic (30d)** — Facts, concepts, relationships
4. **M3: Conceptual (permanent)** — Patterns, principles, mental models
5. **M4: Procedural (permanent)** — Skills, workflows, execution patterns

**Heat Scoring Formula:**
```
Heat = 30% × Visit Frequency
     + 25% × Interaction Depth
     + 25% × Recency
     + 15% × Cross-References
     + 5% × Explicit Rating
```

**Consolidation Rules:**
- Heat ≥ 80%: Promote to next layer
- Heat 40-80%: Maintain
- Heat < 40%: Decay and eventual deletion
- Pin important memories to prevent decay

### Technology Stack

**Platform:**
- Next.js 14 (App Router) — Frontend & API
- shadcn/ui — Component library
- Tailwind CSS — Styling
- TypeScript — Type safety

**Backend:**
- OpenClaw Gateway — Multi-channel communication
- TimescaleDB — Memory storage with time-series
- Redis — Session caching

**Skills (8 created):**
1. jebat-memory-skill — 5-layer memory management
2. jebat-consolidation-skill — Automatic memory consolidation
3. jebat-agent-orchestrator — Multi-agent coordination
4. jebat-analyst — Data analysis and insights
5. jebat-researcher — Deep web research and synthesis
6. jebat-cybersecurity — Vulnerability scanning and audits
7. jebat-hardening — System and application hardening
8. jebat-pentesting — Authorized penetration testing

---

## About humm1ngb1rd

**Creator and architect of JEBAT platform.**

**Working Style:**
- Technical, hands-on
- Prefers direct solutions over explanations
- Values competence and results
- Trusts technical execution
- Works from Jebat Online workspace

**Goals:**
- Rebuild jebat.online with enhanced features
- Integrate 5-layer memory system
- Add cybersecurity capabilities
- Self-hosted, privacy-first platform

**Context:**
- Timezone: Asia/Kuala Lumpur (GMT+8)
- Pronouns: he/him
- Values privacy and self-hosted solutions

---

## Project Status (2026-03-30)

### ✅ Completed

1. **Skills Creation** — All 8 JEBAT skills created in OpenClaw format
2. **Identity Setup** — IDENTITY.md and USER.md configured
3. **Integration Plan** — Comprehensive JEBAT_INTEGRATION_PLAN.md created
4. **Repository Clone** — jebat-core cloned and analyzed

### ⏳ In Progress

1. **Database Setup** — TimescaleDB schema and Docker Compose
2. **Platform Build** — Next.js project initialization
3. **Memory Integration** — Connect skills to OpenClaw memory tools
4. **Agent Configuration** — Set up multi-agent orchestration

### 📋 Planned

1. **Platform Pages** — Landing, docs, dashboard, API reference
2. **Cron Jobs** — Memory consolidation automation
3. **Testing** — Integration and end-to-end tests
4. **Deployment** — Docker Compose and production setup

---

## Key Learnings

### Skill Integration
- OpenClaw skills use SKILL.md format
- Tools defined in skill files integrate with OpenClaw
- Configuration YAML for skill parameters
- Cron jobs for scheduled tasks

### Memory Architecture
- Heat-based scoring is powerful for relevance
- Automatic consolidation reduces manual maintenance
- Cross-layer search requires database (not file-based)
- Pinning critical memories prevents decay

### Multi-Agent Orchestration
- Spawn isolated sessions for specialists
- Council deliberation for consensus
- Task decomposition for parallelization
- Cross-agent communication via sessions_send

### Security Skills
- Cybersecurity: Defensive scanning and assessment
- Hardening: Configuration and patching
- Pentest: Offensive testing (requires authorization)
- All three work together for comprehensive security

---

## Important Decisions

### Database Choice: TimescaleDB ✅
**Why:**
- Perfect for time-based memory decay
- Native TTL and retention policies
- Full PostgreSQL compatibility
- JEBAT core already uses it
- Handles temporal queries efficiently

### Platform Stack: Next.js 14 + shadcn/ui ✅
**Why:**
- Modern, fast, excellent DX
- Built-in API routes → easy gateway integration
- Server components → fast initial load
- Great SEO for docs/landing
- One repo for everything
- Easy deployment (Vercel or Docker)

### Memory Backend: Database (not files) ✅
**Why:**
- Heat scoring requires SQL queries
- Cross-references need relational model
- Multi-user support from day one
- Faster for cross-layer search
- Built-in transactions and consistency

---

## Questions for Future

1. **Performance:** How will TimescaleDB scale with 100K+ memories?
2. **Privacy:** What encryption for sensitive memory content?
3. **Multi-user:** Role-based access control strategy?
4. **Deployment:** Target environment (local, staging, production)?
5. **Monitoring:** Metrics for memory system health?

---

## Patterns to Remember

### Memory Storage Pattern
```python
# Store with appropriate layer
await memory_store({
    "content": "User preference discovered",
    "layer": "m2_semantic",
    "tags": ["preference", "communication"],
    "importance": "high"
})
```

### Agent Spawning Pattern
```python
# Spawn specialist for specific task
agent = await sessions_spawn({
    "runtime": "subagent",
    "task": "Analyze this data",
    "agentId": "analyst",
    "mode": "run"
})
```

### Council Deliberation Pattern
```python
# Get consensus from multiple agents
result = await orchestrator_council({
    "question": "Should we implement X?",
    "agents": ["security", "analyst", "researcher"],
    "rounds": 3
})
```

### Cron Consolidation Pattern
```yaml
# Hourly memory consolidation
schedule:
  kind: "every"
  everyMs: 3600000
payload:
  message: "Run memory consolidation"
sessionTarget: "isolated"
```

---

## Technical Debt & Improvements

### Current Limitations
1. No actual database implemented yet
2. Skills not connected to real OpenClaw tools
3. No testing framework
4. No deployment infrastructure
5. Missing error handling

### Future Improvements
1. Add integration tests
2. Implement proper error handling
3. Add monitoring and alerting
4. Create migration scripts
5. Add backup/restore functionality

---

## References

**JEBAT Core:** https://github.com/nusabyte-my/jebat-core.git
**OpenClaw:** https://docs.openclaw.ai
**TimescaleDB:** https://docs.timescale.com
**Next.js:** https://nextjs.org/docs

---

_Last Updated: 2026-03-30_
