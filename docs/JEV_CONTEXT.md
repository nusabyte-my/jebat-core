# Jev — System One Model Context for JEBAT

> Curated reference for integrating TypeSafe AI's Jev into JEBAT's decision pipeline.
> Source: [awesome-jev](https://github.com/yibie/awesome-jev) + [TypeSafe blog](https://typesafe.ai/blog/introducing-system-one-models-and-jev)

## What Jev Is

Jev is **not an LLM**. It is a System One Model — a probabilistic decision function that takes unstructured state + typed questions and returns typed answers with calibrated probabilities. No string generation, no hallucination, no sequential token decoding.

Inspired by Kahneman's System 1 (fast, intuitive) vs System 2 (slow, deliberate).

## API Shape

```
POST /v1/systemone
{
  "state": "<unstructured text/context>",
  "questions": {
    "question_key": {
      "type": "Choice" | "Score" | "Noul",
      ...type-specific fields
    }
  }
}
```

### Output Types

| Type | Description | Output |
|------|-------------|--------|
| **Noul** (Boolean) | Yes/No verification | `{answer: true/false, probability: 0.0-1.0}` |
| **Choice** | Pick one from a custom list | `{answer: "label", probabilities: {label: p, ...}, confidence: 0.0-1.0}` |
| **Score** | Rate on a scale | `{answer: N, probabilities: {"0": p, ...}, confidence: 0.0-1.0}` |

### Key Characteristics

- **Speed**: 70–500ms end-to-end (40x–200x faster than LLMs)
- **Cost**: $0.042/M input tokens, output tokens FREE
- **Parallel**: All questions answered in a single pass
- **No type errors**: Schema matching is guaranteed
- **Calibrated**: Higher confidence = higher accuracy (RLCD-trained)
- **Max cardinality**: 255 choices per question

## JEBAT Integration Points

### 1. Chat/Message Routing (Hot Path)

Replace LLM-based intent classification with a Jev Choice:

```python
# Before: LLM call to classify intent (~3-30s, expensive)
# After: Jev Choice (~100ms, near-free)
questions = {
    "intent": {
        "type": "Choice",
        "candidates": ["chat", "code", "pentest", "memory", "agent_task", "analytics"]
    },
    "is_urgent": {
        "type": "Noul"  # Boolean
    },
    "complexity": {
        "type": "Score",
        "criteria": ["trivial", "simple", "moderate", "complex", "expert"]
    }
}
```

### 2. Agent Orchestrator Pre-Routing

Before spinning up a full agent, use Jev to decide:
- Which agent type fits (Choice)
- Whether the task needs an agent at all (Noul)
- Task priority scoring (Score)

### 3. Content Moderation / Guardrails

Gate user inputs and agent outputs:
- Prompt injection detection (Noul)
- Sensitive content flags (Noul per category)
- Response quality scoring (Score)

### 4. Memory Relevance Filtering

Score memory chunks before injection into context:
- Relevance to current query (Noul + Score)
- Staleness detection (Noul)

### 5. WhatsApp Message Triage

Classify incoming WA messages before routing:
- Intent classification (Choice)
- Language detection (Choice)
- Priority/urgency (Score)

## Proven Patterns from awesome-jev (256 entries)

### Classification & Routing (24 entries)
- **jev-router**: Routes requests to cheapest capable model via Jev Choice
- **DocJev**: Document classification at 182ms p50
- **jev-cookbook**: 15 runnable recipes for support tickets, bank transactions, Gmail labels

### Verification & Guardrails (22 entries)
- **jev-guard**: Prompt injection + dangerous action guard for coding agents
- **pi-jev**: Tool-call gate checking risky calls before execution
- **jev-git**: Pre-commit gate screening for secrets/destructive commands

### Agent Decisions (31 entries)
- **Jev Ultrafast (browser-use)**: Jev decides each browser action, LLM only for text input
- **limpet**: Stop hook preventing agents finishing too early
- **fast-jev-compaction**: Context pruning via Jev scores vs LLM summarization

### Scoring & Ranking (20 entries)
- **jev-reranker**: Noul judgments for RAG document re-ranking
- **pagegrade**: Per-section clarity/SEO scoring
- **Clean Code Judge**: 31 boolean code smell checks per file

### Evaluation & Benchmarking (16 entries)
- **jevcal**: Per-question confidence threshold fitting for accuracy targets
- **LangChain**: "Jev is the cheaper and more consistent judge for online evals"

## Alignment with JEBAT's `judge()` Primitive

JEBAT's harness already has `judge()` and `judge_batch()` — these map **directly** to Jev's API:

| JEBAT `judge` | Jev Equivalent |
|----------------|----------------|
| `{type: "bool"}` | `Noul` |
| `{type: "choice", criteria: {label: rubric}}` | `Choice` with candidates |
| `{type: "score", criteria: [low..high]}` | `Score` with criteria levels |

This means JEBAT's existing `judge()` calls could be backed by Jev with zero interface change — only the backend transport switches from the default model to the TypeSafe `/v1/systemone` endpoint.

## Cost Comparison

| Operation | LLM (GPT-4o) | Jev |
|-----------|---------------|-----|
| 1M input tokens | $2.50 | $0.042 |
| 1M output tokens | $10.00 | $0.00 |
| Classify 10K messages | ~$25 + 30min | ~$0.42 + 17s |
| Score 100K memory chunks | ~$250 + 5hr | ~$4.20 + 2.8min |

## Risk Notes

- Jev is **early access** — API may change
- Max 255 choices per question
- No image/multimodal input (text state only)
- Not suitable for: prose generation, summarization, code writing, reasoning chains
- Curation ≠ endorsement — verify entries before adopting (see awesome-jev warnings)
