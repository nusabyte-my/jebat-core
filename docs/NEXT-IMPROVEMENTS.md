# JEBAT Next Improvements

Updated: 2026-04-23

This document captures the next structural improvements for JEBAT after the latest shift toward full automatic swarm orchestration.

## Structural Update

JEBAT is no longer just improving chat UX or CLI polish. The active direction is a layered orchestration system.

### 1. Runtime And Gateway Layer

- `packages/create-jebat-app/` is becoming the install, doctor, health, runtime-detection, and workspace-management surface.
- `jebat-agent` and `jebat-gateway` are turning into the operational bootstrap layer.
- This layer makes the rest of the system deployable, repeatable, and supportable.

### 2. Chat And Model-Routing Layer

- The chat UI is moving away from generic local-model behavior into explicit JEBAT routing.
- `jebat/*` models and Ollama models now follow different paths.
- Compare/orchestration mode has been simplified to reduce timeout risk before larger swarm expansion.

### 3. Agent Orchestration Layer

- Full orchestration is becoming the default operating model.
- Tasks should no longer behave like isolated single-agent jobs.
- `AUTO` should resolve into swarm or consensus execution by default.
- Support roles such as orchestration, review, and intelligence should be injected automatically.
- A pinned agent should act as preferred lead inside the swarm, not as a single-agent bypass.

### 4. Legendary Command Layer

The named agents form a command structure, not just a themed registry.

- `Hang Tuah` -> strategy
- `Hang Lekiu` -> reconnaissance
- `Hang Lekir` -> defense
- `Hang Kasturi` -> stability
- `Hang Nadim` -> intelligence and routing

This creates the basis for hierarchical orchestration rather than flat agent selection.

### 5. Skill And Specialization Layer

- TokGuru skills should operate as agent loadouts, not just a passive registry.
- Each major agent family should carry a bounded skillset with a defined token budget.
- The design agent already has a clearer bundle with `logo-generator` and `web-asset-generator`.
- The same pattern should expand to research, security, gateway, coding, and synthesis agents.

### 6. Doctrine And Reduction Layer

This is the missing top layer and should become explicit.

- `Tok Guru Adi Putera` should be the global sage layer.
- Responsibilities: doctrine, long-memory framing, guardrails, high-level context, and override advice.
- `Taming Sari` should be the core powerful keris of the orchestration system.
- Responsibilities: final reduction, conflict resolution, confidence scoring, and merged judgment across all agent outputs.

With these two additions, the swarm becomes a disciplined command system instead of many agents replying independently.

## Full-Orchestration Target Model

The intended orchestration flow should look like this:

1. `Hang Nadim` classifies the task, decomposes it, and decides whether standard or legendary orchestration is needed.
2. `Hang Tuah` owns strategy, primary task shape, and the overall execution frame.
3. Specialists receive scoped sub-jobs and execute in parallel on their own bounded context.
4. Support agents provide orchestration, review, and intelligence overlays where needed.
5. `Taming Sari` reduces all outputs into one coherent result with confidence and conflict handling.
6. `Tok Guru Adi Putera` acts as the long-context doctrine and wisdom layer over the whole system.

## Re-improvised Optimization Order

Because JEBAT is moving toward automatic multi-agent orchestration, token optimization must become orchestration-aware, not only chat-aware.

### 1. Accurate Token Telemetry

- Use provider `usage` when available.
- Otherwise tokenize with the real tokenizer for the active model, not `split()`.
- Persist prompt, completion, cached, and per-agent token usage into `model_usage`.
- This remains the first priority because all later optimization depends on correct measurement.

### 2. Conditional Prompt Profiles

- Simple prompts should use a lean profile: minimal context, short constraints, no examples.
- Deep analysis, security, review, and architectural prompts can use richer profiles.
- Prompt enhancement should become policy-driven instead of always-on.

### 3. Rolling Conversation Summary

- Keep only the last 2-4 raw turns.
- Summarize older history into a compact state block.
- This remains the highest-leverage token optimization for long-running conversations.

### 4. Orchestration-Aware Context Budgets

- Not every swarm agent should receive the full prompt.
- Each role should receive only its scoped context.
- Recon gets discovery context.
- Defense gets risk and hardening context.
- Stability gets rollout and failure-mode context.
- Review gets synthesis context.
- Strategy gets the minimum needed for direction setting.

Without this, full swarm mode multiplies token waste.

### 5. Skill Payload Compression

- Reduce default skill injection from 3 skills to 1-2.
- Inline full guidance only for the top-ranked skill.
- Use short summaries and source names for secondary skills.
- Keep the skill body available for explicit deep mode rather than default mode.

### 6. Task-Based Output Budgets

- Lightweight compare: `64-96`
- Normal chat: `96-128`
- Code, refactor, review, or research: raise only when needed
- Swarm sub-agents should usually have lower output caps than the final synthesizer

### 7. Final Reducer Model

- Swarm agents should return compact findings instead of long prose.
- Expansion should happen once at the end, not separately inside every agent.
- `Taming Sari` is the natural reducer for this role.

### 8. Doctrine-Memory Split

- Long-lived doctrine should be separate from rolling chat history.
- Operator context, guardrails, and durable behavior should not be re-injected as raw chat every turn.
- `Tok Guru Adi Putera` should provide a short durable doctrine block rather than repeated large prompts.

### 9. Caching And Deduplication

- Cache normalized prompt + model + summary-state combinations.
- Reuse search results and prior swarm summaries where the task shape is similar.
- This becomes materially more useful once telemetry is accurate.

### 10. User-Visible Budget Controls

- Expose modes such as `lean`, `balanced`, `deep`, `swarm`, and `legendary`.
- Let users intentionally trade off cost, latency, and depth.

## Best Optimization Order

If implementation has to be prioritized for fastest real gain, do these first:

1. Accurate token telemetry
2. Conditional prompt profiles
3. Rolling conversation summaries
4. Orchestration-aware context budgets

These four produce larger savings than reducing `max_tokens` alone.

## Suggested Next Implementation Sequence

### Phase A: Measurement And Budget Control

- Replace approximate token counting with provider usage or real tokenizer counts.
- Persist request, response, cache, and per-agent token metrics.
- Add task-mode budgets and resolved execution budget reporting.

### Phase B: Prompt And Memory Compression

- Add lean vs deep prompt-enhancement profiles.
- Reduce memory injection from long freeform text to compact fact blocks.
- Add rolling conversation summarization.

### Phase C: Orchestration-Aware Dispatch

- Split task context by role instead of broadcasting the same full prompt to every agent.
- Make `Hang Nadim` the default decomposition and routing entrypoint.
- Keep pinned agents as leads inside the swarm rather than isolated execution targets.

### Phase D: Final Synthesis And Doctrine

- Add `Taming Sari` as the final reducer and confidence judge.
- Add `Tok Guru Adi Putera` as the doctrine and wisdom layer.
- Route final user-facing output through this synthesis path for consistency.

## Implementation Checklist

### Phase A: Measurement And Budget Control

- [ ] Replace `split()` token counting with normalized provider usage where available.
- [ ] Add best-effort tokenizer-based fallback counting for non-provider or local paths.
- [ ] Expose normalized token usage in chat and OpenAI-compatible responses.
- [ ] Carry provider, model, and token metadata through the LLM runtime.
- [ ] Add task-mode output budget defaults and preserve explicit caller overrides.

### Phase B: Prompt And Memory Compression

- [ ] Add lean vs deep prompt profiles selected from task shape and mode.
- [ ] Reduce default memory injection to compact fact blocks instead of long raw context.
- [ ] Add rolling conversation summaries with only the last 2-4 raw turns retained.
- [ ] Use summarized conversation state in the OpenAI-compatible chat path.
- [ ] Keep prompt structure compact by default and only expand it for deep/security/review tasks.

### Phase C: Orchestration-Aware Dispatch

- [ ] Give each swarm agent a scoped task context instead of broadcasting the same full prompt.
- [ ] Use role-specific focus for search query generation.
- [ ] Surface the scoped task focus in built-in agent outputs for inspection and testing.
- [ ] Keep pinned agents as preferred leads inside swarm execution.
- [ ] Align inferred swarm defaults with full orchestration defaults.

### Phase D: Skill Payload Compression

- [ ] Lower automatic skill injection from 3 skills to 1-2 skills by default.
- [ ] Inline full guidance only for the top-ranked skill.
- [ ] Convert secondary skills to short summaries with source references.
- [ ] Keep explicit requested skills pinned ahead of auto-discovered skills.

### Phase E: Final Synthesis And Doctrine

- [ ] Introduce `Taming Sari` as the reducer/conflict-resolution stage.
- [ ] Introduce `Tok Guru Adi Putera` as the doctrine and long-memory layer.
- [ ] Route final user-facing synthesis through the reducer rather than every agent writing full prose.
- [ ] Separate durable doctrine context from rolling chat history.

## Current Implementation Status

This section is the handoff note for other LLMs or future sessions.

### Completed In Code

- [x] Added normalized token usage handling in `jebat/llm/token_usage.py`.
- [x] Added rolling conversation preparation and prompt profiles in `jebat/llm/conversation.py`.
- [x] Updated `jebat/llm/providers.py` to return provider-backed usage metadata where available.
- [x] Updated `jebat/llm/chat_runtime.py` to support prepared prompts, rolling summaries, and runtime metadata.
- [x] Reduced default skill payload in `jebat/llm/skills.py` to 2 skills with full guidance only for the top skill and summaries for secondary skills.
- [x] Updated `jebat/services/api/jebat_api.py` to use normalized token usage instead of `split()` counting.
- [x] Added best-effort `model_usage` persistence from the API path when the database is available.
- [x] Updated swarm routing defaults so inferred swarm tasks start from the 5-agent baseline.
- [x] Added role-scoped swarm context in `jebat/core/agents/orchestrator.py` and `jebat/core/agents/execution_adapters.py`.
- [x] Added `Taming Sari` (`reduction`) and `Tok Guru Adi Putera` (`sage`) as built-in orchestrator agents.
- [x] Added reducer/doctrine payload surfaces into swarm results.
- [x] Added a risk-based `security_layer` overlay in `jebat/core/agents/orchestrator.py`.
- [x] High-risk tasks now auto-inject `review`, `security`, and `defense` roles into full orchestration.
- [x] Swarm execution now returns runtime security coverage, active roles, and recommended controls.
- [x] API responses now expose `security_layer` on plan, execute, and swarm-routed chat responses.
- [x] Installed `pytest` and lightweight runtime deps into workspace-local `.venv` for local verification.

### Verified

- `python3 -m py_compile` passed on the touched orchestrator, API, and LLM modules.
- `python3 jebat-core/test_swarm_orchestrator.py` passed after the reducer-first formatter, doctrine exposure, and security-layer overlay changes.
- `.venv/bin/python -m pytest jebat-core/test_llm_cli.py -q` passed with `15 passed`.

### Security Layer

The security overlay is now an active orchestration layer, not only a plan-time classifier.

- Risk is classified as `low`, `medium`, `high`, or `critical` from task content and explicit parameters.
- Elevated-risk tasks automatically inject security roles into the swarm.
- The swarm result exposes:
  - `risk_level`
  - `triggers`
  - `required_roles`
  - `active_roles`
  - `required_roles_present`
  - `coverage_ok`
  - `recommended_controls`
- This gives downstream callers a first-class security posture object instead of forcing them to infer risk from raw agent output.

### Summary Of Current State

JEBAT now has these active orchestration layers in code:

- Runtime/gateway bootstrap
- chat/model routing
- full automatic swarm orchestration
- legendary command agents
- reducer and doctrine surfaces
- risk-based security overlay

### Immediate Next Step — COMPLETED 2026-04-23

The following have been implemented and verified:

1. ✅ **API contract tests** — `test_swarm_api.py` added; validates reducer.result.decision/confidence/actions, doctrine.result.doctrine_checks, and full security_layer schema including policy_rules
2. ✅ **Critical task policy gate** — `_build_security_layer` adds policy_action/approval_required for critical risk; `_execute_task` blocks and returns clear error unless `approve_critical=true` in parameters
3. ✅ **Role-specific output budgets** — `_apply_output_budget` trims security/defense/review to ≤3 actions and ≤200 char summaries; reduction/sage remain untrimmed; applied in `_run_task`
4. ✅ **Durable doctrine/security split** — Orchestrator loads `durable_doctrine` and `security_policy_rules` from config; `_build_doctrine_payload` uses durable list; `_build_security_summary` adds `policy_rules` field

All existing tests pass; new tests added to `test_swarm_orchestrator.py`:
- `test_critical_task_requires_explicit_approval`
- `test_critical_task_approved_executes`
- `test_role_specific_output_budgets`

Compile and runtime verification complete.

## Immediate Outcome To Target

The near-term goal is not just lower token usage. The goal is a swarm that:

- routes every task automatically
- keeps each agent on bounded scoped work
- reduces duplicated context
- merges results once through a strong reducer
- stays governed by one doctrine layer
- exposes risk posture and required controls as part of the orchestration contract

## Open Items From Phase A–D Roadmap

**All Phase A–E structural improvements are complete and orchestrated.**

### Completed in this session (2026-04-23)

- ✅ Token-based per-role output budgets (orchestrator.py:1253-1312) — `_trim_to_token_budget`, `_apply_output_budget`
- ✅ Secret/data exposure controls — regex detection, redaction, unsafe path flagging; aggregated into security_layer.exposure_controls, exposure_findings, unsafe_warnings
- ✅ Doctrine/security policy split — durable_doctrine and security_policy_rules on orchestrator; only referenced in final synthesis, never injected per-agent
- ✅ Expanded API contract tests — plan vs execution schema separation, reducer required fields, doctrine durability, security_layer policy_action & exposure controls

### Architecture Documentation

- **ARCHITECTURE-SECURITY.md** created — covers brainstorm, wireframing, workflow, structural worktree, file/folder tree, checklist, security. Fully integrated.

### Orchestration Status

- All 27 tests pass (test_swarm_orchestrator.py)
- API contract tests pass (test_swarm_api.py)
- Compile checks OK
- Docs updated (MASTER_INDEX.md, NEXT-IMPROVEMENTS.md)
- Tasks updated (tasks/todo.md, tasks/lessons.md)

**Next phase**: Q2 2026 Infrastructure — Monitoring Dashboard (see ROADMAP.md). Requires new architecture doc before implementation.

Near-term focus should be the secret/data exposure controls and token-budget enforcement before expanding phase D synthesis refinement.
