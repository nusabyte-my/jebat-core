# Phase 3A Coding Control

## Goal

Make Jebat the default front controller for coding work in VS Code-style workflows.

---

## Core behavior
Before coding starts:
- Jebat loads context
- Jebat routes the task
- Jebat decides direct vs specialist path

After coding ends:
- Jebat verifies
- Jebat writes memory if needed
- Jebat appends provenance/lifecycle if needed

---

## Helper set
- coding task intake helper
- coding route helper
- coding verification helper
- coding memory writeback helper

---

## Rule
Jebat should be the control layer for coding tasks, not necessarily the only execution engine.
