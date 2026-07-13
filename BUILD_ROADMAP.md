# JEBAT Build Roadmap

## Current Status (v8.1 — July 2026)

### ✅ FUNCTIONAL — Shipped and Working

| Module | Status | Notes |
|--------|--------|-------|
| Agent Loop (`core/agent_loop.py`) | ✅ FUNCTIONAL | Memory-integrated, working memory, cross-session, ContextManager, cost tracking, adaptive compaction |
| Ghost DB (`features/ghost_db/`) | ✅ FUNCTIONAL | SQLite + sqlite-vec, HNSW indexing, 3 chunkers, MCP server |
| Catalyst O11y (`features/catalyst/`) | ✅ FUNCTIONAL | OTel tracing, Prometheus, Loki, HALO, alerting, Grafana |
| SDK — Python (`jebat_sdk/python/`) | ✅ FUNCTIONAL | Sync/async clients, Pydantic models, testing mocks |
| SDK — TypeScript (`jebat_sdk/typescript/`) | ✅ FUNCTIONAL | Zod validation, React hooks, testing mocks |
| Enterprise RBAC (`features/rbac/`) | ✅ FUNCTIONAL | 3-tier hierarchy, 10 resource types, FastAPI routes |
| Mimpi Dream Engine (`features/mimpi/`) | ✅ FUNCTIONAL | 8 dream types, concept graph, 6-phase pipeline |
| Self-Learning (`features/self_learning/`) | ✅ FUNCTIONAL | UCB1 strategy selection, builtin strategies auto-registered |
| Enhanced Memory (`features/memory/`) | ✅ FUNCTIONAL | 6 types, forgetting curves, pattern extraction, Ghost DB vector search |
| Working Memory (`core/agent_loop.py`) | ✅ FUNCTIONAL | Goals, facts, constraints parsed from LLM output |
| Cross-Session Context | ✅ FUNCTIONAL | FTS5 search across past sessions |
| Branch Agents (`features/code_agent/`) | ✅ FUNCTIONAL | 4 isolation strategies, 5 orchestration modes |
| Cost Tracking (`features/cost_tracking/`) | ✅ FUNCTIONAL | Per-provider pricing, session/day/week aggregation, wired to agent loop |
| 17-Provider Router (`llm/providers.py`) | ✅ FUNCTIONAL | Auto-failover, health monitoring |
| MCP Server (`features/mcp/`) | ✅ FUNCTIONAL | 47 tools, stdio/HTTP/Streamable HTTP |
| Multi-Agent Swarm (`core/agents/orchestrator.py`) | ✅ FUNCTIONAL | 16 specialist agents, 4 execution modes |
| Ultra-Loop (`features/ultra_loop/`) | ✅ FUNCTIONAL | All 5 phases wired: Perception, Cognition, Memory, Action, Learning |
| ContextManager (`features/session/context.py`) | ✅ FUNCTIONAL | Token-aware context assembly, history compression, wired to agent loop |
| Adaptive Context Windowing | ✅ FUNCTIONAL | Importance-based compaction, memory-boosted retention |
| Enhanced Memory Encoding | ✅ FUNCTIONAL | Extracts decisions, files modified, errors from tool results |

### ⚠️ PARTIAL — Exists but Not Fully Wired

| Module | Status | What's Missing |
|--------|--------|----------------|
| Core Memory ↔ Enhanced Memory | ⚠️ PARTIAL | Bridge added in `manager.py` but sync is one-way (store only, search is substring fallback) |

### ❌ STUB — Not Implemented

(None — all P0 and P1 items completed)

---

## Build Priority — Next Sprint

### P0: Critical Path — ✅ COMPLETED

All three P0 items are now wired:

1. ✅ **Ultra-Loop**: All 5 phases real (Perception gathers messages, Cognition routes via DecisionEngine, Memory encodes via EnhancedMemorySystem, Action delegates to Orchestrator, Learning records via MetaLearner)
2. ✅ **Cost Tracker → Agent Loop**: `record_usage()` called after every LLM iteration with provider/model/tokens
3. ✅ **ContextManager → Agent Loop**: Replaces manual system prompt assembly; handles wiki/memory/history compression within token budget

### P1: High Impact — ✅ COMPLETED

All three P1 items are now implemented:

4. ✅ **Semantic Memory Search**: Ghost DB vector search integrated into `EnhancedMemorySystem.retrieve()`. Uses embedding-based similarity when available, falls back to n-gram. Traces indexed in Ghost DB on encode.
5. ✅ **Adaptive Context Windowing**: `_adaptive_compact()` scores messages by importance (system > tool calls > final answers > user questions > recent). Memory-boosted retention when recalled memories match content.
6. ✅ **Post-Run Memory Encoding**: Enhanced `_encode_run_memories()` now extracts: user intent + outcome (episodic), key decisions (semantic), files modified (procedural), errors encountered (episodic, high importance), significant tool results (procedural).

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

### P3: Polish — ✅ COMPLETED

9. ✅ **Context Budget Dashboard**: Grafana dashboard with token allocation pie chart, utilization gauge, compaction events, memory recall hits, working memory utilization, and cost-per-token by provider
10. ✅ **Working Memory Auto-Persistence**: Save/load working memory (goals/facts/constraints) to session DB across agent loop invocations

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
| `jebat/core/agent_loop.py` | ContextManager, CostTracker, adaptive compaction, working memory persistence, enhanced memory encoding |
| `jebat/features/ultra_loop/ultra_loop.py` | All 5 phases wired: Perception, Cognition, Memory, Action, Learning |
| `jebat/features/memory/__init__.py` | Ghost DB vector search, auto-indexing on encode |
| `jebat/core/memory/manager.py` | Async search method for enhanced memory bridge |
| `jebat/features/session/__init__.py` | Working memory persistence table and methods |
| `jebat/features/catalyst/dashboards.py` | Context Budget Dashboard (7 panels) |
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
