# Penganalisis — Product Management Specialist Agents

**Role:** JEBAT's expanded product management capabilities
**Adapted from:** [slgoodrich/agents](https://github.com/slgoodrich/agents) — AI PM Copilot
**Type:** Multi-agent skill

## What We Adopt

### 7 Specialist PM Agents

| Agent | Purpose | Framework |
|-------|---------|-----------|
| **market-analyst** | Competitive landscape, market sizing (TAM/SAM/SOM), positioning | SWOT, Porter's Five Forces |
| **research-ops** | User interview design, usability testing, insight synthesis | Continuous Discovery Habits |
| **product-strategist** | Product vision, North Star metrics, quarterly/annual goals | OKRs, RICE |
| **roadmap-builder** | Now-Next-Later roadmaps, theme-based planning, milestone sequencing | Story Mapping |
| **feature-prioritizer** | RICE, ICE, Kano model, Value vs. Effort scoring | Prioritization frameworks |
| **requirements-engineer** | PRDs, technical specs, user stories, acceptance criteria | PR/FAQ, Lean PRD |
| **launch-planner** | GTM strategy, distribution channels, launch execution | Launch framework |

### Multi-Agent Team Presets

**Validation Sprint** — Parallel investigation
- Researcher vs. Skeptic
- BUILD / DON'T BUILD verdicts
- Use before committing to feature development

**PRD Stress Test** — Three independent reviewers
- Score PRD on market-fit, feasibility, scope
- Catches weak requirements before development

**Competitive War Room** — Parallel competitor deep-dives
- Battle cards and positioning maps
- Strategic response recommendations

### Context-Aware Memory

Setup generates 8 markdown files in `.jebat/product-context/`:
- `tech-stack.md` — Discovered from codebase
- `strategic-goals.md` — Quarterly objectives
- `user-personas.md` — Target user profiles
- `competitive-landscape.md` — Known competitors
- `business-model.md` — Revenue strategy
- `constraints.md` — Technical and business limits
- `metrics.md` — KPIs and North Star
- `glossary.md` — Domain terminology

## Integration with JEBAT

Maps to Penganalisis + Strategi Produk + Strategi Jenama:

```
JEBAT Product Request → Route to specialist
  ├─ "analyze market" → market-analyst
  ├─ "prioritize features" → feature-prioritizer
  ├─ "write PRD" → requirements-engineer
  ├─ "build roadmap" → roadmap-builder
  ├─ "plan launch" → launch-planner
  ├─ "user research" → research-ops
  └─ "product vision" → product-strategist
```

## Context Scanner

Automatically scans codebase to discover:
- Features from routes and components
- Tech stack from package.json, requirements.txt, go.mod
- 3rd-party integrations from imports
- Project scale and maturity

Uses lightweight model for efficient scanning (doesn't burn premium tokens).

## PRD Template Selection

Dynamically selects PRD template based on complexity:

| Complexity | Score | Template |
|------------|-------|----------|
| Simple | 0-3 | Lean PRD (1-pager) |
| Medium | 4-6 | Comprehensive PRD |
| Complex | 7-8 | Google PRD format |
| Strategic | 9-10 | Amazon PR/FAQ |

## Output Artifacts

All agents produce structured markdown saved to `.jebat/product-context/`:
- PRDs → `prds/[feature-name].md`
- Roadmaps → `roadmaps/[quarter].md`
- Market Analysis → `analysis/[topic].md`
- Launch Plans → `launches/[feature].md`

## Triggers

Use when the task involves:
- Product strategy or vision
- Feature prioritization
- Market analysis
- PRD writing
- Roadmap planning
- Launch planning
- User research design
- Competitive analysis
- Go-to-market strategy
