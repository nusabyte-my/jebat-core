---
name: app-development
description: Product and application delivery across frontend, backend, API, auth, state, and release slices. Use when the task is feature-oriented application work rather than isolated code edits.
category: development
tags:
  - app
  - product
  - feature
  - api
  - auth
  - release
ide_support:
  - claude
author: JEBATCore / NusaByte
version: 1.0.0
---

# App Development Skill

## Shared Core

This skill inherits the shared Codex operating core in [`skills/_core/CODEX_CORE.md`](../_core/CODEX_CORE.md).
Use it for the baseline; this skill adds feature-delivery coordination rules.

## Jiwa — Pembina Aplikasi

Treat each app task as a user outcome crossing multiple layers, not a disconnected file edit.

## App Additions

1. Define the feature outcome first
2. Map the layers touched: UI, API, data, auth, jobs, analytics
3. Identify coupling and release risk before coding
4. Keep the implementation slice small enough to verify end to end
5. Prefer vertical slices over broad refactors

## Deploy When

- building new product features
- coordinating cross-layer bug fixes
- planning release-ready implementation slices
- deciding how UI, backend, and data changes fit together
