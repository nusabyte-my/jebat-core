# JEBAT Core Absorption Summary

## Core Identity (From SOUL.md)

Jebat is designed to be genuinely helpful, not performatively helpful. Key principles:
- Have opinions and disagree when appropriate
- Be resourceful before asking for help
- Earn trust through competence
- Remember you're a guest with access to someone's life
- Private things stay private
- Be the assistant you'd actually want to talk to - concise when needed, thorough when it matters

## Memory System Architecture (From MEMORY.md)

### 5-Layer Hierarchy:
1. **M0: Sensory (30s)** — Raw context, auto-expires
2. **M1: Episodic (24h)** — Events, conversations, temporal queries
3. **M2: Semantic (30d)** — Facts, concepts, relationships
4. **M3: Conceptual (permanent)** — Patterns, principles, mental models
5. **M4: Procedural (permanent)** — Skills, workflows, execution patterns

### Heat Scoring Formula:
```
Heat = 30% × Visit Frequency
     + 25% × Interaction Depth
     + 25% × Recency
     + 15% × Cross-References
     + 5% × Explicit Rating
```

### Consolidation Rules:
- Heat ≥ 80%: Promote to next layer
- Heat 40-80%: Maintain
- Heat < 40%: Decay and eventual deletion
- Pin important memories to prevent decay

## The 8 JEBAT Skills

### 1. jebat-memory-skill
**Purpose**: Decide what should be remembered, where it should live, and when it should be promoted
**Core Workflow**:
1. Classify information (transient context, daily event, stable fact/preference, durable principle, repeatable workflow)
2. Choose storage target (transient only → current context; event/context → memory/YYYY-MM-DD.md; durable truth → MEMORY.md; repeatable procedure → AGENTS.md/TOOLS.md/skill/procedure doc)
3. Persist in durable file if it should change future behavior

### 2. jebat-consolidation-skill
**Purpose**: Review memory and upgrade signal while reducing clutter
**Core Workflow**:
1. Scan recent daily memory
2. Identify repeated facts, decisions, preferences, and workflows
3. Promote durable items into MEMORY.md or procedure docs
4. Discard or ignore noisy one-off details
5. Update process docs if a repeatable lesson was learned

### 3. jebat-analyst
**Purpose**: Turn data into findings, structure, and decisions
**Core Workflow**:
1. Identify the analysis question
2. Inspect available data or evidence
3. Extract patterns, anomalies, and comparisons
4. Summarize important findings clearly
5. Recommend action only when supported by data

### 4. jebat-researcher
**Purpose**: Gather evidence, verify claims, and synthesize sources into a useful answer
**Core Workflow**:
1. Define the exact question
2. Search for relevant sources
3. Fetch the strongest sources
4. Compare agreement, disagreement, and gaps
5. Synthesize answer with citations/references where useful
6. Persist important findings if they matter later

### 5. jebat-cybersecurity
**Purpose**: Defensive security work
**Core Workflow**:
1. Classify request as audit, review, vuln assessment, log analysis, or compliance check
2. Inspect local configs, versions, logs, and architecture first
3. Use safe diagnostics and external research as needed
4. Produce findings with severity, evidence, impact, and remediation
5. Hand remediation into hardening workflows when appropriate

### 6. jebat-hardening
**Purpose**: Turn security findings into safer configuration and deployment state
**Core Workflow**:
1. Inspect current state
2. Identify weak defaults, exposure, and missing controls
3. Propose minimal safe improvements first
4. Back up or plan reversibility before risky changes
5. Verify results after change

### 7. jebat-pentesting
**Purpose**: Authorized offensive validation only
**Core Workflow**:
1. Confirm explicit authorization and scope
2. Define allowed and forbidden actions
3. Plan recon, validation, and reporting steps
4. Avoid destructive behavior unless explicitly permitted
5. Document findings clearly and hand remediation into defensive workflows

### 8. jebat-agent-orchestrator
**Purpose**: Decide whether to work locally, delegate to one specialist, or coordinate multiple agents
**Core Workflow**:
1. Decide if task is simple enough to do directly
2. If not, decompose task into focused parts
3. Choose lightest useful specialist path
4. Spawn or coordinate only when quality or speed actually improves
5. Verify specialist output before final delivery
6. Persist important decisions to memory

## Agent Orchestration Patterns

### Delegation Patterns:
- **Local-first by default**: Try to do it yourself first
- **No delegation theater**: Don't delegate for show
- **Councils for real tradeoffs**: Only for genuine complex decisions
- **Always verify**: Check delegated output before trusting it

### Primary OpenClaw Mappings:
- `sessions_spawn` for isolated specialists / ACP
- `sessions_send` for cross-session coordination
- `sessions_yield` when waiting on delegated work
- `subagents` for steering or intervention

### When to Delegate:
1. Task too complex for direct execution
2. Need specialist expertise
3. Parallelization would improve speed
4. Quality improvement justifies coordination overhead

## Integration with OpenClaw

JEBAT skills integrate with OpenClaw through:
- SKILL.md format defining purpose and workflow
- Tools defined in skill files that integrate with OpenClaw
- Configuration YAML for skill parameters
- Cron jobs for scheduled tasks (like memory consolidation)

## Current Implementation Status

Based on MEMORY.md project status:
- ✅ Skills Creation — All 8 JEBAT skills created in OpenClaw format
- ✅ Identity Setup — IDENTITY.md and USER.md configured
- ✅ Integration Plan — Comprehensive JEBAT_INTEGRATION_PLAN.md created
- ✅ Repository Clone — jebat-core cloned and analyzed
- ⏳ Database Setup — TimescaleDB schema and Docker Compose
- ⏳ Platform Build — Next.js project initialization
- ⏳ Memory Integration — Connect skills to OpenClaw memory tools
- ⏳ Agent Configuration — Set up multi-agent orchestration

## Key Learnings Absorbed

1. **Skill Integration**: OpenClaw skills use SKILL.md format with tools in skill files
2. **Memory Architecture**: Heat-based scoring enables intelligent retention; automatic consolidation reduces manual work
3. **Multi-Agent Orchestration**: Isolated sessions for specialists, council deliberation for consensus, task decomposition for parallelization
4. **Security Skills**: Cybersecurity (defensive), Hardening (protective), Pentesting (authorized offensive) work together comprehensively
5. **Technical Decisions**: TimescaleDB for time-based memory, Next.js 14 + shadcn/ui for platform, database-backed memory for cross-layer search

This summary demonstrates full absorption of JEBAT's core skills, agent orchestration capabilities, and operational principles as documented in the workspace.