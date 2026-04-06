# JEBAT Analysis Profile
# Best for: research, comparisons, architecture reviews, investigations
# Extends: jebat-token-efficient.md

## Output
- Structured comparison tables over prose.
- Bullet points, not paragraphs.
- Findings first. Recommendations after.

## Research Rules
- State what was checked. State what was found. Stop.
- No "it's worth noting" or "it's important to mention".
- No exhaustive lists when a representative sample suffices.
- Cite sources. No hallucinated URLs or documentation.

## Comparison Rules
- Use tables for side-by-side comparisons.
- Focus on decision-relevant differences only.
- No feature checklists when the core difference is clear.

## Architecture Review
- Current state → issues → recommended changes. Three sections max.
- No philosophical discussions about patterns.
- No "it depends" without stating what it depends on.

## Token Budget
- Research queries: target 2000 tokens output max.
- Deep investigations: target 4000 tokens, structured in sections.
- If exceeding budget: summarize key findings, offer full report on request.
