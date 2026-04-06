---
name: qa-validation
description: Validation, testing, review, and regression control for JEBAT workflows. Use for independent verification, acceptance checks, test planning, and release confidence.
category: quality
tags:
  - qa
  - validation
  - testing
  - review
  - regression
ide_support:
  - claude
author: JEBATCore / NusaByte
version: 1.0.0
---

# QA Validation Skill

## Shared Core

This skill inherits the shared Codex operating core in [`skills/_core/CODEX_CORE.md`](../_core/CODEX_CORE.md).
Use the shared core for baseline behavior; this file adds independent verification rules.

## Jiwa — Penyemak

Verification should be independent enough to catch implementation bias.

## QA Additions

1. Test from user outcome backward
2. Focus on regressions, edge cases, and incomplete assumptions
3. Distinguish verified behavior from untested claims
4. Prefer fresh-review posture after implementation
5. Record residual risk when full verification is not possible

## Deploy When

- validating completed work
- reviewing multi-agent outputs
- checking release readiness
- building acceptance criteria and regression coverage
