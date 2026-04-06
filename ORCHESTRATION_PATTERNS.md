# Orchestration Patterns for Hermes + Jebat

## Goal

Standardize how Jebat delegates, coordinates, and merges specialist work.

---

## Pattern 1: Local-first execution
Use direct tools when:
- task is small
- workspace is clear
- no specialist viewpoint is needed

## Pattern 2: Single specialist delegation
Spawn one specialist when:
- task is deep but narrow
- coding, analysis, or research requires focus

## Pattern 3: Multi-specialist council
Use multiple specialists when:
- decision quality matters more than speed
- security, architecture, and product tradeoffs collide

### Council roles
- analyst: evidence and structure
- researcher: source grounding
- security: risk and exposure
- developer: implementation realism

## Pattern 4: Sequential handoff
Use when outputs depend on previous work.

Example:
1. researcher gathers evidence
2. analyst structures findings
3. security reviews risks
4. main agent delivers final synthesis

### Handoff minimums
Every handoff should include:
- task objective
- current status
- evidence or artifacts produced
- open questions
- success criteria for the next step

## Pattern 5: Verification loop
After delegated work:
1. inspect result
2. verify against task
3. merge into one answer
4. store key outcomes in memory

### Reviewer / builder split
When quality matters:
- builder produces draft/output
- reviewer checks correctness, completeness, and risks
- main agent decides whether to ship

---

## Hermes routing rule

Do not spawn agents just because you can.
Spawn them only when they reduce risk, improve quality, or save real time.
