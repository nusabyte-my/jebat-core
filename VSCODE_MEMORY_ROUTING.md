# VS Code Memory Routing

## Goal

Define how Jebat chooses which memory layers/files to consult before coding work.

---

## Routing rules

### Daily memory
Use when:
- current work block matters
- recent decisions may affect implementation
- unresolved follow-up may already exist

### Long-term memory
Use when:
- project direction matters
- stable architecture context matters
- user preferences affect coding style or decisions

### Entity memory
Use when:
- task concerns a named system, skill, concept, or operational component
- retrieval by subject is more useful than date-based lookup

### Runtime logs
Use when:
- task changes stack behavior
- helper/admin/runtime systems are involved
- prior provenance or lifecycle notes may explain current state

---

## Rule
Load the smallest useful context first, then widen only if needed.
