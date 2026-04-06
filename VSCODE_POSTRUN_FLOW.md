# VS Code Post-Run Flow

## Goal

Define what Jebat does after downstream model or agent work finishes.

---

## Post-run sequence
1. inspect output
2. verify it matches the task
3. decide whether follow-up work is needed
4. write important memory if the result changes future behavior
5. append provenance if a meaningful decision was made
6. append lifecycle if stack state changed
7. update task record if one exists

---

## Memory rule
Do not write everything.
Write what should survive:
- decisions
- durable facts
- reusable workflows
- stack changes

---

## Control rule
Jebat should remain the closer, not just the opener.
