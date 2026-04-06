---
name: agent-dispatch
description: Multi-agent orchestration for JEBAT. Use when tasks span multiple domains, require parallel specialists, or need explicit routing, sequencing, and verification.
category: orchestration
tags:
  - orchestration
  - multi-agent
  - routing
  - workflow
ide_support:
  - claude
author: JEBATCore / NusaByte
version: 1.0.0
---

# Agent Dispatch Skill

## Shared Core

This skill inherits the shared Codex operating core in [`skills/_core/CODEX_CORE.md`](../_core/CODEX_CORE.md).
Use the shared core for baseline behavior; this file adds orchestration rules for multi-agent work.

## Jiwa — Panglima Pengarah

Orchestrate with discipline: route well, keep prompts self-contained, and separate implementation from validation.

## Dispatch Protocol

1. Classify the request by domain and risk
2. Choose the minimum specialist set that covers the task
3. Parallelize investigation for independent questions
4. Convert findings into explicit specs before execution
5. Assign implementation and verification separately where possible

## Routing Heuristics

- product feature: `app-development` + `fullstack` + `database` as needed
- frontend build: `ui-ux` + `web-developer`
- security review: `security-pentest` + `qa-validation`
- growth work: `marketing` + `copywriting` + `seo` + `content-creation`
- operations work: `automation` + domain specialist affected by the automation
- exploratory task: `research-docs`, then route to execution specialists
