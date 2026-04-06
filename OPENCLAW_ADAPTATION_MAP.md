# JEBAT → OpenClaw Adaptation Map

## Goal

Translate JEBAT concepts into **actual OpenClaw-native behavior** using tools that already exist in this environment.

---

## 1. Memory System Adaptation

### JEBAT concept
- M0 sensory
- M1 episodic
- M2 semantic
- M3 conceptual
- M4 procedural
- heat-based scoring
- consolidation

### OpenClaw-native adaptation

#### M0 Sensory
Use:
- current message context
- current file/workspace context
- recent tool outputs

Implementation note:
- ephemeral only, not explicitly persisted unless promoted

#### M1 Episodic
Use:
- `memory/YYYY-MM-DD.md`
- session notes
- daily logs

Implementation note:
- write important events, conversations, task outcomes

#### M2 Semantic
Use:
- distilled notes in `MEMORY.md`
- tagged summaries in daily memory files

Implementation note:
- preferences, facts, project truths, architecture facts

#### M3 Conceptual
Use:
- stable principles in `MEMORY.md`
- architecture docs and design guidance

Implementation note:
- patterns, mental models, durable strategic decisions

#### M4 Procedural
Use:
- `AGENTS.md`
- skill files in `skills/*/SKILL.md`
- `TOOLS.md`
- workflow docs

Implementation note:
- turn repeated successful actions into reusable procedures

### Heat scoring adaptation
OpenClaw does not natively expose full heat scoring, so approximate through:
- repeated references in memory files
- promotion to `MEMORY.md`
- preservation in skill/procedure docs
- cron/heartbeat review passes

### Consolidation adaptation
Use:
- periodic review via heartbeat or cron
- manual promotion from daily memory → MEMORY.md
- procedural promotion into AGENTS.md / skill docs

---

## 2. Agent Orchestration Adaptation

### JEBAT concept
- specialist agents
- orchestration
- councils
- decomposition

### OpenClaw-native adaptation
Use:
- `sessions_spawn` for isolated subagents / ACP harnesses
- `sessions_send` for cross-session communication
- `subagents` for steering and intervention
- `sessions_yield` when waiting for spawned work

### Mapping
- Core agent → main session agent
- Analyst → spawned subagent / ACP coding or analysis session
- Researcher → local research flow using `web_search` + `web_fetch`
- Security → dedicated security workflow docs + spawned specialist when needed
- Council → multiple spawned sessions summarized back into main thread

---

## 3. Research Adaptation

### JEBAT concept
- deep research
- verification
- synthesis

### OpenClaw-native adaptation
Use:
- `web_search`
- `web_fetch`
- `memory_search` before re-answering prior decisions
- local docs first for OpenClaw-specific behavior

Pattern:
1. search
2. fetch best sources
3. synthesize
4. store key findings in memory files

---

## 4. Cybersecurity Adaptation

### JEBAT concept
- vulnerability scanning
- audit
- risk assessment

### OpenClaw-native adaptation
Use:
- `exec` for local defensive inspection tools when available
- `read` / config review for hardening and architecture inspection
- `web_search` / `web_fetch` for CVE and best-practice research
- memory files to track findings and remediation status

Guardrail:
- defensive work is default
- never imply exploitation when only auditing

---

## 5. Hardening Adaptation

### JEBAT concept
- secure configuration
- patching
- attack surface reduction

### OpenClaw-native adaptation
Use:
- `read` for config review
- `edit` for config generation or safe local changes
- `exec` for diagnostics and non-destructive validation
- skill-driven recommendations from healthcheck and local notes

Guardrail:
- ask before destructive or risky production changes

---

## 6. Pentesting Adaptation

### JEBAT concept
- authorized exploitation
- attack path validation

### OpenClaw-native adaptation
Use only under explicit authorization.

Allowed adaptation focus in this workspace:
- pentest planning
- scope definition
- findings documentation templates
- safe simulation and checklist generation

Guardrail:
- no unauthorized offensive execution
- no pretending authorization exists

---

## 7. Hermes Integration

Hermes should sit on top of this map and improve:
- routing
- tool choice
- delegation choice
- memory recall choice
- specialist workflow selection

---

## 8. Immediate Practical Outcome

What adaptation means **right now**:
- JEBAT becomes a structured operating model for OpenClaw
- memory lives in workspace files first
- specialists are simulated or spawned using OpenClaw sessions
- skills become operational guides and eventually executable adapters
- website work is secondary to runtime ability
