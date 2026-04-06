# Awesome OpenClaw Skills - JEBAT Shortlist

Source reviewed:
- https://github.com/VoltAgent/awesome-openclaw-skills

Goal:
- shortlist high-value external skill ideas worth adapting into Jebat
- prioritize patterns over blind installation

---

## Tier 1 — strongest fit for Jebat

### 1. agent-team-orchestration
Why it fits:
- directly reinforces Hermes + Jebat orchestration
- useful for task lifecycle, role design, and handoff structure

Likely import class:
- **B** (adapt structure and references)

Use for:
- multi-agent plans
- councils
- specialist delegation patterns

---

### 2. arc-trust-verifier
Why it fits:
- Jebat needs safe external skill intake
- trust/provenance scoring is exactly the right defense layer

Likely import class:
- **A/B**

Use for:
- skill provenance checks
- source trust heuristics
- import review workflow

---

### 3. azhua-skill-vetter
Why it fits:
- strong complement to trust verification
- likely useful for security-first skill review patterns

Likely import class:
- **A/B**

Use for:
- screening skills before adoption
- identifying unsafe skill patterns

---

### 4. arc-security-audit
Why it fits:
- maps well to JEBAT cybersecurity
- could improve agent-stack review posture

Likely import class:
- **B**

Use for:
- skill stack audit
- system security review
- risk reporting

---

### 5. 2nd-brain
Why it fits:
- overlaps with JEBAT memory direction
- useful for memory capture/retrieval ideas

Likely import class:
- **A**

Use for:
- personal knowledge workflows
- preference capture
- memory retrieval ideas

---

### 6. arxiv-search-collector / academic-research
Why it fits:
- strengthens research mode
- useful for researcher skill upgrades

Likely import class:
- **A/B**

Use for:
- literature search
- paper set construction
- evidence-based research mode

---

## Tier 2 — useful support skills

### 7. arc-skill-gitops
Why it fits:
- skill lifecycle and versioning matter if Jebat grows a larger skill stack

Likely import class:
- **A**

Use for:
- skill deployment discipline
- rollback/version management ideas

---

### 8. alex-session-wrap-up
Why it fits:
- useful for end-of-session memory and rule capture
- aligns with Jebat continuity goals

Likely import class:
- **A**

Use for:
- session wrap-up
- note extraction
- learning persistence

---

### 9. agent-commons
Why it fits:
- may provide reusable reasoning-chain / consult / challenge workflows

Likely import class:
- **A**

Use for:
- structured reasoning support
- internal review / challenge patterns

---

### 10. agentgate
Why it fits:
- human-in-the-loop write approval is a good design pattern
- useful for sensitive external actions

Likely import class:
- **A**

Use for:
- approval boundaries
- external action safety patterns

---

## Tier 3 — maybe useful later

### 11. arc-agent-lifecycle
Use later for:
- long-lived specialist lifecycle management
- session state and cleanup conventions

### 12. auto-pr-merger / git automation skills
Use later for:
- release ops
- repo automation
- workflow support once Jebat enters active development loops

### 13. biz-reporter
Use later for:
- report formatting ideas
- analytics workflow inspiration

---

## Not a priority right now

Do not spend time on:
- novelty consumer APIs
- crypto / chain-heavy skills
- random shopping/media gimmicks
- weakly described security skills
- anything that doesn’t improve Jebat runtime ability

---

## Immediate adaptation targets

### Target A — Hermes orchestration upgrade
Sources:
- agent-team-orchestration
- agent-commons
- arc-agent-lifecycle

### Target B — skill trust and import pipeline
Sources:
- arc-trust-verifier
- azhua-skill-vetter
- agentgate

### Target C — research upgrade
Sources:
- academic-research
- arxiv-search-collector

### Target D — continuity / memory review
Sources:
- 2nd-brain
- alex-session-wrap-up

### Target E — security stack refinement
Sources:
- arc-security-audit

---

## Next review procedure

For each shortlisted skill:
1. inspect actual SKILL.md/source
2. classify A/B/C/D from vetting doc
3. extract useful patterns
4. merge into JEBAT docs and skills
5. avoid bloating the workspace with low-value imports
