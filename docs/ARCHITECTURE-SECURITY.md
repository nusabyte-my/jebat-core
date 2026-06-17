# JEBAT Security Layer — Architecture Document

**Status**: Implemented & Verified (2026-04-23)
**Scope**: Orchestrator security overlay, exposure controls, token budgets, policy enforcement
**Related**: `orchestrator.py`, `test_swarm_orchestrator.py`, `docs/NEXT-IMPROVEMENTS.md`

---

## 1. Brainstorm

### Problem
Multi-agent swarm execution lacked runtime risk governance. Tasks could proceed without:
- Knowing the risk level of the request
- Enforcing required security roles
- Limiting output size to prevent context bloat
- Detecting credential leaks or unsafe suggestions
- Blocking destructive critical operations

### Goals
- Classify task risk from description + parameters
- Auto-inject required roles (review, security, defense) for elevated risk
- Enforce critical task gate (explicit approval required)
- Trim agent outputs by role to keep bounded
- Scan and redact secrets in agent responses
- Flag unsafe deployment patterns
- Expose all of this as a first-class `security_layer` contract

### Non-Goals
- UI/UX (backend-only)
- Database schema changes (no persistence requirement)
- Real-time blocking at provider level (post-generation sanitization only)

---

## 2. Wireframing (System Flow)

```
[Task Request]
      |
      v
[Build Security Layer]  <-- _build_security_layer()
      |
      |  risk_level, triggers, required_roles, enforced
      v
[Apply Critical Policy] <-- _execute_task() gate
      |   (block if critical & not approved)
      v
[Route to Agent(s)] ----> Single | Swarm (full_orchestration)
      |
      v
[Agent Handler] ----> returns payload
      |
      v
[Sanitize]  <-- _sanitize_payload() + _flag_unsafe_output_paths()
      |   - redact credentials
      |   - collect exposure_findings
      |   - collect unsafe_warnings
      v
[Apply Token Budget] <-- _apply_output_budget(role)
      |   - trim summary/decision to token limits
      |   - limit/tail actions
      v
[Collect Executions]
      |
      v
[Build Security Summary] <-- _build_security_summary()
      |   - active_roles
      |   - required_roles_present
      |   - coverage_ok
      |   - recommended_controls
      |   - policy_rules (durable)
      |   - exposure_controls, exposure_findings, unsafe_warnings
      v
[Assemble Final Result]
      |
      v
{ reducer, doctrine, security_layer, agent_results }
```

---

## 3. DB Creation

No database schema changes required. Security layer is:
- Computed per-task at runtime
- Returned in API responses
- Not persisted (could be added later via `model_usage` table extension)

---

## 4. Workflow

### Planning Phase (`plan_task`)
- `_build_security_layer()` classifies risk
- Returns base security_layer (risk_level, triggers, required_roles, enforced)
- No runtime fields (active_roles, coverage_ok, exposure_*)

### Execution Phase (`execute_task`)
- Critical policy check before agent dispatch
- Per-agent sanitization and budget trim
- Aggregation of exposure findings across all agents
- `_build_security_summary()` adds runtime coverage and controls
- Final security_layer attached to swarm result

### API Surface
- `SwarmPlanResponse.security_layer` — plan-time classification
- `SwarmTaskResponse.security_layer` — runtime summary with exposure data
- `ChatResponse.security_layer` — propagated from swarm when routed

---

## 5. UI/UX

Not applicable (backend-only). Potential future UI:
- Admin dashboard showing security posture per task
- Drill-down into exposure findings
- Role budget configuration

---

## 6. Structural Worktree

**Files Modified**:
- `jebat-core/jebat/core/agents/orchestrator.py` — core implementation
- `jebat-core/test_swarm_orchestrator.py` — extended tests
- `jebat-core/test_swarm_api.py` — API contract tests
- `jebat-core/docs/NEXT-IMPROVEMENTS.md` — status update

**New Methods in Orchestrator**:
- `_build_security_layer()` — risk classifier
- `_build_security_summary()` — runtime aggregator
- `_apply_output_budget()` — token-based trim
- `_trim_to_token_budget()` — token estimator + binary search truncation
- `_scan_for_exposures()` — regex pattern matching
- `_sanitize_payload()` — recursive redaction
- `_flag_unsafe_output_paths()` — heuristic detection
- `_execute_single_task()` — updated to include runtime security summary

**New State**:
- `self.durable_doctrine` — durable policy (configurable)
- `self.security_policy_rules` — durable security rules (configurable)
- `self.exposure_patterns` — compiled regex patterns

---

## 7. File/Folder Tree (Changes)

```
jebat-core/
├── jebat/
│   └── core/
│       └── agents/
│           └── orchestrator.py        (+260 lines, core security layer)
├── test_swarm_orchestrator.py         (+120 lines, 12 new tests)
├── test_swarm_api.py                  (+40 lines, expanded contract)
└── docs/
    └── NEXT-IMPROVEMENTS.md           (status update)
```

---

## 8. Checklist

- [x] Risk classification (low/medium/high/critical) from keywords + params
- [x] Required role injection (review for medium+, security/defense for high+)
- [x] Critical task policy gate (block unless `approve_critical=True`)
- [x] Token-based per-role output budgets:
  - [x] security/defense/review: ~50 token summary, 30 token decision, max 3 actions
  - [x] standard roles: ~100 token summary, 60 token decision, max 5 actions
  - [x] reduction/sage: unlimited
- [x] Credential exposure detection (5 regex patterns)
- [x] Automatic redaction (`[REDACTED]`) in agent outputs
- [x] Unsafe output path detection (publish to npm, deploy public, etc.)
- [x] Exposure findings aggregated into `security_layer`
- [x] Doctrine/security policy split (durable on orchestrator, not per-agent)
- [x] Single-agent security summary (previously only swarm had runtime summary)
- [x] API contract coverage:
  - [x] plan endpoint returns base security_layer
  - [x] execute endpoint returns runtime security_layer
  - [x] reducer contract (decision, confidence, synthesized_decision, votes, conflicts)
  - [x] doctrine contract (doctrine_checks from durable list)
  - [x] security_layer schema (risk_level, triggers, required_roles, enforced, active_roles, required_roles_present, coverage_ok, recommended_controls, policy_rules, exposure_controls, exposure_findings, unsafe_warnings)
  - [x] critical execution blocking (policy_action=blocked)
- [x] All 27 tests pass (test_swarm_orchestrator.py)
- [x] Compile checks pass (orchestrator.py, jebat_api.py, test files)
- [x] Documentation updated (NEXT-IMPROVEMENTS.md)

---

## 9. Security

### Threat Model
- **Credential leakage**: Agent outputs may inadvertently include secrets → **Mitigation**: regex detection + redaction
- **Unsafe operations**: Agent may suggest public exposure → **Mitigation**: phrase detection + warnings
- **Critical task abuse**: Destructive tasks could be executed unintentionally → **Mitigation**: explicit approval gate
- **Context bloat**: Large agent outputs could overwhelm swarm synthesis → **Mitigation**: token-based per-role budgets

### Controls Implemented
1. **Input validation**: `_build_security_layer()` classifies risk; blocks critical tasks at entry
2. **Output sanitization**: `_sanitize_payload()` redacts patterns; `_flag_unsafe_output_paths()` adds warnings
3. **Budget enforcement**: `_apply_output_budget()` trims oversized responses by role
4. **Audit trail**: exposure_findings and unsafe_warnings recorded in security_layer for observability
5. **Durable policy**: `durable_doctrine` and `security_policy_rules` configurable, not prompt-injected

### Open Items
- Token budgets currently use estimator; could tighten with model-specific tokenizer
- Exposure patterns could be extended (environment variable names, connection strings)
- Could add rate-based detection (multiple exposures in single task = higher risk)
- Consider persisting security_layer to database for historical analysis

---

## 10. Orchestration & Handoff

The security overlay is now an **integrated orchestration layer**, not a post-processing step:

- **Planning**: risk classified, roles identified
- **Execution**: agents sanitized + budgeted, findings collected
- **Synthesis**: reducer/doctrine/security_layer all present in final payload
- **API**: all three surfaces (plan, execute, chat) expose security_layer consistently
- **Testing**: contract validated end-to-end; failure modes (critical block) tested

No further integration work required. The subsystem is self-contained and backwards-compatible (new fields added to responses, existing fields untouched).
