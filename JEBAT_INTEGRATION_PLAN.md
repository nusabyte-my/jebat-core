# JEBAT Integration Plan

**Created:** 2026-03-29
**Repository:** https://github.com/nusabyte-my/jebat-core.git
**Goal:** Adapt JEBAT core to OpenClaw gateway and rebuild jebat.online

---

## Overview

We're integrating JEBAT's sophisticated memory system and agent orchestration with OpenClaw's multi-channel gateway to create a production-ready self-hosted AI assistant platform.

---

## Phase 1: Skill Adaptation (Priority)

### 1.1 Memory Skills

**`skills/jebat-memory-skill/SKILL.md`**
- Store memories in 5 layers (M0-M4)
- Search across all memory layers
- Heat-based importance scoring
- Memory pinning and linking

**`skills/jebat-consolidation-skill/SKILL.md`**
- Automatic memory consolidation
- Promotion/demotion based on heat scores
- Cross-layer migration
- Scheduled via cron jobs

### 1.2 Agent Skills

**`skills/jebat-agent-orchestrator/SKILL.md`**
- Multi-agent coordination
- Task decomposition
- Agent selection based on capabilities
- Council deliberation mode

**`skills/jebat-analyst/SKILL.md`**
- Data analysis
- Pattern recognition
- Report generation
- Insight extraction

**`skills/jebat-researcher/SKILL.md`**
- Web research
- Information synthesis
- Fact verification
- Source attribution

### 1.3 Utility Skills

**`skills/jebat-heat-calculator/SKILL.md`**
- Calculate heat scores for memories
- Weighted importance scoring
- Decay rate management
- Cross-reference tracking

---

## Phase 2: Memory System Integration

### 2.1 OpenClaw Memory Enhancement

Extend `MEMORY.md` with JEBAT patterns:

```markdown
## Memory Layers

### M0: Sensory Buffer (0-30s)
- Raw sensory data, temporary context
- Auto-expires, no persistence

### M1: Episodic (hours)
- Specific events, conversations
- Temporal: "What happened yesterday?"
- Consolidates to M2 after 24h if heat ≥ 0.8

### M2: Semantic (30 days)
- Facts, concepts, relationships
- Extracted from episodic memories
- "Alice prefers morning meetings"

### M3: Conceptual (permanent)
- Abstract patterns, principles
- "Users value privacy over convenience"
- Never expires, rarely deleted

### M4: Procedural (permanent)
- Skills, workflows, habits
- "Process for client onboarding"
- Skill execution patterns
```

### 2.2 Heat Scoring Integration

Implement in OpenClaw tools:
- Visit tracking for memory recall
- Interaction depth measurement
- Recency decay curves
- Cross-reference graph

### 2.3 Consolidation Automation

Set up cron jobs:
```yaml
- name: "Memory Consolidation"
  schedule:
    kind: "every"
    everyMs: 3600000  # Every hour
  payload:
    kind: "agentTurn"
    message: "Run memory consolidation. Promote M1→M2 if heat ≥ 0.8, demote M2→M1 if heat < 0.4. Update heat scores for all memories."
  sessionTarget: "isolated"
```

---

## Phase 3: Platform Rebuild (jebat.online)

### 3.1 Architecture

```
┌─────────────────────────────────────────────┐
│         jebat.online Web Platform           │
│  - Landing page with hero section           │
│  - Documentation portal                     │
│  - Dashboard for stats & monitoring         │
│  - API reference                           │
│  - Download & installation guides          │
└──────────────────┬──────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
         ▼                   ▼
┌─────────────────┐  ┌─────────────────┐
│  JEBAT Core     │  │  OpenClaw GW    │
│  - Memory Sys   │  │  - Multi-ch     │
│  - Agent Orch   │  │  - Gateway      │
│  - Skills       │  │  - Security     │
└─────────────────┘  └─────────────────┘
         │                   │
         └─────────┬─────────┘
                   ▼
        ┌─────────────────────┐
        │  TimescaleDB/Redis   │
        │  - Memory storage   │
        │  - Session cache    │
        └─────────────────────┘
```

### 3.2 Core Pages

1. **Landing Page** (`index.html` - exists, enhance)
   - Hero: "Your AI. Your Data. Your Legacy."
   - Features grid with icons
   - Architecture diagram
   - Quick start terminal
   - Discord community CTA

2. **Documentation** (`/docs`)
   - Quick Start Guide
   - Installation Guide
   - Configuration Reference
   - Memory System Deep Dive
   - Skill Development
   - Agent Customization
   - Multi-Channel Setup
   - Deployment Guide

3. **Dashboard** (`/dashboard` - new)
   - Active sessions
   - Memory statistics (by layer)
   - Agent status
   - Channel status
   - Recent activity feed
   - Heat score visualization

4. **API Reference** (`/api` - new)
   - REST endpoints
   - WebSocket protocol
   - Webhook format
   - Authentication methods

5. **Download Center** (`/download` - new)
   - NPM package
   - Docker images
   - Source code releases
   - Installation scripts

### 3.3 Tech Stack

- **Frontend:** Next.js (React) + Tailwind CSS + shadcn/ui
- **Backend:** Next.js API Routes + OpenClaw Gateway
- **Database:** TimescaleDB (PostgreSQL) for memories
- **Cache:** Redis for sessions
- **Auth:** JWT tokens
- **Deployment:** Docker + Docker Compose

---

## Phase 4: Configuration & Setup

### 4.1 OpenClaw Config (~/.jebat/config.yaml)

```yaml
agent:
  model: "zai/glm-4.7"
  temperature: 0.7
  thinking: "medium"

memory:
  system: "jebat-core"
  layers:
    m0_ttl: 30
    m1_ttl: 86400      # 24 hours
    m2_ttl: 2592000    # 30 days
    m3_ttl: null       # permanent
    m4_ttl: null       # permanent
  consolidation:
    interval: 3600     # 1 hour
    highThreshold: 0.8
    lowThreshold: 0.4

gateway:
  port: 18789
  bind: "loopback"
  auth:
    mode: "token"
    dmPolicy: "pairing"

skills:
  - jebat-memory-skill
  - jebat-consolidation-skill
  - jebat-agent-orchestrator
  - jebat-analyst
  - jebat-researcher

channels:
  webchat:
    enabled: true
```

### 4.2 Database Schema

```sql
-- Memories table
CREATE TABLE memories (
    memory_id UUID PRIMARY KEY,
    content TEXT NOT NULL,
    layer VARCHAR(20) NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    heat_score FLOAT DEFAULT 0.5,
    visit_count INT DEFAULT 0,
    last_visit TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    expires_at TIMESTAMP
);

-- Heat score components
CREATE TABLE memory_heat (
    memory_id UUID REFERENCES memories(memory_id),
    visit_frequency FLOAT DEFAULT 0,
    interaction_depth FLOAT DEFAULT 0,
    recency FLOAT DEFAULT 1,
    cross_reference_count FLOAT DEFAULT 0,
    explicit_rating FLOAT DEFAULT 0.5
);

-- Memory relationships
CREATE TABLE memory_links (
    source_id UUID REFERENCES memories(memory_id),
    target_id UUID REFERENCES memories(memory_id),
    relationship_type VARCHAR(50),
    strength FLOAT DEFAULT 1.0
);
```

---

## Phase 5: Implementation Roadmap

### Week 1-2: Core Skills
- [ ] Create jebat-memory-skill
- [ ] Create jebat-consolidation-skill
- [ ] Test memory storage and retrieval
- [ ] Implement heat scoring

### Week 3-4: Agent System
- [ ] Create jebat-agent-orchestrator
- [ ] Create jebat-analyst
- [ ] Create jebat-researcher
- [ ] Test multi-agent coordination

### Week 5-6: Platform Build
- [ ] Set up Next.js project
- [ ] Build landing page
- [ ] Create documentation site
- [ ] Build dashboard
- [ ] Deploy to staging

### Week 7-8: Integration & Polish
- [ ] Connect all components
- [ ] Performance testing
- [ ] Security audit
- [ ] Production deployment

---

## Questions for humm1ngb1rd

1. **Priority:** Should I start with Phase 1 (skills), Phase 2 (memory integration), or Phase 3 (platform build)?

2. **Platform Framework:** Do you want Next.js for jebat.online, or another stack?

3. **Database:** Use TimescaleDB as in JEBAT core, or PostgreSQL with time-series extensions?

4. **Memory Backend:** File-based (OpenClaw default) or database (JEBAT style)?

5. **Deployment:** Target environment (local dev, staging, production)?

---

**Status:** Ready to begin
**Next Action:** Awaiting humm1ngb1rd's direction on priorities
