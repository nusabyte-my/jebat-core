# DESIGN.md

## Workspace (top-level tree)

Purpose:
- Canonical source of truth for the workspace; the top-level tree is what runs and what changes
- `jebat-core/` (frozen 2026-07-04) was removed on 2026-09-30; its visual direction carries on in the top-level tree
- Its docs, generated interfaces, and setup experiences define the tone for the rest of the stack

Visual direction:
- Terminal-native, black/emerald/cyan identity
- Strong information hierarchy
- Premium technical minimalism, not startup landing-page aesthetics

Priority surfaces:
- setup flows
- status / doctor / health views
- memory and vault tooling
- orchestration and admin panels

Rules:
- Default to dense, useful layouts
- Make system state visible
- Prefer utility and correctness over decorative UI
