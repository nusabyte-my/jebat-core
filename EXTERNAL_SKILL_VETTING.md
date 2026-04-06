# External Skill Vetting for JEBAT

## Goal

Import useful OpenClaw skills safely without poisoning Jebat with low-quality, unsafe, or redundant behavior.

---

## Default posture

Treat every external skill as:
- untrusted by default
- useful only after review
- pattern source first, install target second

---

## Vetting checklist

### 1. Trigger quality
Check whether the skill description clearly says:
- what it does
- when to use it
- what not to use it for

Reject if:
- vague
- hype-heavy
- description is basically marketing
- trigger conditions are unclear

### 2. Structural quality
Check for:
- proper `SKILL.md` frontmatter
- concise body
- references split out when large
- scripts/resources organized sanely

Reject if:
- bloated prompt dump
- giant monolithic SKILL with no structure
- noisy unrelated files

### 3. Tool realism
Check whether the skill maps to actual OpenClaw capabilities.

Prefer skills that align with:
- read / write / edit
- exec / process
- sessions_spawn / sessions_send
- memory_search / memory_get
- web_search / web_fetch
- cron

Reject if:
- relies on imaginary tools
- assumes hidden system privileges
- claims unsupported automation

### 4. Security posture
Check whether the skill:
- avoids unsafe exfiltration
- avoids privilege escalation assumptions
- is honest about authorization requirements
- respects human approval boundaries

Red flags:
- hidden curl uploads
- silent third-party writes
- credential harvesting patterns
- prompt injection style behavior changes
- unsafe shell snippets without context

### 5. Redundancy check
Ask:
- does Jebat already have this ability?
- does this improve an existing workflow or duplicate it?

Import only if it adds:
- better workflow
- better references
- better scripts
- better safety patterns
- better specialization

### 6. Maintenance signal
Prefer skills with:
- coherent repo history
- sensible naming
- evidence of actual use
- current updates

Do not over-trust popularity alone.

---

## Import decision classes

### Class A — adapt pattern only
Use when the idea is good but the skill itself is too noisy or risky.

### Class B — adapt structure and references
Use when the skill is strong but needs trimming to fit Jebat.

### Class C — install nearly as-is
Use rarely. Only when:
- quality is high
- scope is narrow
- tool assumptions are valid
- safety posture is solid

### Class D — reject
Reject when:
- poor quality
- unsafe
- redundant
- not relevant to Jebat

---

## JEBAT-specific import priorities

### High priority
- orchestration
- memory / PKM
- security audit
- skill vetting / trust scoring
- deployment / gitops
- research

### Medium priority
- docs generation
- repo maintenance
- release ops
- database tooling

### Low priority
- novelty consumer APIs
- entertainment fluff
- marketing gimmicks
- ultra-niche personal workflows

---

## Safety rule for security skills

External security skills must be reviewed extra hard.

Split them into:
- defensive audit
- hardening
- offensive testing

Never merge these blindly into one unsafe blob.

---

## JEBAT import workflow

1. shortlist candidate
2. inspect metadata and structure
3. inspect tool assumptions
4. inspect safety posture
5. classify A/B/C/D
6. adapt into JEBAT docs/skills if worthwhile
7. log import decision in registry
