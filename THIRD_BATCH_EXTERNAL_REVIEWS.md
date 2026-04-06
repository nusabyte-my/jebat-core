# Third Batch External Reviews

## 1. academic-research

### Summary
Academic search and literature-review skill built around OpenAlex, with topic/author/DOI lookups, citation traversal, and structured review generation.

### Strong patterns
- practical academic retrieval workflow
- no API key requirement is attractive
- literature review pipeline is clear and useful
- structured output expectations are strong

### Concerns
- frontmatter uses `version`, beyond minimal-spec guidance
- script-driven review generation needs deeper inspection before stronger trust
- caches and external fetching behavior need review if imported directly

### Jebat decision
- **APPROVE WITH CAUTION** as a pattern source
- strong fit for `jebat-researcher`

### Planned Jebat use
- improve literature review workflows
- improve citation-chain and paper triage guidance
- strengthen evidence-based research mode

---

## 2. arxiv-search-collector

### Summary
Model-led arXiv collection workflow where the model designs queries, filters results, and merges a curated paper set.

### Strong patterns
- model-led query planning is a good fit for Hermes/Jebat
- explicit staged workflow is strong
- query-writing guidance is unusually concrete
- useful for curated paper collection, not just ad-hoc lookup

### Concerns
- longer, more procedural, more room for workflow drift
- script layer not yet inspected
- manual query-selection workflow may be powerful but more complex than needed for routine use

### Jebat decision
- **APPROVE WITH CAUTION** as a pattern source
- more specialized than `academic-research`

### Planned Jebat use
- improve advanced research collection mode
- model-led query expansion patterns
- dedupe/selection workflow ideas for serious literature gathering

---

## Net takeaway

Both are good additions to Jebat’s researcher stack.

Recommended hierarchy:
1. `academic-research` for general scholarly research
2. `arxiv-search-collector` for focused advanced paper-set building
