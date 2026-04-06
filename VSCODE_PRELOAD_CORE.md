# VS Code Preload Core

## Goal

Make Jebat the first consult point before coding or editor-driven LLM workflows begin.

---

## Preload sequence
1. Load `JEBAT_CONTROL_PANEL.md`
2. Load `JEBAT_STATUS.md`
3. Load `JEBAT_EXEC_SUMMARY.md`
4. Load recent `memory/YYYY-MM-DD.md` if task continuity matters
5. Load relevant `brain/` entities for named systems, concepts, or skills
6. Check `RUNTIME_LOGS_INDEX.md` if task touches ops, governance, or stack changes

---

## Preload questions
Before any downstream coding work:
- what is the task type?
- what memory is relevant?
- is this direct edit vs deeper coding work?
- is security or research needed first?
- what should be logged afterward?

---

## Rule
Jebat frames coding work before any downstream model or coding agent is used.
