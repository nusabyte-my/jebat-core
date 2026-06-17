# MEMORY.md

This file is the root memory index for the workspace.

## Current Operating Memory

- This repository should be treated as a JEBAT workspace with `jebat-core/` as the canonical operating center.
- Canonical startup begins from `jebat-core/BOOTSTRAP.md`.
- Codex sessions should also load `CODEX_PROFILE.md`.
- If duplicate docs exist at the root and in `jebat-core/`, prefer the `jebat-core/` copy unless the user explicitly directs otherwise.

## Session Notes

- Daily session records live in `memory/YYYY-MM-DD.md`.

## Durable Decisions

- Architecture and operating decisions live in `jebat-core/vault/decisions/`.
- See `jebat-core/vault/decisions/2026-04-08-jebatcore-canonical-startup.md` for the accepted JEBATCore startup rule.
- See `jebat-core/vault/decisions/2026-04-16-llamacpp-jebat-llm-production-cutover.md` for the production `llama.cpp` cutover, VPS tuning, JEBAT chat preset routing, and the current `.65 -> .206` remote model-host topology.

## Current Production LLM Topology

- `72.62.254.65` is the public-facing JEBAT node for `jebat.online`.
- `72.62.255.206` is the stronger active `llama.cpp` model host for JEBAT chat.
- The live JEBAT stack on `.65` routes `LLAMA_CPP_HOST` to `.206` instead of using a local `.65` model process.
- `.206` exposes TCP `8081` only to `.65` for this path.
- The `.65 -> .206` remote `llama.cpp` route has been verified through the live OpenAI-compatible JEBAT chat endpoint with `provider: "llamacpp"`.
