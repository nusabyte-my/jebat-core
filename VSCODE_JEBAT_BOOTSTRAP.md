# VS Code Jebat Bootstrap

## Goal

Make Jebat the first-loaded control layer before other LLM workflows in the editor.

---

## Load order
1. `JEBAT_CONTROL_PANEL.md`
2. `JEBAT_STATUS.md`
3. `JEBAT_EXEC_SUMMARY.md`
4. relevant `memory/YYYY-MM-DD.md`
5. relevant `brain/` entries if the task matches named entities or core stack concepts
6. relevant runtime logs if the task touches operations or stack evolution

---

## Core principle

Jebat should frame the task first.
Other models or agents should receive a task that is already:
- classified
- scoped
- memory-aware
- policy-bounded

---

## Bootstrap questions
Before handing work to another model:
- what kind of task is this?
- what context is actually needed?
- what memory should be loaded?
- what safety boundary applies?
- should this stay local or be delegated?
