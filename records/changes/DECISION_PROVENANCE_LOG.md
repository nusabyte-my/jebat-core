
### 2026-03-30 — Adopt records tree for append-style operational outputs
- **Decision:** Adopt records tree for append-style operational outputs
- **Context:** Operational outputs were scattered at workspace root and needed a cleaner structure before workstation setup work continues
- **Evidence:** Created records/ops, records/security, records/tasks, records/changes and retargeted append-style helpers plus generated output writers
- **Alternatives considered:** Keep root-level markdown files as the primary append target
- **Outcome:** New helper defaults now write into records/ while preserving manual override capability via -TargetFile
- **Follow-up:** Optionally migrate historical root logs into records/ copies later

