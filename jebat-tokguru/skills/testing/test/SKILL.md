---
name: test
description: Run focused verification, interpret failures, and prove the change with the smallest meaningful test surface
category: testing
tags:
  - test
  - verification
  - regression
  - validation
  - debugging
ide_support:
  - vscode
  - zed
  - cursor
  - claude
  - gemini
author: JEBAT Team
version: 1.0.0
---

# Test

## Description
Use this skill when a change needs proof. Choose the narrowest verification that can confirm behavior, then expand only if the result is inconclusive.

## When to Use
- Verifying a bug fix
- Checking that a route or CLI command still works
- Running focused regression tests after a patch
- Reproducing a failure before changing code

## Operating Pattern
- Start with syntax and targeted tests
- Prefer one meaningful test over a noisy full-suite run
- Record what was verified and what remains unverified
- If a test fails, isolate whether the failure is new or pre-existing

## Response Defaults
- State what you tested
- State whether it passed or failed
- If it failed, show the failure surface and next fix target

## Example Usage
```text
@test Verify the WebUI provider selector change with a syntax check, focused tests, and a live route probe.
```
