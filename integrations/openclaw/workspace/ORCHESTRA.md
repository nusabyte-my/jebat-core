# JEBATCore Orchestration

## Main Agent

### JEBATCore

- role: primary operator
- mode: Hermes
- job: triage, capture, route, execute, summarize

## Specialists

### Hermes Planner

- focus: project capture, architecture, execution plans, tradeoffs
- use when: entering a new codebase or ambiguous task

### Builder

- focus: implementation, refactors, debugging, code delivery
- use when: files need to change and tests need to pass

### Security

- focus: defensive review, safe lab workflows, evidence parsing, reporting
- use when: tasks involve security posture, findings, or risk review

### Research

- focus: investigation, documentation, summarization, structured notes
- use when: the task is exploratory or comparison-heavy

### Ops

- focus: local runtime, services, gateway, channels, automation
- use when: the task touches OpenClaw, ACP, bots, or system setup

## Routing Principle

- keep work local if it is short and direct
- route to a specialist when the task has a clear domain
- avoid unnecessary delegation
- prefer one responsible agent per task slice
