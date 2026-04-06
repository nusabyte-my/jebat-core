# VS Code Dispatch Policy

## Goal

Define how Jebat routes work before another model or tool is used.

---

## Dispatch rules

### Stay local
Use Jebat directly when:
- task is small
- direct file edits are enough
- no specialist depth is needed

### Coding engine
Use coding-focused model/agent when:
- implementation or refactor is substantial
- repo exploration is needed
- iterative coding loop will be long

### Research flow
Use research mode when:
- external sources matter
- claim verification matters
- literature or academic search is required

### Security flow
Use security/hardening flow when:
- posture, exposure, risk, audit, or remediation is involved

### Orchestrator flow
Use orchestration when:
- the task is multi-part
- specialist handoffs improve quality
- verification should be separated from generation

---

## Rule
Dispatch should reduce ambiguity, not just move work elsewhere.
