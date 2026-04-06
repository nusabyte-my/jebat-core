# Token Optimization Guide

Maximize token efficiency across **both input and output** for all LLM operations in JEBATCore.

## Overview

JEBATCore implements a **dual-strategy** token optimization system inspired by [claude-token-efficient](https://github.com/drona23/claude-token-efficient):

| Strategy | What it does | Savings |
|----------|-------------|---------|
| **Input-side** (our system) | Compress context, prompts, and MCP responses | 25-50% |
| **Output-side** (behavioral rules) | Strip LLM fluff: greetings, sign-offs, restatements | 30-60% |

Combined: **~63% total token reduction** on output-heavy workflows.

### How It Works
- The system prompt adds ~50 input tokens per message
- Output savings compound across repeated calls
- At scale: 1,000 prompts/day → ~96,000 tokens saved → ~$8.64/mo (Sonnet pricing)

## Quick Start

### Analyze Token Usage

```bash
# Analyze text directly
npx jebatcore token-analyze --text "Your text here"

# Analyze a file
npx jebatcore token-analyze --file AGENTS.md --model claude

# Analyze with different models
npx jebatcore token-analyze --file system-prompt.txt --model gemini
```

### Compress Text for Token Efficiency

```bash
# Compress a file with moderate compression
npx jebatcore token-compress --file AGENTS.md

# Aggressive compression with target token count
npx jebatcore token-compress --file large-context.txt --level aggressive --target-tokens 3000

# Save compressed output to file
npx jebatcore token-compress --file prompt.txt --output compressed-prompt.txt

# Minimal compression (preserve almost everything)
npx jebatcore token-compress --file docs.md --level minimal
```

### Compress System Prompts

```bash
# Optimize system prompt for token budget
npx jebatcore token-compress-prompt --file universal-prompt.md --target-tokens 4000

# Save optimized prompt
npx jebatcore token-compress-prompt --file jebat-universal-prompt.md --output optimized-prompt.md
```

### View Token Budgets

```bash
# Show all default budgets
npx jebatcore token-budget

# Show specific budget with character equivalents
npx jebatcore token-budget --budget implementation
npx jebatcore token-budget --budget codeReview
```

### Analyze Output Fluff

```bash
# Analyze LLM output for fluff
npx jebatcore output-fluff --file llm-response.txt

# Analyze inline text
npx jebatcore output-fluff --text "Sure! I'd be happy to help..."

# Save cleaned output
npx jebatcore output-fluff --file response.txt --output clean.txt
```

## Output Token Efficiency

JEBATCore enforces output-side token reduction through behavioral directives embedded in the system prompt and MCP server fluff-stripping.

### What Gets Stripped

| Category | Examples | Tokens Saved |
|----------|---------|-------------|
| Greetings | "Sure!", "Certainly!", "I'd be happy to help" | 5-15 |
| Status narration | "Now I'll read the file...", "Let me check..." | 10-30 |
| Sycophantic content | "Great question!", "As an AI assistant..." | 10-25 |
| Unnecessary closings | "Let me know if...", "Happy coding!" | 10-20 |
| Restatements | "Based on the code you've shared..." | 15-40 |

### Output Rules (Embedded in System Prompt)

The universal prompt enforces:
- No greetings, sign-offs, or conversational filler
- Code first. Explanation after, only if non-obvious
- Use JSON, bullets, or tables — not prose
- Simple task → one-line fix, no explanation
- Execute the task. Do not narrate what you are doing
- No "Now I will..." or "I have completed..." status updates

### MCP Server Fluff Stripping

The MCP server automatically strips common fluff patterns from all tool responses before returning them to the LLM, reducing output token consumption on every call.

### Specialized Profiles

| Profile | Best For | File |
|---------|----------|------|
| Coding | Dev projects, code review, debugging | `adapters/profiles/jebat-coding.md` |
| Agents | Automation pipelines, multi-agent systems | `adapters/profiles/jebat-agents.md` |
| Analysis | Research, comparisons, architecture reviews | `adapters/profiles/jebat-analysis.md` |
| Universal | All-purpose JEBAT operation | `adapters/jebat-universal-prompt.md` |
| Token-efficient | Drop-in output optimization | `adapters/jebat-token-efficient.md` |

### Using Profiles

Drop the appropriate profile file into your project root as `CLAUDE.md` (or append to existing system prompts):

```bash
# For coding projects
cp adapters/profiles/jebat-coding.md your-project/CLAUDE.md

# For automation pipelines
cp adapters/profiles/jebat-agents.md your-project/CLAUDE.md

# For pure output efficiency (minimal rules)
cp adapters/jebat-token-efficient.md your-project/CLAUDE.md
```

## Input Token Efficiency

Default budgets for different operation types:

| Operation | Input Tokens | Output Tokens | Total |
|-----------|-------------|---------------|-------|
| casualChat | 2,000 | 500 | 2,500 |
| quickFact | 1,500 | 300 | 1,800 |
| memorySearch | 4,000 | 800 | 4,800 |
| verification | 5,000 | 1,000 | 6,000 |
| planning | 6,000 | 1,500 | 7,500 |
| codeReview | 8,000 | 1,000 | 9,000 |
| research | 10,000 | 1,500 | 11,500 |
| implementation | 12,000 | 2,000 | 14,000 |

## Compression Levels

### Minimal (95% retention)
- Preserves almost all content
- Minor whitespace optimization
- No content removal
- Best for: Critical documentation, code

### Moderate (75% retention) ⭐ Recommended
- Balance of completeness and efficiency
- Abbreviates common terms
- Shortens file paths
- Best for: System prompts, general context

### Aggressive (50% retention)
- Maximum token savings
- Removes examples and verbose explanations
- Strips blockquotes and notes
- Best for: Large contexts, memory search

## MCP Server Token-Efficient Tools

The MCP server now includes optimized versions of all tools:

### operating_system_efficient
Returns compressed operating system index with token statistics.

```json
{
  "name": "operating_system_efficient",
  "arguments": {
    "maxTokens": 6000
  }
}
```

### find_assets_efficient
Returns concise asset list with token count and truncation detection.

```json
{
  "name": "find_assets_efficient",
  "arguments": {
    "category": "playbook",
    "pattern": "dispatch",
    "maxTokens": 2000
  }
}
```

### read_asset_efficient
Reads asset with compression to fit token budget.

```json
{
  "name": "read_asset_efficient",
  "arguments": {
    "path": "vault/OPERATING-SYSTEM.md",
    "maxTokens": 4000,
    "compression": "moderate"
  }
}
```

### token_stats
Get token count for any text string.

```json
{
  "name": "token_stats",
  "arguments": {
    "text": "Your text here",
    "model": "claude"
  }
}
```

### cache_stats / cache_clear
Manage MCP response cache.

```json
{
  "name": "cache_stats"
}
```

```json
{
  "name": "cache_clear"
}
```

## Model Token Ratios

Different models have different token densities:

| Model | Chars/Token | Best For |
|-------|-------------|----------|
| GPT-3.5 | 3.5 | Fast responses, simple tasks |
| Claude | 3.7 | Reasoning, code, complex tasks |
| Llama | 3.8 | Local deployment |
| Mistral | 3.9 | Balanced performance |
| GPT-4 | 4.0 | Deep reasoning |
| Gemini | 4.2 | Long context windows |
| Default | 4.0 | General estimation |

## Best Practices

### 1. Analyze Before Sending
```bash
# Check token count before LLM call
npx jebatcore token-analyze --file prompt.txt --model claude
```

### 2. Compress Large Contexts
```bash
# Compress files over 8000 tokens
npx jebatcore token-compress --file large-file.md --target-tokens 6000 --output compressed.md
```

### 3. Use MCP Efficient Tools
- Prefer `*_efficient` tools when available
- Set appropriate `maxTokens` for your needs
- Monitor cache stats to verify reuse

### 4. Match Budget to Operation
- Casual questions → `quickFact` (1,800 tokens)
- Code implementation → `implementation` (14,000 tokens)
- Research tasks → `research` (11,500 tokens)

### 5. Leverage Caching
- MCP server caches responses automatically
- Identical requests return cached results
- Clear cache when context changes: `cache_clear`

## Integration Examples

### Using in Scripts

```bash
#!/bin/bash
# Analyze all markdown files and report token usage

for file in *.md; do
  echo "=== $file ==="
  npx jebatcore token-analyze --file "$file" --model claude
  echo ""
done
```

### Compressing Prompts for Deployment

```bash
# Optimize universal prompt for token efficiency
npx jebatcore token-compress-prompt \
  --file adapters/jebat-universal-prompt.md \
  --target-tokens 3500 \
  --output adapters/optimized-prompt.md

# Verify token count
npx jebatcore token-analyze --file adapters/optimized-prompt.md --model claude
```

## Programmatic Usage

```javascript
import { countTokens, compressContext, checkBudget } from './lib/token-utils.js';

// Count tokens
const tokens = countTokens("Your text here", "claude");

// Compress context
const result = compressContext(largeText, {
  level: "moderate",
  targetTokens: 4000,
  model: "claude"
});

console.log(`Saved ${result.savings} tokens (${result.compressionRatio})`);

// Check budget
const budget = checkBudget(text, 8000, "claude");
if (!budget.within) {
  console.log(`Over budget by ${budget.used - budget.limit} tokens`);
}
```

## Troubleshooting

### Text is too long after compression
- Use `--target-tokens` to enforce hard limits
- Try `aggressive` compression level
- Split content into multiple smaller files

### Token count seems inaccurate
- Token counting uses character-based estimation
- Actual counts vary by model (±10-15%)
- Use `--model` flag for model-specific estimation

### MCP responses still too long
- Use `*_efficient` tool variants
- Set lower `maxTokens` in tool arguments
- Enable compression in tool calls

## Files Added

- `lib/token-utils.js` - Core token counting and budget tracking
- `lib/context-compression.js` - Context and prompt compression
- `lib/token-config.json` - Configuration defaults
- Enhanced `lib/mcp-server.js` - Token-efficient tools
- Enhanced `lib/cli.js` - Token CLI commands

## Next Steps

- Integrate with OpenClaw gateway for real-time token tracking
- Add token usage logging for analytics
- Implement per-IDE token optimization profiles
- Add token budget enforcement in LLM routing
