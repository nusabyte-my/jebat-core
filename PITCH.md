# JEBAT — Sovereign Agent Operating System

## Executive Summary

**JEBAT** is an open-source, self-hosted **Agent Operating System** that gives enterprises full control over their AI infrastructure. Five specialized AI products share a single persistent memory layer and MCP protocol bus — running entirely air-gapped with zero telemetry.

**One platform. Five products. Your data never leaves your network.**

---

## The Problem

Enterprise AI adoption is stalled by three critical risks:

1. **Data Sovereignty** — Sensitive code, documents, and conversations flow through third-party APIs (OpenAI, Anthropic, Google). Regulated industries (finance, healthcare, defense, government) cannot comply with data residency requirements.

2. **Vendor Lock-in** — Switching between LLM providers requires rewriting application logic. Price increases, API changes, and deprecations leave enterprises dependent on a single vendor's roadmap.

3. **Fragmented Tooling** — Enterprises cobble together 5-10 disconnected tools: one for code generation, another for security scanning, a third for chat, a fourth for observability. No shared memory. No unified context. Agents restart from zero every session.

**The market has AI products. It lacks an AI operating system.**

---

## The Solution

JEBAT is the **operating system layer** for enterprise AI. It provides:

### Five Integrated Products

| Product | Codename | Function |
|---------|----------|----------|
| **JEBAT Core** | Hang Jebat | Sovereign inference router with 7 reasoning modes, 5-layer memory, multi-agent swarm |
| **Sentinel** | Keris | Autonomous security orchestrator — network scanning, CVE correlation, CVSS scoring |
| **Developer Suite** | Pandai | MCP-native code generation, review, sandboxed execution — integrated with 6 IDEs |
| **Companion** | Sahabat | Conversational AI with persistent memory, meeting intelligence, task tracking |
| **Nexus** | Perisai | Multi-channel bot orchestrator across Telegram, Discord, Slack, WhatsApp, Signal, Matrix |

### Shared Intelligence Layer

Every product connects to the same:

- **Memory Engine** — 6 memory types (working, episodic, semantic, procedural, emotional, prospective) with Ebbinghaus forgetting curves, pattern extraction, and self-learning
- **MCP Protocol Bus** — 47 tools exposed over stdio, HTTP, and Streamable HTTP transport
- **Provider Router** — 17 LLM backends with automatic failover (OpenAI, Anthropic, Gemini, Ollama, llama.cpp, OpenRouter, Groq, and 10 more)

### Embedded Subsystems

- **Ghost DB** — Embedded vector database (SQLite + sqlite-vec) with HNSW indexing for offline RAG
- **Catalyst O11y** — Full observability stack: OTel tracing, Prometheus metrics, Loki logging, HALO analysis engine
- **Enterprise RBAC** — 3-tier hierarchical access control (org → team → project) with 10 resource types
- **SDK** — Python (sync/async, Pydantic) and TypeScript (Zod validation, React hooks) clients
- **Mimpi** — Dream engine that generates insights from concept graphs during idle cycles
- **Working Memory** — Live context buffer tracking goals, facts, and constraints across agent iterations

---

## Technical Moats

### 1. Zero-Dependency Architecture
Runs on SQLite + sqlite-vec. No PostgreSQL, no Redis, no external vector DB required. Single binary deployment via `npx @nusabyte/jebat`.

### 2. Air-Gapped by Design
No telemetry. No phone-home. No external API calls required. Every component runs inside the customer's network. Ollama auto-starts local models.

### 3. Provider-Agnostic Router
17 LLM providers with automatic failover. Switch from OpenAI to local Ollama by changing one config line. No code changes required.

### 4. Memory Persistence Across Products
Unlike chatbots that forget everything between sessions, JEBAT maintains a 6-type memory system with forgetting curves. Memories consolidate automatically. The agent remembers what worked.

### 5. MCP Protocol Native
Built on the Model Context Protocol standard. Works with Cursor, VS Code, Zed, Windsurf, JetBrains. Not another proprietary API — an open standard.

### 6. Self-Learning Agent Loop
MetaLearner with UCB1 strategy selection auto-discovers optimal approaches. Branch agents isolate parallel work. Spec-driven development with cost tracking per agent.

---

## Market Opportunity

### TAM: $85B by 2028
Enterprise AI platform market (Gartner, 2025)

### SAM: $12B
Self-hosted / on-premises AI infrastructure for regulated industries

### SOM: $500M
Enterprises requiring air-gapped AI with memory persistence and multi-product integration

### Target Customers

| Segment | Pain Point | JEBAT Solution |
|---------|-----------|----------------|
| **Financial Services** | Regulatory data residency (MAS, SEC, GDPR) | Air-gapped deployment, zero telemetry |
| **Healthcare** | HIPAA compliance, patient data isolation | Self-hosted inference, no external API calls |
| **Defense / Government** | Classified networks, air-gapped facilities | Full offline operation, no internet required |
| **Software Enterprises** | Multi-tool fragmentation, lost context | Unified memory across all AI tools |
| **Managed Service Providers** | Multi-tenant AI platforms | RBAC, cost tracking, enterprise access control |

---

## Business Model

### Open Source Core (MIT License)
- Full platform: all 5 products, memory engine, MCP bus, observability
- Community-driven development, transparent roadmap
- Self-hosted deployment — no SaaS dependency

### Enterprise Support (Revenue Stream)
- **JEBAT Enterprise** — Priority support, SLA, custom integrations
- **JEBAT Cloud** — Managed deployment for teams that want cloud without vendor lock-in
- **Professional Services** — Architecture review, custom agent development, training

### Competitive Positioning

| Feature | JEBAT | LangChain | AutoGPT | OpenAI Platform |
|---------|-------|-----------|---------|-----------------|
| Self-hosted | ✓ | ✓ | ✓ | ✗ |
| Air-gapped | ✓ | ✗ | ✗ | ✗ |
| Multi-product | 5 integrated | Library only | Single agent | Single product |
| Memory persistence | 6-type + forgetting curves | Basic | None | Session only |
| MCP native | ✓ (47 tools) | ✗ | ✗ | ✗ |
| Provider routing | 17 providers | Multiple | Limited | OpenAI only |
| Observability built-in | ✓ (Catalyst) | ✗ | ✗ | Basic |
| Enterprise RBAC | ✓ (3-tier) | ✗ | ✗ | ✓ |
| IDE integration | 6 IDEs | ✗ | ✗ | ✓ |
| License | MIT | MIT | MIT | Proprietary |

---

## Traction

### Current State (v7.5)

- **145 tests passing** across 10 test suites
- **47 MCP tools** registered and functional
- **17 LLM providers** integrated with auto-failover
- **5 products** shipped and operational
- **6 IDE integrations** (Cursor, VS Code, Zed, Windsurf, JetBrains, Continue)
- **Python + TypeScript SDKs** with full API coverage
- **Full observability stack** (tracing, metrics, logging, alerting)

### What Ships Next

| Timeline | Milestone |
|----------|-----------|
| Q3 2026 | v7.5 — Unified CLI, Streamable HTTP MCP, Ghost DB, Catalyst, SDK, RBAC |
| Q4 2026 | Production hardening — multi-node deployment, SSO, audit logging |
| Q1 2027 | Enterprise features — multi-tenant isolation, cost analytics dashboard |
| Q2 2027 | JEBAT Cloud (managed offering) |

---

## Team

**NusaByte** — Built by Shaidan Shaari (humm1ngb1rd)

- Full-stack systems engineer with deep expertise in LLM orchestration, distributed systems, and security
- Previous work: enterprise AI platforms, security tooling, developer infrastructure
- Building JEBAT as the sovereign alternative to cloud-dependent AI platforms

---

## The Ask

**Pre-Seed: $1.5M**

| Use of Funds | Allocation |
|-------------|------------|
| Engineering (3 hires) | 50% |
| Enterprise sales & partnerships | 25% |
| Infrastructure & operations | 15% |
| Legal & compliance | 10% |

### Milestones with Funding

- **6 months**: 5 enterprise design partners, first paying customer
- **12 months**: 50 enterprise deployments, $500K ARR
- **18 months**: JEBAT Cloud launch, $2M ARR

---

## Why Now

1. **Regulation is tightening** — EU AI Act, MAS TRM, HIPAA updates all require data residency and auditability that cloud AI cannot provide
2. **LLM costs are dropping** — Local inference (Ollama, llama.cpp) makes self-hosted AI economically viable for the first time
3. **MCP is becoming standard** — The Model Context Protocol is gaining adoption across IDEs and tools; JEBAT is built on it natively
4. **Enterprises are frustrated** — They want AI capabilities without sending their code and data to third-party APIs

---

## Contact

**NusaByte**
https://github.com/nusabyte-my/jebat-core
https://jebat.online

---

*JEBAT — Your AI. Your Infrastructure. Your Rules.*
