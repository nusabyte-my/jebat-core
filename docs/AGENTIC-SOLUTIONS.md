# Agentic Solutions & Agent Creation — Landscape and the nusabyte.bot Core

Status: research + design proposal · 2026-10-09 · owner: humm1ngb1rd / NusaByte.
Scope: how agents get created in 2025–2026, what JEBAT already ships (`jebat agentix`),
and the core architecture this points to for **nusabyte.bot**.

---

## 0. Ground rules

- Every market claim below carries a source (links in §7). Where a number comes from a
  tracker, the tracker and date are named.
- "Agentic solution" here means a **governed, deployable agent**: declared capability +
  bounded tools + budget + doctrine + a run record. Not a prompt, not a demo.

---

## 1. Market map

### 1.1 Platform layer

| Player | What they shipped | Read |
|---|---|---|
| **OpenAI** | AgentKit (2025-10-06): Agent Builder canvas, Evals, RFT for agents. Agents SDK evolves toward sandboxed file/command/code work for long-horizon tasks. Oct-2026 release notes track a public-beta Agents API plus plugin and Marketplace options. | Building the **visual + eval + marketplace** trio. |
| **Anthropic** | Agent Skills (2025-10-16): `SKILL.md` packages (instructions + resources), org-wide management, public directory. Donated MCP to the **Agentic AI Foundation** (Linux Foundation, 2025-12-09). | Skills are the **distribution format**; MCP is now neutral infrastructure. |
| **Google** | ADK: Python 2.0 GA (graph workflows, collaborative agents), TypeScript 2.0 GA, Go/Java 1.0. | Code-first framework, no marketplace play yet. |
| **Microsoft** | Agent Framework (AutoGen/SK lineage); Power Platform 2026 wave adds multi-agent orchestration + evaluations. | Enterprise-grade orchestration bolted to existing estates. |
| **IBM / UiPath / HCL / ServiceNow** | Agent builders + orchestration layered onto automation suites (watsonx Orchestrate, UiPath agentic suite, HCL UnO, ServiceNow AI Agents). | "Agentic" as the new SKU for RPA/iPaaS. |

### 1.2 Protocol + distribution layer

- **MCP**: current spec **2026-07-28** (stateless, sessionless scaling).
  Registry tracking shows **~125,400 servers** (mcpgrowth.den.dev, 2026-09-29) — the
  integration surface is now table stakes, not a differentiator.
- **Skills directories**: skills.sh leaderboard, claudeskil.com (~2,840 `SKILL.md`
  skills), multiple marketplace sites. `SKILL.md` is read across Claude Code, Codex CLI
  and compatible agents — a de-facto portable package.
- **Agent marketplaces**: OpenAI Marketplace (enterprise beta), Agent Mall, platform
  "agent stores" — distribution is the emerging moat, not the model.
- **Security research is catching up**: an ACM TOSEM survey on MCP landscape and
  security threats (tool poisoning class) — registrations need pinning and review.

### 1.3 Malaysia channel layer (adjacent to nusabyte.bot)

WhatsApp chat automation is **commoditized** in Malaysia: Wazzap, aiwhatsapp.com.my,
BMO (iCRM), iwsapp, 1000AI, WyraChat; Meta's own Business Agent configures in minutes.
The sharpest signal: **FlowAgent (Mampu AI) — "AI builds your AI chatbot"** — the
auto-creation angle is already being marketed locally.

Implication: nusabyte.bot cannot win as "another WhatsApp FAQ bot". It can win as a
**governed agent-solutions foundry** with channel delivery: objective → validated
solution → bot on the channel → audit + learning loop. The differentiation is the
foundry, the governance, and the evidence discipline — not the chat UI.

### 1.4 Domain-packaged agents — case study: REA

`morluto/rea` (MIT, ~35.6k stars, npm `rea-agents@6.1.0`, 133-tool catalog at the 5.0.0
checkpoint) ships **one MCP server + one skill** for reverse engineering across
binaries, JS/Electron, .NET, APK, firmware, and browsers. The anatomy is worth copying:

1. **Tools as an MCP server** (`npx -y rea-agents@6.1.0 mcp`), version-pinned.
2. **Workflow instructions as a skill** ("connect only when needed", route target first,
   work summary-first, finding ledger).
3. **Evidence discipline**: every conclusion distinguishes observations / inferences /
   unknowns; limitations shipped with results.
4. **Local-first**: analysis runs on the operator's machine.

This is exactly the shape our catalog solutions + MCP bridge already produce — REA is a
proof point for the pattern, and now a capability on the bus (see §3).

---

## 2. Agent-creation patterns (what actually exists)

| Pattern | Shape | Strengths | Weaknesses | Examples |
|---|---|---|---|---|
| Code framework | Python/TS constructs agents | full control | bespoke glue per project | LangGraph, CrewAI, ADK, MAF |
| Manifest + doctrine | declarative manifest + markdown doctrine, shared runtime | reviewable, versionable, bounded tools/budget | needs runner + registry | **JEBAT agentix** (reflex/flow/lattice) |
| Skill package | `SKILL.md` + resources | portable, cheap, human-editable | instructions only — no runtime, no budget | Claude Skills, skills.sh |
| Visual builder | canvas flows | fastest for mapping, non-devs | weak governance, lock-in | Agent Builder, watsonx, Power Platform |
| Auto-generated | LLM drafts the spec → deterministic gates → deploy | scales **solution creation itself** | gate quality decides everything | `jebat agentix auto` (shipped today) |

**Key insight**: distribution ≠ execution. Skills distribute expertise; MCP distributes
capability; a governed runtime executes, budgets, and records. nusabyte.bot should own
the foundry loop (create → gate → deploy → run → learn) and consume everyone else's
skills and MCP servers.

---

## 3. What shipped in JEBAT (2026-10-09)

1. **`reverse-engineer` specialist** — 23rd catalog template, REA-backed doctrine
   (classify target → ground in evidence → authorization → verify → mechanism-not-copy).
   Source of truth is `scripts/gen_agentix_specialists.py`; regenerate with
   `python scripts/gen_agentix_specialists.py`.
2. **REA on the MCP bus** — workspace configs now register `rea`
   (`npx -y rea-agents@6.1.0 mcp`) in `.vscode/mcp.json`, `.cursor/mcp.json`,
   `.agents/mcp.json`; the omp user config already carried it. Version is pinned;
   bump deliberately (REA pins registrations to the setup version).
3. **`jebat agentix auto "<objective>"`** — the solution foundry: one provider call
   drafts `{name, description, doctrine, tools, max_iterations, jailed}`, deterministic
   normalization + a build gate validate it, `--deploy local|mcp` wires it up.
   `draft=` injection keeps tests model-free.
4. **Agentix on the JEBAT MCP server** — new tools `agentix_list`, `agentix_create`
   (specialist copy or objective auto-draft), `agentix_deploy` (local registry or
   paste-ready per-solution MCP config). Writes sit at the `confirm` tier.
5. **CLI arg passthrough fix** — subcommand-owned flags now survive parsing
   (`jebat mcp serve --transport stdio` and `jebat agentix auto ... --name X` previously
   died with argparse exit 2; the workspace IDE configs use exactly this form).
   Regression test in `tests/test_cli_new_entrypoint.py`.
6. **Tests** — `tests/test_agentix_auto.py` (extraction, normalization, write/build,
   deploy validation; no model calls).
7. **NusaByte fleet on the bus** — `nusabyte-fleet` specialist (24th template) mirrors
   the Hermes front-door skill: routes work into `D:/nusabyte-hermes/bus/tasks/<queue>/inbox/`
   as `TASK-YYYY-MM-DD-NNN` briefs (bus-global ids, nb-bus compatible, approval gates
   intact). MCP tools: `fleet_agents` (registry — 24 agents with codenames),
   `fleet_tasks` (queue counts/backlog), `fleet_dispatch` (write a brief; confirm tier).
   Root override: `NUSABYTE_FLEET_ROOT`.
8. **MCP as agent solutions** — any configured MCP server becomes an instrument:
   - `mcp_describe` / `mcp_call` native loop tools (`jebat_cli_new/mcp_bridge.py`), config
     from `~/.jebat/config.yaml` (`mcp:` section, override `JEBAT_MCP_CONFIG`); optional
     per-server `require_approval: true` gate; one-shot session per operation on the
     shared transports (`jebat.features.mcp.mcp_client`).
   - `jebat agentix from-mcp <server>` (`agentix_mcp.py`): introspects the server's tool
     catalog, LLM-drafts a solution around the exact tools, forces
     `mcp_describe`/`mcp_call` into the allowlist, stores `mcp-snapshot.json` for diffing,
     builds; `--list` shows configured servers. MCP tool surface: `agentix_from_mcp`.
   - Transport fix: the stdio reader's default 64 KiB stream limit killed the reader on
     large catalogs (REA's 138-tool `tools/list` ≈ 1 MB single line) and every request
     then burned its full timeout — raised to 32 MiB, pending requests now fail fast on
     reader death.
   - Live receipts: REA introspected (138 tools, protocol `2025-11-25`); sequential-thinking
     called directly; `seq-ops` solution drafted+built+eval'd, then drove the server through
     the ReAct loop — 3 tool calls, self-corrected a `-32602` argument-nesting error from the
     MCP error feedback, reported the server's exact returned text.

Usage sketch:

```bash
jebat agentix auto "triage inbound supplier emails into a daily action memo" \
    --name supplier-triage --deploy local
jebat agentix run supplier-triage "run against inbox-export.md"
jebat agentix eval <path>                  # structural + golden gates
jebat agentix deploy <path> --target mcp   # per-solution MCP server config
jebat agentix from-mcp --list              # configured MCP servers
jebat agentix from-mcp rea --name rea-ops  # wrap an MCP server as a solution
```

---

## 4. nusabyte.bot — core architecture proposal

### 4.1 Thesis

**nusabyte.bot = NusaByte's agent-solutions foundry + multi-channel delivery.**
Malaysia-first (BM/EN/中文), sovereign deployment (own VPS/edge), evidence discipline
(no fabricated claims), and per-solution governance (tools, budget, audit). The
"foundry" is the product; the bot is the delivery surface.

### 4.2 Components (all map to existing repo assets)

| # | Component | Existing asset |
|---|---|---|
| 1 | Foundry — solution = manifest + doctrine + allowlist + budget; gates = build/validate + `eval` golden tasks | `jebat agentix` (+ `auto`), `agentix_ops` |
| 2 | Capability bus — JEBAT MCP (stateless 2026-07-28) + per-solution MCP servers + downstream domain MCPs (REA pattern) | `jebat/features/mcp`, `agentix_mcp_server`, hosted `mcp.jebat.online` |
| 3 | Channel gateway — message → solution routing, per-contact sessions, human handoff | `wa-router`, `wa-meta`, `wa-baileys` (WhatsApp first; Telegram later) |
| 4 | Memory + learning — project facts, session traces, dream consolidation, ops memos | AutoMimpi / SelfLearn, `ops-reporter` specialist |
| 5 | Governance — token/wall-clock budgets, tool allowlists, confirm tiers, run registry as audit trail, bearer-gated remote MCP | agentix budget gates, `~/.jebat/agentix/runs`, MCP auth |
| 6 | Distribution — export solution as skill or MCP server; publish to directories; per-tenant endpoints | `agentix export --format skill|claude-subagent`, `deploy --target mcp` |
| 7 | Fleet dispatch — route business/ops work to the 24-agent nusabyte-hermes fleet over its file task-bus (TASK ids, approval gates) | `nusabyte-fleet` specialist, `fleet_*` MCP tools, `bin/nb-bus` |

### 4.3 Phases

- **P0 — foundry hardening.** Golden tasks for the top specialists; `agentix auto` →
  `eval` gate in CI; fix the artifact-contract weakness from the 2026-10-05 finding
  (verifier legs blocked on weak local models — pin a stronger provider for
  drafting/verification, or demand the artifact as the first action).
- **P1 — one channel end-to-end.** WhatsApp (baileys/meta) → solution routing →
  per-contact session → human handoff → weekly ops memo from the run registry.
- **P2 — marketplace surface.** Per-solution MCP configs + skill exports; tenant
  registry; billing hooks (Stripe is already in the NusaByte stack).
- **P3 — multi-tenant governance.** RBAC, quotas, audit export, PDPA posture
  (PII endpoints guarded by default), per-tenant keys.

### 4.4 Risks (explicit)

- **Prompt injection via channel content** — bots read untrusted messages; constrain
  tools per solution, keep confirm tiers, never put secrets in memory files.
- **Weak-model artifact contracts** — auto-drafted solutions and team verifiers fail on
  local 7B models; the drafting/verification model is a product decision, not a detail.
- **Budget runaway** — foundry sets `budget.tokens`/`wall_clock`; run registry + ops
  memos watch failure rates and spend.
- **MCP supply chain** — pin versions (`rea-agents@6.1.0`), review new registrations,
  allowlist per client (tool-poisoning class is documented).
- **Evidence discipline is a feature** — REA-style "state what was NOT checked" must
  hold on every customer-facing claim; the copywriting gate bans fabricated metrics.

---

## 7. Sources

- OpenAI AgentKit: https://openai.com/index/introducing-agentkit/ · next Agents SDK: https://openai.com/index/the-next-evolution-of-the-agents-sdk · 2026 platform notes: https://releasebot.io/updates/openai
- Anthropic Agent Skills: https://claude.com/blog/skills · MCP donation (AAIF): https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation
- Skills directories: https://www.skills.sh/ · https://claudeskil.com/ · https://claude-marketplace.com/
- Google ADK: https://adk.dev/ · https://google.github.io/adk-docs/agents
- Microsoft Agent Framework / Power Platform 2026: https://www.damcogroup.com/blogs/building-ai-agents-using-microsoft-power-platform
- MCP spec + growth: https://modelcontextprotocol.io/docs/2026-07-28/getting-started/intro · https://mcpgrowth.den.dev/ · ACM survey: https://dl.acm.org/doi/abs/10.1145/3796519
- Agent builders landscape: https://blog.apify.com/ai-agent-builders/ · IBM: https://www.ibm.com/products/watsonx-orchestrate/ai-agent-builder · UiPath: https://www.uipath.com/newsroom/uipath-accelerates-ai-transformation-with-agentic-automation-and-orchestration
- Malaysia WhatsApp market: https://wazzap.my/ · https://aiwhatsapp.com.my/ · https://www.bmo.my/whatsapp-business-api-chatbot.php · https://mampuai.com/flow-agent · https://amast.com.my/wyrachat-ai-powered-whatsapp-automation
- REA: https://github.com/morluto/rea · https://rea.tools/ · skill: https://skills.sh/morluto/rea/reverse-engineer-anything
- Prior internal research: `competitor-profiles/_summary.md` (Dify, Open WebUI, Letta, OpenHands, PentAGI — 2026-08-29)
