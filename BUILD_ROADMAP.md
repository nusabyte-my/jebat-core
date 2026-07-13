# JEBAT Build Roadmap

## Current Status (v7.5 — July 2026)

### ✅ FUNCTIONAL — Shipped and Working

| Module | Status | Notes |
|--------|--------|-------|
| Agent Loop (`core/agent_loop.py`) | ✅ FUNCTIONAL | Memory-integrated, working memory, cross-session context |
| Ghost DB (`features/ghost_db/`) | ✅ FUNCTIONAL | SQLite + sqlite-vec, HNSW indexing, 3 chunkers, MCP server |
| Catalyst O11y (`features/catalyst/`) | ✅ FUNCTIONAL | OTel tracing, Prometheus, Loki, HALO, alerting, Grafana |
| SDK — Python (`jebat_sdk/python/`) | ✅ FUNCTIONAL | Sync/async clients, Pydantic models, testing mocks |
| SDK — TypeScript (`jebat_sdk/typescript/`) | ✅ FUNCTIONAL | Zod validation, React hooks, testing mocks |
| Enterprise RBAC (`features/rbac/`) | ✅ FUNCTIONAL | 3-tier hierarchy, 10 resource types, FastAPI routes |
| Mimpi Dream Engine (`features/mimpi/`) | ✅ FUNCTIONAL | 8 dream types, concept graph, 6-phase pipeline |
| Self-Learning (`features/self_learning/`) | ✅ FUNCTIONAL | UCB1 strategy selection, builtin strategies auto-registered |
| Enhanced Memory (`features/memory/`) | ✅ FUNCTIONAL | 6 types, forgetting curves, pattern extraction, consolidation |
| Working Memory (`core/agent_loop.py`) | ✅ FUNCTIONAL | Goals, facts, constraints parsed from LLM output |
| Cross-Session Context | ✅ FUNCTIONAL | FTS5 search across past sessions |
| Branch Agents (`features/code_agent/`) | ✅ FUNCTIONAL | 4 isolation strategies, 5 orchestration modes |
| Cost Tracking (`features/cost_tracking/`) | ✅ FUNCTIONAL | Per-provider pricing, session/day/week aggregation |
| 17-Provider Router (`llm/providers.py`) | ✅ FUNCTIONAL | Auto-failover, health monitoring |
| MCP Server (`features/mcp/`) | ✅ FUNCTIONAL | 47 tools, stdio/HTTP/Streamable HTTP |
| Multi-Agent Swarm (`core/agents/orchestrator.py`) | ✅ FUNCTIONAL | 16 specialist agents, 4 execution modes |

### ⚠️ PARTIAL — Exists but Not Fully Wired

| Module | Status | What's Missing |
|--------|--------|----------------|
| ContextManager (`features/session/context.py`) | ⚠️ PARTIAL | Exists but agent loop uses ad-hoc building. Needs to replace `_build_project_context_section` + memory injection |
| Cost Tracker ↔ Agent Loop | ⚠️ PARTIAL | CostTracker exists standalone. Not integrated into agent loop for budget enforcement |
| Ultra-Loop (`features/ultra_loop/`) | ⚠️ PARTIAL | Action phase works (calls orchestrator). Perception, Cognition, Memory, Learning phases are stubs |
| Memory ↔ Ghost DB | ⚠️ PARTIAL | Both exist separately. Memory traces have `embedding` field but no vector search via Ghost DB |
| Core Memory ↔ Enhanced Memory | ⚠️ PARTIAL | Bridge added in `manager.py` but sync is one-way (store only, search is substring fallback) |

### ❌ STUB — Not Implemented

| Module | Status | What's Needed |
|--------|--------|---------------|
| Ultra-Loop Perception Phase | ❌ STUB | Integrate with channel gateway for message ingestion |
| Ultra-Loop Cognition Phase | ❌ STUB | Wire to `core/decision/engine.py` for real decision processing |
| Ultra-Loop Memory Phase | ❌ STUB | Wire to `EnhancedMemorySystem.encode()` for cycle memory storage |
| Ultra-Loop Learning Phase | ❌ STUB | Implement performance analysis, strategy adaptation feedback loop |
| Adaptive Context Windowing | ❌ STUB | Importance-based retention, semantic compression, dynamic budget |
| Semantic Memory Search | ❌ STUB | Vector similarity search via Ghost DB HNSW index |
| Post-Run Memory Encoding | ⚠️ PARTIAL | Basic encoding exists but doesn't extract key decisions/facts from tool results |

---

## Build Priority — Next Sprint

### P0: Critical Path (This Week)

#### 1. Wire Ultra-Loop to Real Systems
**File**: `jebat/features/ultra_loop/ultra_loop.py`
**Lines**: 225-436

Replace stubs with real implementations:

```python
# Perception: integrate with channel gateway
async def perception_phase(self, context):
    inputs = {"timestamp": ..., "messages": [], "events": []}
    # Real: read from all active channels
    for channel in self.channels:
        msgs = await channel.get_new_messages()
        inputs["messages"].extend(msgs)
    context.outputs["perception"] = inputs

# Cognition: wire to decision engine
async def cognition_phase(self, context):
    perception = context.outputs.get("perception", {})
    if perception.get("messages"):
        decision = await self.decision_engine.decide(perception["messages"])
        context.outputs["cognition"] = decision

# Memory: wire to enhanced memory
async def memory_phase(self, context):
    cycle_data = json.dumps(context.outputs)
    await self.memory.encode(cycle_data, memory_type=MemoryType.EPISODIC)

# Learning: wire to self-learning
async def learning_phase(self, context):
    outcome = context.outputs.get("action", {})
    self.meta_learner.record_outcome(outcome)
```

#### 2. Wire Cost Tracker to Agent Loop
**File**: `jebat/core/agent_loop.py`
**Lines**: 686-690 (after token accumulation)

Add after token tracking:
```python
# Enforce cost budget
if self._cost_tracker:
    self._cost_tracker.add_usage(
        session_id=self.session_id,
        provider=used_provider,
        prompt_tokens=metadata.usage.get("prompt_tokens", 0),
        completion_tokens=metadata.usage.get("completion_tokens", 0),
    )
    if self._cost_tracker.check_budget(self.session_id):
        # Budget exceeded — halt loop
        break
```

#### 3. Replace Ad-Hoc Context with ContextManager
**File**: `jebat/core/agent_loop.py`
**Lines**: 574-598

Replace the manual system prompt assembly with:
```python
from jebat.features.session.context import ContextManager

ctx = ContextManager(max_tokens=self.max_context_tokens)
messages = ctx.build_messages(
    system_prompt=base_system_prompt,
    history=working_history,
    wiki_pages=wiki_context,
    memory_entries=memory_context,
)
```

### P1: High Impact (Next Week)

#### 4. Semantic Memory Search via Ghost DB
**File**: `jebat/features/memory/__init__.py`
**Lines**: 358-368 (in `retrieve()`)

Replace n-gram similarity with Ghost DB vector search:
```python
# In retrieve(), after type/strength filtering:
if self.ghost_db and trace.embedding:
    similar = await self.ghost_db.vector_search(
        query_embedding=await self._get_embedding(query.query_text),
        top_k=5,
    )
    # Use vector similarity instead of n-gram
    similarity = vector_score(trace.embedding, similar)
```

#### 5. Adaptive Context Windowing
**File**: `jebat/core/agent_loop.py`
**New function**: `_adaptive_compact()`

Replace `_compact_conversation_history()` with importance-aware version:
```python
def _adaptive_compact(messages, max_tokens, memory_system):
    # Score each message by importance
    scored = []
    for msg in messages:
        importance = 0.5  # default
        # Boost: system messages, recent messages, messages with tool calls
        if msg["role"] == "system": importance += 0.3
        if msg == messages[-1]: importance += 0.2
        if "Action:" in msg["content"]: importance += 0.1
        # Boost: messages referenced in memory
        if memory_system and memory_system.is_recalled(msg["content"]):
            importance += 0.2
        scored.append((importance, msg))
    
    # Sort by importance, keep top N within budget
    scored.sort(reverse=True)
    result = []
    budget = max_tokens
    for importance, msg in scored:
        tokens = len(msg["content"]) // 4
        if tokens <= budget:
            result.append(msg)
            budget -= tokens
    
    # Re-sort chronologically
    return sort_chronologically(result)
```

### P2: Medium Impact (Week 3)

#### 6. Post-Run Memory Encoding Enhancement
**File**: `jebat/core/agent_loop.py`
**Function**: `_encode_run_memories()`

Enhance to extract:
- Key decisions made
- Files modified
- Errors encountered and resolved
- User preferences discovered

#### 7. Working Memory Auto-Persistence
**File**: `jebat/core/agent_loop.py`

Save working memory state to session DB so it persists across agent loop invocations within the same session.

#### 8. Ultra-Loop Learning Phase
**File**: `jebat/features/ultra_loop/ultra_loop.py`

Implement:
- Track task outcomes (success/failure, duration, tokens)
- Feed to MetaLearner for strategy adaptation
- Extract patterns from repeated approaches
- Update concept graph with new associations

### P3: Polish (Week 4)

#### 9. Memory Consolidation Scheduling
Wire the background consolidation loop to run after every N agent runs instead of on a fixed timer.

#### 10. Context Budget Dashboard
Expose token usage breakdown (system/memory/history/working) via Catalyst O11y metrics.

#### 11. Cross-Session Memory Summaries
Auto-generate session summaries and store as semantic memories for faster recall.

---

## Architecture After All Builds

```
┌─────────────────────────────────────────────────────────┐
│                    L0 — INTERFACE                        │
│  WebUI │ CLI │ MCP (47 tools) │ SDK (Py+TS) │ REST     │
├─────────────────────────────────────────────────────────┤
│                    L1 — AGENTS                          │
│  ReAct Loop │ Ultra-Think │ Swarm │ Branch │ Spec-Dev  │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Working Memory Buffer (goals/facts/constraints) │    │
│  │ Adaptive Context Windowing (importance-based)   │    │
│  │ Cost-Aware Budget Enforcement                   │    │
│  └─────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────┤
│                    L2 — PRODUCTS                         │
│  Core │ Sentinel │ DevSuite │ Companion │ Nexus         │
├─────────────────────────────────────────────────────────┤
│                    L3 — COGNITION                        │
│  6-Type Memory │ Ghost DB │ Mimpi │ Self-Learning       │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Memory ↔ Ghost DB (vector search)               │    │
│  │ Post-Run Auto-Encoding                          │    │
│  │ Consolidation Scheduling                        │    │
│  └─────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────┤
│                    L4 — INFRASTRUCTURE                   │
│  17-Provider Router │ MCP Bus │ Catalyst O11y │ RBAC    │
├─────────────────────────────────────────────────────────┤
│                    L5 — RUNTIME                          │
│  SQLite+sqlite-vec │ Ollama │ Docker │ Air-Gapped      │
└─────────────────────────────────────────────────────────┘
```

---

## File Change Summary

| File | Changes |
|------|---------|
| `jebat/features/ultra_loop/ultra_loop.py` | Replace 4 stub phases with real implementations |
| `jebat/core/agent_loop.py` | Wire ContextManager, CostTracker, adaptive compaction |
| `jebat/features/memory/__init__.py` | Add Ghost DB vector search to retrieve() |
| `jebat/core/memory/manager.py` | Bidirectional sync with enhanced memory |
| `jebat/features/session/context.py` | Add importance scoring, dynamic budget |
| `landing.html` | Update capabilities section |
| `PITCH.md` | Update roadmap section |
| `BUILD_ROADMAP.md` | This file |

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Ultra-Loop phases functional | 1/5 | 5/5 |
| Context budget utilization | ~60% wasted | <20% wasted |
| Memory recall relevance | n-gram only | Vector + n-gram |
| Cost enforcement | None | Per-session budget |
| Cross-session context | FTS5 only | FTS5 + semantic |
| Agent loop token efficiency | ~40% overhead | <15% overhead |
