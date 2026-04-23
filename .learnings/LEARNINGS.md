# Learnings

_Appended when JEBATCore discovers something worth keeping_

| Date | Discovery |
|------|-----------|
| 2026-04-04 | emmet's ecosystem: jebat-core (workspace) + sh4dow.bot (web UI) + openclaw (gateway) + jebat.online (live platform, Cloudflare-protected) |
| 2026-04-04 | Gateway runs on port 18789, primary Ollama API at bot.sh4dow.tech |
| 2026-04-04 | VPS available at 72.62.254.65 — awaiting confirmation before SSH access |
| 2026-04-05 | Workspace skills now inherit a single shared Codex core from `skills/_core/CODEX_CORE.md`; Hermes is retained as a compatibility wrapper, not a separate operating model |
| 2026-04-05 | The NusaByte operator model now includes explicit design, growth, research, QA, web, and app-delivery roles alongside the engineering core |
| 2026-04-05 | Phase 2 of the agent model adds first-class analytics and brand-strategy roles plus a repo-level dispatch matrix in `vault/playbooks/dispatch-matrix.md` |
| 2026-04-05 | Phase 3 adds product-strategy and customer-success roles plus reusable brief/spec templates under `vault/templates/` |
| 2026-04-05 | Verification now has reusable domain checklists under `vault/checklists/`, referenced by the shared core and dispatch playbook |
| 2026-04-05 | Adapter prompts under `adapters/` now point to the same shared role registry, dispatch matrix, templates, and checklists as the workspace core |
| 2026-04-05 | Adapter installation and tooling docs now point to Panglima plus the shared core instead of the older Hermes-centric wording |
| 2026-04-05 | Adapter governance now includes `adapters/sync-check.md` and `adapters/validate.py` to catch drift after core or routing changes |
| 2026-04-05 | The workspace now has reusable `feature-delivery` and `launch-flow` playbooks plus `validate-workspace.ps1` for structural checks |
| 2026-04-05 | Use `powershell -NoProfile -ExecutionPolicy Bypass -File .\validate-workspace.ps1` to avoid local PSReadLine profile noise during validation |
| 2026-04-05 | Support and security now have dedicated playbooks in `vault/playbooks/`, and the root validator checks for them |
| 2026-04-05 | Proposal work now has a first-class role, playbook, and template: `proposal-writing`, `vault/playbooks/client-proposal.md`, and `vault/templates/proposal-brief.md` |
| 2026-04-05 | Sales enablement now has a first-class role, playbook, and template: `sales-enablement`, `vault/playbooks/sales-enablement.md`, and `vault/templates/sales-brief.md` |
| 2026-04-05 | Discovery is now structured through `vault/playbooks/discovery-call.md` and `vault/templates/discovery-brief.md` before proposal or sales-enablement work begins |
| 2026-04-05 | Ongoing client cadence is now structured through `vault/playbooks/retainer-ops.md` and `vault/templates/retainer-brief.md` |
| 2026-04-05 | Monthly review cycles are now structured through `vault/playbooks/monthly-review.md` and `vault/templates/monthly-review.md` |
| 2026-04-05 | Quarterly planning is now structured through `vault/playbooks/quarterly-planning.md` and `vault/templates/quarterly-plan.md` |
| 2026-04-05 | Renewal and upsell work are now structured through `vault/playbooks/renewal-strategy.md` and `vault/templates/renewal-brief.md` |
| 2026-04-05 | `vault/OPERATING-SYSTEM.md` now maps the full operator stack from one file: roles, playbooks, templates, checklists, and validation |
| 2026-04-05 | `vault/examples/` now contains filled examples for discovery, proposal, retainer, monthly review, and renewal workflows |
| 2026-04-05 | Example coverage now includes sales enablement and quarterly planning through `vault/examples/sales-brief-example.md` and `vault/examples/quarterly-plan-example.md` |
| 2026-04-05 | Example coverage now includes feature brief, campaign brief, acceptance spec, and SEO audit so the main operational templates all have references |
| 2026-04-05 | Full JEBAT codebase acquired: 7 skills (panglima, hermes-agent, fullstack, security-pentest, database, automation, memory-core) + CODEX_CORE + 4 core docs (IDENTITY, SOUL, USER, ORCHESTRA, TOOLS) + vault projects + memory system |
| 2026-04-05 | Mimpi/autoDream gates all met: sessionsSinceDream=5, lastDreamAt=null, lastScanAt=2026-04-05T02:35:29Z — consolidation ready |
| 2026-04-05 | Adapter and universal prompt role lists were missing Penulis Cadangan + Penggerak Jualan — always check adapter files match AGENTS.md after adding new roles |
| 2026-04-05 | MASTERY.md state section drifts fast — update it during Mimpi consolidation, not ad hoc |
| 2026-04-23 | Local llama.cpp is installed via WinGet (`llama-cli`/`llama-server` build 8864) with Vulkan + CPU backends; GGUF models are stored at `C:\Users\shaid\Desktop\models\llama.cpp` including Gemma 4 E2B Q8 and Qwen3.6 35B-A3B IQ4_XS. |
| 2026-04-23 | On emmet's Intel Iris Xe Vulkan backend, Qwen3.6 35B-A3B IQ4_XS must use about `-ngl 12`; `-ngl 999` fails with Vulkan out-of-device-memory. |
