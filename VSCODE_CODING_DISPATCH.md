# VS Code Coding Dispatch

## Goal

Define how Jebat routes coding tasks.

---

## Dispatch rules

### Direct local handling
Use when:
- change is small
- a few files are involved
- direct edits are faster than delegation

### Coding-engine / specialist handling
Use when:
- implementation is substantial
- repo exploration is needed
- iterative coding loop will be long
- testing/build loop is non-trivial

### Research-first handling
Use when:
- architecture is unclear
- external references matter
- best-practice grounding is needed first

### Security-first handling
Use when:
- auth, exposure, secrets, permissions, or risky execution paths are involved

### Review-first handling
Use when:
- code exists but quality or risk is uncertain
- we need verification before merge or adoption

---

## Dispatch output
Every coding task should be framed with:
- objective
- scope
- relevant context
- chosen execution path
- verification expectations
