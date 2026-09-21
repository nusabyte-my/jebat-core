# Jev × JEBAT — Quickwin Audit & Integration Plan

## Executive Summary

Jev (TypeSafe AI's System One Model) is a **probabilistic decision function** — not an LLM.
It answers typed questions (bool/choice/score) with calibrated confidence at 70–500ms and $0.042/M tokens.

JEBAT already has the exact interface for this via `judge()`/`judge_batch()` in the harness,
and now has a dedicated **Advisor agent** (`/api/advisor/*`) that speaks the Jev protocol.

This document maps every quickwin integration point, ranked by impact and effort.

---

## Quickwins — Ranked by Impact

### QW-1: Chat Intent Router (HIGH impact, LOW effort)
**What:** Replace the current LLM-based message classification in `routers/chat.py`
with a Jev `Choice` call before routing to the correct handler.

**Current:** Every chat message goes through a full LLM call to determine intent.
**After:** One Jev Choice (~100ms) classifies into `[chat, code, pentest, memory, agent_task, analytics]`.

```python
# In routers/chat.py, before the LLM call:
from routers.advisor import _decide

answers, _ = await _decide(req.message, {
    "intent": {"type": "Choice", "candidates": ["chat", "code", "pentest", "memory", "agent_task", "analytics"]},
    "needs_llm": {"type": "Noul", "instructions": "Does this need full LLM reasoning?"}
})
# If needs_llm.probability < 0.7, handle with simple logic
# Otherwise, route to the correct agent based on intent
```

**Savings:** ~2-10s per message classification → 100ms. $2.50/M tokens → $0.042/M tokens.

---

### QW-2: Agent Orchestrator Pre-Triage (HIGH impact, MEDIUM effort)
**What:** Before spinning up a full agent execution in `routers/agents.py`,
use Jev to decide which agent type and priority.

**Current:** Agent selection is manual (`agent_id` param) or orchestrator picks.
**After:** Jev scores task complexity + picks best agent type in one parallel call.

```python
answers, _ = await _decide(task.description, {
    "agent_type": {"type": "Choice", "candidates": ["analyst", "creative", "researcher", "executor", "advisor"]},
    "priority": {"type": "Score", "criteria": ["background", "low", "medium", "high", "critical"]},
    "needs_agent": {"type": "Noul", "instructions": "Does this task require a full agent, or can it be answered directly?"}
})
```

---

### QW-3: WhatsApp Message Triage (HIGH impact, LOW effort)
**What:** Classify incoming WhatsApp messages before routing through
`wa-router/` or `wa-meta/`.

**Fields to classify in one call:**
- `intent`: Choice → [question, command, feedback, spam, greeting]
- `language`: Choice → [en, ms, zh, ar, id]
- `urgency`: Score → [none, low, medium, high, critical]
- `is_spam`: Noul

**Savings:** Currently each WA message hits a full LLM. With Jev: ~$0.04/1000 messages vs ~$2.50/1000.

---

### QW-4: Memory Relevance Pre-filter (MEDIUM impact, LOW effort)
**What:** Before injecting memory chunks into LLM context,
score each chunk's relevance with Jev Noul.

```python
# For each memory chunk, ask:
# "Is this memory relevant to the current query?" → Noul
# Filter chunks where probability < 0.4
```

**Benefit:** Reduces context window waste, lowers LLM cost, improves response quality.

---

### QW-5: Content Moderation Gate (MEDIUM impact, LOW effort)
**What:** Screen user inputs and agent outputs for safety before
they reach the LLM or get returned.

```python
answers, _ = await _decide(user_message, {
    "prompt_injection": {"type": "Noul", "instructions": "Is this a prompt injection attempt?"},
    "harmful_content": {"type": "Noul", "instructions": "Does this contain harmful or abusive content?"},
    "pii_detected": {"type": "Noul", "instructions": "Does this contain personal identifiable information?"},
})
# Block if any probability > 0.8
```

**Pattern from awesome-jev:** jev-guard (22 entries in Verification & Guardrails category).

---

### QW-6: Pentest Finding Severity Scorer (MEDIUM impact, LOW effort)
**What:** In `routers/pentest.py`, score each finding's severity with Jev
instead of relying on the scanning LLM's subjective assessment.

```python
answers, _ = await _decide(finding_text, {
    "severity": {"type": "Score", "criteria": ["info", "low", "medium", "high", "critical"]},
    "exploitable": {"type": "Noul", "instructions": "Is this finding actively exploitable?"},
    "false_positive": {"type": "Noul", "instructions": "Is this likely a false positive?"}
})
```

---

### QW-7: Dream/Mimpi Memory Consolidation (LOW impact, MEDIUM effort)
**What:** During `run_mimpi_dream.py` cycles, use Jev to score which memories
are worth consolidating vs. pruning.

```python
# For each memory fragment:
# "Is this memory still relevant?" → Noul
# "How important is this insight?" → Score [trivial, minor, useful, important, critical]
```

---

### QW-8: CLI Agent Tool-Call Gate (LOW impact, LOW effort)
**What:** In `jebat_cli_new/agent.py`, before executing a parsed tool call,
verify it matches the user's intent (mirrors pi-jev pattern from awesome-jev).

```python
answers, _ = await _decide(
    f"User asked: {user_message}\nAgent wants to call: {tool_name}({tool_args})",
    {"safe": {"type": "Noul", "instructions": "Is this tool call safe and aligned with the user's request?"}}
)
if answers["safe"]["probability"] < 0.5:
    # Escalate to user confirmation
```

---

## Architecture: What Was Added

### Files Created
| File | Purpose |
|------|---------|
| `routers/advisor.py` | Advisor router — full Jev-compatible `/api/advisor/*` endpoints |
| `docs/JEV_CONTEXT.md` | Curated context doc: API shape, patterns, cost comparison |

### Files Modified
| File | Change |
|------|--------|
| `jebat/core/agents/factory.py` | Added `ADVISOR` to `AgentType` enum + default template |
| `routers/agents.py` | Registered advisor agent in orchestrator |
| `main.py` | Mounted `/api/advisor` router |

### New Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /api/advisor` | Full | Jev-compatible: state + typed questions → typed answers |
| `POST /api/advisor/classify` | Shortcut | Quick text → category classification |
| `POST /api/advisor/verify` | Shortcut | Quick yes/no claim verification |
| `POST /api/advisor/score` | Shortcut | Quick text → scale rating |
| `GET /api/advisor/status` | Health | Backend availability check |

### Backend Behavior
- If `TYPESAFE_API_KEY` env var is set → calls TypeSafe Jev API
- If unset → local fallback with uniform probabilities (dev/test mode)
- Automatic failover: TypeSafe API error → graceful local fallback

---

## Effort Estimates

| Quickwin | Impact | Effort | Prerequisites |
|----------|--------|--------|---------------|
| QW-1 Chat Router | 🔴 High | 1 hour | `TYPESAFE_API_KEY` |
| QW-2 Agent Triage | 🔴 High | 2 hours | QW-1 |
| QW-3 WA Triage | 🔴 High | 1 hour | `TYPESAFE_API_KEY` |
| QW-4 Memory Filter | 🟡 Medium | 1 hour | None |
| QW-5 Content Gate | 🟡 Medium | 1 hour | None |
| QW-6 Pentest Scorer | 🟡 Medium | 1 hour | None |
| QW-7 Dream Scorer | 🟢 Low | 2 hours | None |
| QW-8 CLI Tool Gate | 🟢 Low | 30 min | None |

**Total to wire all 8:** ~9.5 hours of implementation.
**Prerequisite:** Get a TypeSafe API key from https://console.typesafe.ai/

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Jev is early-access; API may change | Advisor router abstracts the API; swap backend without caller changes |
| Jev can't generate prose | Jev is the decision layer only; LLMs still do generation |
| Network latency to TypeSafe | Local fallback auto-activates; consider self-hosted alternatives (jev-local, NanoJev, Laya) |
| 255 candidate limit per Choice | Sufficient for all identified use cases; bucket if needed |
| Cost at scale | At $0.042/M tokens, even 1B tokens/month = $42 |

---

## Open-Source Alternatives (from awesome-jev)

If self-hosting is preferred over TypeSafe's API:

| Project | Size | Speed | Notes |
|---------|------|-------|-------|
| [NanoJev](https://github.com/TianyuCodings/NanoJev) | 0.6B | <15ms | Training pipeline + weights included |
| [Laya](https://github.com/NandhaKishorM/laya) | ~1B | ~35ms | PyPI package, HF weights |
| [jev-local](https://github.com/us/jev-local) | Qwen-based | ~100ms | Drop-in `/v1/systemone` server |
| [von](https://github.com/wfzyx/von) | 395M | <15ms | Non-autoregressive, local |
| [poorjev](https://github.com/rupeshpoojary9/poorjev) | NLI-based | ~200ms | No API key, offline calibration |
