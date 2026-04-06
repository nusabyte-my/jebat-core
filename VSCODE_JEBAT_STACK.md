# VS Code Jebat Stack

## Role

Jebat acts as the editor-first control layer.

It should:
- load context first
- decide routing
- set constraints
- close the loop after downstream work

---

## Stack layers

### 1. Bootstrap layer
Files:
- `VSCODE_JEBAT_BOOTSTRAP.md`
- `JEBAT_CONTROL_PANEL.md`
- `JEBAT_STATUS.md`
- relevant memory and brain entries

### 2. Dispatch layer
File:
- `VSCODE_DISPATCH_POLICY.md`

Purpose:
- choose local vs specialist vs coding vs research vs security flow

### 3. Execution layer
Uses:
- Jebat native helpers
- OpenClaw tools
- downstream coding/research/security engines where justified

### 4. Post-run layer
File:
- `VSCODE_POSTRUN_FLOW.md`

Purpose:
- verify
- persist memory
- append provenance/lifecycle when needed
- update task state

---

## Principle

Jebat should be the framing intelligence before other models, and the integrating intelligence after them.
