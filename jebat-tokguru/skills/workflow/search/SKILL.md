---
name: search
description: Search local or remote sources quickly, narrow results, and surface the highest-signal matches for the task
category: workflow
tags:
  - search
  - discovery
  - triage
  - navigation
  - evidence
ide_support:
  - vscode
  - zed
  - cursor
  - claude
  - gemini
author: JEBAT Team
version: 1.0.0
---

# Search

## Description
Use this skill when the first problem is not implementation but discovery. Search fast, reduce noise, and return the smallest useful set of matches that moves the task forward.

## When to Use
- Finding where a feature is implemented
- Locating routes, handlers, and config
- Narrowing a large codebase before editing
- Searching docs, logs, or output for a specific signal

## Operating Pattern
- Start with precise terms, then broaden only if needed
- Prefer exact matches before semantic guesses
- Keep findings grouped by path or source
- Turn search results into a direct next action

## Response Defaults
- Show the best match first
- Include the path or source location
- State why that match matters

## Example Usage
```text
@search Find every provider and model selector in this repo and show me which file controls the live shell.
```
