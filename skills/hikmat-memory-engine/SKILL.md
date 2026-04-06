# Hikmat Memory Engine — Persistent Memory Compression

**Role:** JEBAT's enhanced memory system
**Adapted from:** [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem)
**Type:** Enhancement to existing jebat-memory-skill

## What We Adopt

### 1. Persistent Context Engine
- Auto-captures tool usage observations during sessions
- Generates AI-compressed semantic summaries
- Injects relevant context into future sessions automatically
- Survives session restarts and reconnections with zero-touch operation

### 2. Progressive Disclosure (3-Layer Search)
Designed for ~10x token efficiency:

**Layer 1 — Compact Index** (50-100 tokens/result):
- Returns observation IDs with brief summaries
- Fast scan for relevant memories

**Layer 2 — Timeline** (200-500 tokens):
- Fetches chronological context around specific IDs
- Shows the narrative around a decision

**Layer 3 — Full Detail** (500-1000 tokens/result):
- Retrieves complete observation details
- Only fetch when deep context needed

### 3. Privacy Controls
- `<private>` tags exclude sensitive content from storage
- Automatic credential detection and redaction
- User-controlled memory boundaries

### 4. Real-Time Memory API
- Local HTTP API for memory operations
- Web viewer for browsing session history
- Citation IDs for all observations

## Integration with JEBAT M0-M4

```
claude-mem layer          → Maps to JEBAT layer
─────────────────────────────────────────────────
Session observations       → M1 Episodic
AI-compressed summaries   → M2 Semantic
Persistent patterns        → M3 Conceptual
Installation habits        → M4 Procedural
Sensory buffer (current)   → M0 Sensory
```

## MCP Search Tools (New)

Three tool endpoints to add to memory skill:

```
mem_search(query, max_results)
  → Compact index with observation IDs

mem_timeline(ids, window)
  → Chronological context around IDs

mem_get_observations(ids)
  → Full details for batched IDs
```

## Token Budget Strategy

| Operation | Token Cost | When |
|-----------|-----------|------|
| Compact search | 50-100 | Every message |
| Timeline fetch | 200-500 | When context needed |
| Full retrieval | 500-1000 | Only for deep dives |
| Summary generation | 200-400 | During consolidation |

## Implementation Notes

- Replace current file-based memory with SQLite + Chroma vector DB for hybrid search
- Add auto-capture hooks on tool use (PostToolUse lifecycle hook)
- Build memory API server (port 37777 equivalent, or integrate into existing API on 8000)
- Progressive disclosure is the key differentiator — most memory systems dump everything
