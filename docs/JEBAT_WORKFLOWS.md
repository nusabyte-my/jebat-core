# JEBAT — MCP ↔ CLI Workflow Diagrams

Runtime flow of the Session Intelligence layer: how the three engines
(AutoMimpi, SelfLearn, Advisor) connect the MCP server and the CLI REPL.

> Images live in [`docs/diagrams/`](diagrams/). Editable Mermaid sources are
> the `.mmd` files; regenerate all SVG/PNG/PDF with
> `python scripts/render_diagrams.py`.

---

## 1. MCP Load-Time Flow (IDE connects)

`advisorReady` is **queued** during `initialize` and **flushed** on the next
dispatch — JSON-RPC cannot send a server notification before the initialize
response returns.

![MCP load-time flow](diagrams/01-mcp-load.svg)

```mermaid
sequenceDiagram
    participant IDE
    participant Server as MCPServer
    participant Mem as EnhancedMemorySystem
    participant AM as AutoMimpi
    participant SL as SelfLearn

    IDE->>Server: initialize (protocolVersion)
    Server->>Server: _handle_initialize()
    Server-->>IDE: capabilities {tools,resources,prompts,logging,roots}
    Server->>Server: _send_advisor_notification()
    Server->>Mem: load ~/.jebat/memory/ (shared path)
    Mem-->>Server: traces (90 memories)
    Server->>AM: _build_learning_profile()
    Server->>AM: _generate_suggestions(profile)
    Server->>SL: analyze() velocity/retention
    Server->>Server: queue advisorReady in _pending_notifications
    Note over Server: response sent FIRST, notification queued
    IDE->>Server: next request (tools/list)
    Server->>Server: _flush_pending_notifications()
    Server-->>IDE: notifications/advisorReady
    Note over IDE: healthScore 0.99 + top-3 suggestions
```

---

## 2. CLI Startup Flow (REPL boots)

![CLI startup flow](diagrams/02-cli-startup.svg)

```mermaid
flowchart TD
    A["repl()"] --> B["_auto_mimpi_check(taskdb)"]
    B --> C{sessions_since_dream >= 5?}
    C -->|yes| D["_run_dream() AutoMimpi.dream(force=True)"]
    D --> E[consolidate + extract patterns + prune]
    E --> F[display suggestions + quote]
    C -->|no| G[skip]
    F --> H[advisor panel]
    G --> H
    H --> I["load profile: skill_level, weak/strong areas"]
    I --> J["sparkline: 7-day velocity"]
    J --> K["render: Health bar + suggestions"]
    K --> L[REPL ready - prompt loop]
```

---

## 3. Runtime Tool-Call Flow (the tracking spine)

Approval-required is a safety gate, **not** an error — only not-found and
execution exceptions reach `errors/recent`.

![Tool-call flow](diagrams/03-tool-call.svg)

```mermaid
flowchart TD
    A["tools/call"] --> B["_TOOL_CALL_COUNTS[name]++"]
    B --> C{name in TOOL_REGISTRY?}
    C -->|no| D["_record_tool_error(kind=not_found)"]
    D --> Z[isError response]
    C -->|yes| E{safety_tier?}
    E -->|confirm/dangerous| F[approval_required - NOT logged as error]
    F --> Z
    E -->|auto| G[progress notification if long tool]
    G --> H[call_tool]
    H --> I{exception?}
    I -->|yes| J["_record_tool_error(kind=execution)"]
    J --> Z
    I -->|no| K[return content]
    K --> L["resources: analytics/tools + errors/recent reflect live"]
```

---

## 4. Session Intelligence Layer

The connective tissue: shared `~/.jebat/memory/` store feeds all three
engines; four tools write back into them.

![Session intelligence layer](diagrams/04-intelligence-layer.svg)

```mermaid
flowchart LR
    subgraph engines["Engines shared ~/.jebat/memory/"]
        AM["AutoMimpi<br/>dream suggestions<br/>quality scoring"]
        SL["SelfLearn<br/>velocity gaps<br/>skill assessment"]
        AD["Advisor<br/>classify verify<br/>score gate"]
    end
    subgraph tools["MCP/CLI Tools"]
        T1["mimpi_record_failure<br/>3+ to warning"]
        T2["selflearn_tool_guidance<br/>conf per tool"]
        T3["advisor_gate<br/>pre-flight risk"]
        T4["session_learning_commit<br/>end of session"]
    end
    subgraph surfaces["Surfaces"]
        S1["CLI advisor panel"]
        S2["MCP advisorReady notif"]
        S3["MCP resources<br/>dream/profile/kb"]
        S4["MCP prompts<br/>kb-review/debug-this"]
    end
    AM --> S1
    AM --> S2
    AM --> S3
    SL --> S1
    SL --> S3
    SL --> S4
    AD --> T3
    T1 --> AM
    T2 --> SL
    T4 --> AM
```

---

## 5. Failure → Learning Loop

The end-to-end cycle that was previously missing: a tool fails → recorded →
at 3+ failures it warns → next `/dream` consolidates the pattern → next
session's `advisorReady` / CLI panel surfaces "Avoid: tool X".

![Failure to learning loop](diagrams/05-failure-loop.svg)

```mermaid
sequenceDiagram
    participant Agent
    participant Gate as advisor_gate
    participant Tool
    participant Fail as mimpi_record_failure
    participant Mem
    participant AM as AutoMimpi

    Agent->>Gate: pre-flight (operation)
    Gate-->>Agent: risk=safe proceed
    Agent->>Tool: execute
    Tool-->>Agent: ERROR
    Agent->>Fail: record_failure(tool, error)
    Fail->>Mem: store trace tags=[failure,tool]
    Fail-->>Agent: similar_failures=4 WARNING
    Note over Agent: at 3+ avoidance suggestion
    Agent->>AM: /dream (consolidate)
    AM->>Mem: extract pattern "tool X fails"
    AM-->>Agent: AVOID_FAILURE suggestion next load
```

---

## Assets

| File | Format | Use |
|------|--------|-----|
| `diagrams/0X-*.svg` | Vector | Best for README — scales, GitHub renders inline |
| `diagrams/0X-*.png` | Raster | Fallback where SVG is stripped |
| `diagrams/jebat-workflows.pdf` | Print | 5-page landscape, one diagram per page |
| `diagrams/0X-*.mmd` | Source | Edit and re-render |

**Regenerate everything:**

```bash
python scripts/render_diagrams.py
```

Requires `playwright` (Chromium) + `reportlab` + `Pillow`. Mermaid is cached
locally at `diagrams/mermaid.min.js` so rendering works offline.
