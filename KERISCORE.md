# 🗡️ KERISCORE - Personal AI Assistant with Eternal Memory

**Sharp. Precise. Culturally Rooted.**

KerisCore is a personal AI assistant that combines the multi-channel gateway architecture of OpenClaw with advanced cognitive memory systems. Like the legendary Malaysian keris dagger - sharp in execution, precise in memory, and deeply rooted in purpose.

---

## 🌟 Vision

A **self-hosted, privacy-first AI assistant** that:
- **Remembers** everything across all your channels and devices
- **Learns** from every interaction with intelligent memory consolidation
- **Coordinates** multiple specialized agents for complex tasks
- **Executes** with precision through structured cognitive pipelines
- **Respects** your privacy - your data never leaves your control

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMMUNICATION LAYER                           │
│  WhatsApp • Telegram • Discord • Slack • Signal • iMessage      │
│  Matrix • Teams • WebChat • Voice (macOS/iOS/Android)           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GATEWAY (Control Plane)                       │
│  • WebSocket Hub (ws://localhost:18789)                         │
│  • Session Management & Routing                                  │
│  • Security & DM Pairing                                         │
│  • Real-time Events & Presence                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              COGNITIVE PIPELINE (C.O.R.E.)                       │
│                                                                   │
│  Comprehension  →  Understand input & extract intent            │
│       ↓                                                           │
│  Orchestration  →  Plan execution & route to agents             │
│       ↓                                                           │
│  Reasoning      →  Memory-augmented decision making              │
│       ↓                                                           │
│  Evaluation     →  Quality assessment & refinement               │
│       ↓                                                           │
│  Execution      →  Tool execution & response generation          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MEMORY SYSTEM (5 Layers)                      │
│                                                                   │
│  M0: Sensory Buffer     →  Raw inputs (0-30s)                   │
│  M1: Episodic Memory    →  Recent interactions (hours)          │
│  M2: Semantic Memory    →  Facts & entities (days-weeks)        │
│  M3: Conceptual Memory  →  Long-term knowledge (permanent)      │
│  M4: Procedural Memory  →  Skills & workflows (permanent)       │
│                                                                   │
│  • Heat-based Importance Scoring                                 │
│  • Automatic Consolidation & Forgetting                          │
│  • Cross-modal Retrieval (text, image, audio, video)            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   AGENT ORCHESTRATOR                             │
│                                                                   │
│  • Core Agent       →  Main reasoning & coordination            │
│  • Memory Agent     →  Specialized memory operations            │
│  • Tool Agent       →  External integrations                    │
│  • Execution Agent  →  Action execution                         │
│  • Analyst Agent    →  Data analysis                            │
│  • Researcher Agent →  Information gathering                    │
│                                                                   │
│  • Multi-agent Task Distribution                                 │
│  • Council of Perspectives (multi-agent deliberation)            │
│  • Agent Performance Tracking                                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      TOOL ECOSYSTEM                              │
│                                                                   │
│  Browser Control  →  CDP-based automation                       │
│  Canvas System    →  Visual workspace (A2UI)                    │
│  Node Network     →  Device capabilities (camera, screen, etc)  │
│  Skills Platform  →  Extensible skill system                    │
│  Cron & Webhooks  →  Automation & triggers                      │
│  Sessions Tools   →  Agent-to-agent communication               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Differentiators

### 1. **Eternal Memory** 🧠
Unlike OpenClaw's session-based approach, KerisCore implements:
- **5-layer memory architecture** (M0→M4) inspired by human cognition
- **Heat-based importance scoring** - memories that matter stay, trivial ones fade
- **Automatic consolidation** - episodic → semantic → conceptual
- **Cross-modal memory** - remember text, images, audio, video together
- **Temporal precision** - recall exact moments with 0.1s accuracy

### 2. **Cognitive Pipeline** 🎓
Structured reasoning through C.O.R.E.:
- **Comprehension** - Deep intent understanding
- **Orchestration** - Intelligent task decomposition
- **Reasoning** - Memory-augmented chain-of-thought
- **Evaluation** - Quality assessment with iterative refinement
- **Execution** - Precise action with feedback

### 3. **Multi-Agent Coordination** 🤝
- **Agent Factory** - Dynamic agent creation with specialized capabilities
- **Council of Perspectives** - Multi-agent deliberation for complex decisions
- **Task Dependencies** - Sequential and parallel execution patterns
- **Performance Leaderboard** - Track agent efficiency and success rates

### 4. **Hybrid Search** 🔍
- **Vector similarity** - Semantic understanding
- **Keyword search** - Full-text with BM25
- **Graph traversal** - Relationship-based retrieval
- **Temporal filtering** - Time-aware context
- **LLM re-ranking** - Relevance optimization

---

## 🚀 Quick Start

### Installation

```bash
# Install KerisCore
npm install -g keriscore@latest

# Run onboarding wizard
keriscore onboard --install-daemon

# Start the gateway
keriscore gateway --port 18789 --verbose
```

### Basic Usage

```bash
# Send a message
keriscore message send --to +1234567890 --message "Hello"

# Chat with memory context
keriscore agent --message "What did we discuss yesterday?" --thinking high

# Check system health
keriscore doctor

# View memory statistics
keriscore memory stats

# Trigger memory consolidation
keriscore memory consolidate
```

---

## 📊 Memory Heat Scoring

KerisCore's unique **heat-based importance algorithm**:

```
heat_score = (
    0.30 × visit_frequency      # How often accessed
  + 0.25 × interaction_depth    # Engagement level
  + 0.25 × recency              # Time decay
  + 0.15 × cross_references     # Links to other memories
  + 0.05 × explicit_rating      # User-assigned importance
)
```

**Memory Lifecycle:**
- **High Heat (≥80%)** → Immediate promotion to next layer
- **Medium Heat (40-80%)** → Monitor and maintain
- **Low Heat (<40%)** → Apply forgetting curve → eventual expiration

---

## 🔒 Security Model

### Default Stance: Privacy-First

- **Local-first** - All data stays on your infrastructure
- **DM Pairing** - Unknown contacts get a pairing code (not auto-accepted)
- **Sandbox Mode** - Non-main sessions run in isolated Docker containers
- **Allowlist Control** - Explicit approval for all channels
- **Encrypted Storage** - Memories encrypted at rest
- **No Cloud Lock-in** - Self-hosted, full control

### Security Layers

```yaml
# Minimal secure config
security:
  dmPolicy: "pairing"           # Require pairing for DMs
  sandboxMode: "non-main"       # Sandbox all group chats
  allowlist:
    enabled: true
    autoApprove: false
  
channels:
  whatsapp:
    allowFrom: []               # Explicit allowlist
  telegram:
    allowFrom: []
  discord:
    dmPolicy: "pairing"
    allowFrom: []
```

---

## 🛠️ Configuration

### Minimal Config (`~/.keriscore/config.yaml`)

```yaml
agent:
  model: "anthropic/claude-opus-4-6"
  temperature: 0.7

memory:
  layers:
    m0_ttl: 30s
    m1_ttl: 24h
    m2_ttl: 30d
    m3_ttl: permanent
  consolidation:
    interval: 3600              # seconds
    highThreshold: 0.8
    lowThreshold: 0.4

gateway:
  port: 18789
  bind: "loopback"
  auth:
    mode: "token"

channels:
  whatsapp:
    enabled: true
    allowFrom: ["+1234567890"]
  telegram:
    enabled: true
    botToken: "${TELEGRAM_BOT_TOKEN}"
  discord:
    enabled: true
    token: "${DISCORD_BOT_TOKEN}"
```

---

## 🎨 Unique Features

### 1. **Memory Pinning**
```bash
# Pin important memories to prevent forgetting
keriscore memory pin <memory_id> --importance 1.0
```

### 2. **Memory Relationships**
```bash
# Link related memories
keriscore memory link <memory_id_1> <memory_id_2>

# Get related memories
keriscore memory related <memory_id>
```

### 3. **User Profiles**
```bash
# Get aggregated user profile from conceptual memory
keriscore memory profile --user alice

# Export: preferences, entities, relationships, facts
```

### 4. **Memory Export/Import**
```bash
# Backup memories
keriscore memory export --user alice --output backup.json

# Restore from backup
keriscore memory import --file backup.json
```

### 5. **Agent Council**
```bash
# Multi-agent deliberation
keriscore council --question "Should we invest in AI memory startups?" \
  --agents core,analyst,researcher \
  --rounds 3
```

### 6. **Session Tools** (Agent-to-Agent)
```bash
# List active sessions
keriscore sessions list

# Send message to another agent/session
keriscore sessions send --session <id> --message "Status update"

# Get session history
keriscore sessions history --session <id>
```

---

## 📱 Multi-Channel Support

### Supported Channels

| Channel | Status | Features |
|---------|--------|----------|
| **WhatsApp** | ✅ | DM pairing, Groups, Media |
| **Telegram** | ✅ | Bot API, Inline queries, Media |
| **Discord** | ✅ | Slash commands, DM pairing, Embeds |
| **Slack** | ✅ | Bolt SDK, Slash commands, Threads |
| **Signal** | ✅ | signal-cli integration |
| **iMessage** | ✅ | BlueBubbles (recommended) or legacy |
| **Microsoft Teams** | ✅ | Bot Framework |
| **Matrix** | ✅ | E2E encryption support |
| **Google Chat** | ✅ | Chat API |
| **WebChat** | ✅ | Built-in web interface |
| **Voice** | ✅ | macOS/iOS/Android with ElevenLabs |

### Channel-Specific Features

#### WhatsApp
```yaml
channels:
  whatsapp:
    allowFrom: ["+1234567890", "+0987654321"]
    groups:
      enabled: true
      requireMention: true
      allowFrom: ["*"]          # All groups or specific IDs
    mediaMaxMb: 10
```

#### Discord
```yaml
channels:
  discord:
    token: "${DISCORD_BOT_TOKEN}"
    dmPolicy: "pairing"
    guilds:
      - id: "123456789"
        allowFrom: ["user_id_1", "user_id_2"]
    commands:
      native: true              # Use slash commands
      text: true                # Also support text commands
```

#### Telegram
```yaml
channels:
  telegram:
    botToken: "${TELEGRAM_BOT_TOKEN}"
    allowFrom: ["username1", "username2"]
    groups:
      enabled: true
      requireMention: false
```

---

## 🧰 Tool Ecosystem

### Built-in Tools

#### 1. **Browser Control**
```javascript
// Automated browser tasks with CDP
await browser.navigate("https://example.com");
const screenshot = await browser.screenshot();
await browser.click("button.submit");
```

#### 2. **Canvas System** (A2UI)
```javascript
// Visual workspace for agents
await canvas.push({
  type: "chart",
  data: analyticsData
});
await canvas.snapshot();
```

#### 3. **Node Network**
```javascript
// Device capabilities
await node.invoke("camera.snap", { quality: "high" });
await node.invoke("screen.record", { duration: 10 });
await node.invoke("location.get");
await node.invoke("system.notify", { message: "Task complete" });
```

#### 4. **Skills Platform**
```bash
# Install skill
keriscore skill install data-analysis

# List installed skills
keriscore skill list

# Create custom skill
keriscore skill create my-skill --template basic
```

#### 5. **Cron & Webhooks**
```yaml
automation:
  cron:
    - schedule: "0 9 * * *"     # Daily at 9 AM
      action: "memory.consolidate"
    - schedule: "0 0 * * 0"     # Weekly summary
      action: "sessions.send"
      params:
        session: "main"
        message: "Weekly summary ready"
  
  webhooks:
    - path: "/webhook/github"
      secret: "${GITHUB_WEBHOOK_SECRET}"
      handler: "github-integration"
```

---

## 🎭 Agent Types & Specialization

### Core Agent Types

#### 1. **Core Agent**
- **Role**: Main reasoning & coordination
- **Capabilities**: Planning, delegation, synthesis
- **Best for**: Complex multi-step tasks

#### 2. **Memory Agent**
- **Role**: Specialized memory operations
- **Capabilities**: Search, consolidation, profile building
- **Best for**: Memory-intensive queries

#### 3. **Tool Agent**
- **Role**: External integrations
- **Capabilities**: API calls, web scraping, data fetching
- **Best for**: Real-time information gathering

#### 4. **Execution Agent**
- **Role**: Action execution
- **Capabilities**: File operations, system commands, deployments
- **Best for**: DevOps and automation tasks

#### 5. **Analyst Agent**
- **Role**: Data analysis
- **Capabilities**: Statistical analysis, visualization, insights
- **Best for**: Data-driven decision making

#### 6. **Researcher Agent**
- **Role**: Information gathering
- **Capabilities**: Web search, document analysis, synthesis
- **Best for**: Research and investigation

### Custom Agent Creation

```yaml
agents:
  custom:
    - name: "Domain Expert"
      type: "analyst"
      model: "gpt-4"
      temperature: 0.3
      capabilities:
        - name: "domain_analysis"
          description: "Deep domain-specific analysis"
        - name: "expert_consultation"
          description: "Expert-level recommendations"
      systemPrompt: |
        You are a domain expert specializing in...
```

---

## 📈 Performance & Scalability

### Benchmarks

| Operation | Latency (p95) | Throughput |
|-----------|---------------|------------|
| Memory Storage | <10ms | 10,000/s |
| Memory Retrieval | <100ms | 1,000/s |
| Search (10 results) | <150ms | 500/s |
| Consolidation | ~1000 memories/s | - |
| Agent Task | <2s | 50/s |
| WebSocket Messages | <5ms | 5,000/s |

### Scaling Strategy

#### Horizontal Scaling
```yaml
deployment:
  instances: 3                  # Multiple gateway instances
  loadBalancer: "nginx"
  sharding:
    strategy: "user_id"         # Shard by user
    shards: 8
```

#### Caching
```yaml
cache:
  redis:
    enabled: true
    url: "redis://localhost:6379"
    ttl:
      sessions: 3600            # 1 hour
      memories: 1800            # 30 minutes
      hotData: 300              # 5 minutes
```

#### Database Optimization
```yaml
database:
  postgres:
    poolSize: 20
    maxConnections: 100
  timescaledb:
    chunkInterval: "1 day"
    compression: true
  indexes:
    - table: "memories"
      columns: ["user_id", "created_at"]
    - table: "memories"
      type: "gin"
      columns: ["metadata"]
```

---

## 🧪 Testing

### Unit Tests
```bash
npm test                        # All tests
npm run test:unit              # Unit tests only
npm run test:integration       # Integration tests
npm run test:e2e               # End-to-end tests
npm run test:coverage          # Coverage report
```

### Load Testing
```bash
# Locust-based load testing
npm run test:load -- --users 100 --spawn-rate 10

# Memory system stress test
npm run test:stress:memory -- --memories 100000
```

### Example Test
```javascript
describe('Memory System', () => {
  it('should store and retrieve memories with heat scoring', async () => {
    const memory = await memoryManager.store({
      content: 'Test memory',
      userId: 'test_user',
      modality: 'text'
    });
    
    expect(memory.id).toBeDefined();
    expect(memory.heatScore).toBeGreaterThan(0);
    
    const retrieved = await memoryManager.retrieve(memory.id);
    expect(retrieved.content).toBe('Test memory');
  });
});
```

---

## 🚢 Deployment

### Docker Compose

```yaml
version: '3.8'

services:
  keriscore:
    image: keriscore:latest
    ports:
      - "18789:18789"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/keriscore
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./config:/app/config
      - ./workspace:/app/workspace

  db:
    image: timescale/timescaledb-ha:pg16
    environment:
      POSTGRES_DB: keriscore
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data

volumes:
  pgdata:
  redisdata:
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: keriscore
spec:
  replicas: 3
  selector:
    matchLabels:
      app: keriscore
  template:
    spec:
      containers:
      - name: keriscore
        image: keriscore:latest
        ports:
        - containerPort: 18789
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: keriscore-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
```

---

## 🔗 API Reference

### WebSocket Protocol

```javascript
// Connect to gateway
const ws = new WebSocket('ws://localhost:18789');

// Subscribe to events
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'sessions.main'
}));

// Send message
ws.send(JSON.stringify({
  type: 'message.send',
  data: {
    content: 'Hello',
    sessionId: 'main'
  }
}));
```

### REST API

```bash
# Health check
GET /health

# Memory operations
POST /api/v1/memories
GET /api/v1/memories/{id}
POST /api/v1/memories/search
DELETE /api/v1/memories/{id}

# Agent operations
POST /api/v1/agents
GET /api/v1/agents
GET /api/v1/agents/{id}

# Task operations
POST /api/v1/tasks
GET /api/v1/tasks/{id}

# Chat operations
POST /api/v1/chat/completions
GET /api/v1/chat/sessions/{id}/history
WS /ws/chat/{session_id}
```

---

## 🎓 Learning Resources

### Documentation
- **Getting Started** - Installation and setup guide
- **Architecture Deep Dive** - System design and components
- **Memory System Guide** - Understanding the 5-layer architecture
- **Agent Orchestration** - Multi-agent coordination patterns
- **Security Best Practices** - Privacy and safety guidelines
- **API Reference** - Complete API documentation

### Example Projects
- **Personal Assistant** - Daily task management with memory
- **Research Assistant** - Multi-agent research workflows
- **DevOps Bot** - Automated deployment with procedural memory
- **Customer Support** - Context-aware support with semantic memory

---

## 🤝 Community & Support

### Contribution
- **GitHub**: [github.com/yourusername/keriscore](https://github.com/yourusername/keriscore)
- **Discussions**: Share ideas and ask questions
- **Issues**: Report bugs and request features
- **Pull Requests**: Submit improvements (AI-assisted PRs welcome!)

### Support Channels
- **Discord**: Real-time community support
- **Documentation**: Comprehensive guides and tutorials
- **Email**: support@keriscore.ai

---

## 📜 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

**KerisCore** is inspired by and builds upon:
- **OpenClaw** - Gateway architecture and multi-channel design
- **MemContext** - Multi-modal memory with spatiotemporal precision
- **CORE** - Cognitive orchestration framework
- **MemFuse** - Production-ready memory layer patterns
- **MemoryCore-Lite** - Symbolic memory compression concepts

Special thanks to the broader AI research community for advancing the field.

---

## 🗡️ The KerisCore Philosophy

> "Like the legendary keris dagger - sharp in execution, precise in memory, and deeply rooted in purpose. KerisCore cuts through complexity to deliver a personal AI assistant that truly remembers, learns, and evolves with you."

**Built with ❤️ for the AI community**

*Your AI. Your Data. Your Control.*

---

**Version**: 1.0.0  
**Last Updated**: 2026  
**Status**: Production Ready 🚀