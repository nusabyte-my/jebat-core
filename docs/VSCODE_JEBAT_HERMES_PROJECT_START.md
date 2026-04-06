# VS Code JEBAT/Hermes Project Start Guide

This guide is the default operating playbook for using JEBAT in VS Code before starting any project.

The goal is simple:

1. capture the project first
2. activate JEBAT/Hermes mode
3. select the right skills
4. only then start planning, coding, or reviewing

## Outcome

If you follow this guide, JEBAT should behave as:

- a repo-aware technical copilot
- a low-noise Hermes-style personal assistant
- a small internal multi-agent team when the task is complex
- a skill-guided assistant instead of a generic chat bot

## Core Rule

Before starting work on any new project, JEBAT must first capture:

- the project goal
- the tech stack
- the current repo structure
- constraints and success criteria
- the active JEBAT/Hermes skills for the session

No implementation should start before that context is captured.

## Recommended VS Code Setup

Use one of these paths:

- Continue with an OpenAI-compatible JEBAT endpoint
- Continue with your preferred LLM provider and local JEBAT workflow
- terminal-first workflow using `jebat-cli` inside VS Code

If you want the most predictable setup, use the VS Code terminal plus `jebat-cli`.

## Default Startup Routine

Run this every time you start a new project or open an unfamiliar repo.

### Step 1: Open the repo root in VS Code

Make sure the workspace is the actual project root, not a parent folder with unrelated repos.

### Step 2: Check your local JEBAT path

```bash
jebat-cli llm-best-provider
jebat-cli skills show hermes-agent
```

### Step 3: Start JEBAT in Hermes mode

For general project takeover:

```bash
jebat-cli chat-project "Act as Hermes for this project. First capture the repo, stack, constraints, risks, and next steps before changing anything." --project-path . --skill hermes-agent
```

For a Python-heavy codebase:

```bash
jebat-cli chat-project "Act as Hermes for this Python project. Capture the repo first, then propose the first execution plan." --project-path . --skill hermes-agent --skill python-patterns
```

For architecture-heavy work:

```bash
jebat-cli chat-project "Act as Hermes and review this architecture before implementation starts." --project-path . --skill hermes-agent --skill cortex-reasoning
```

## Capture-First Prompt

Use this prompt in VS Code chat when entering a new project:

```text
Act as JEBAT in Hermes mode for this project.
Before starting implementation, capture:
- project purpose
- stack and runtime
- key directories and entrypoints
- constraints, risks, and missing context
- the best skill set to use for this repo

Then return:
1. project snapshot
2. suggested active skills
3. first execution plan
4. questions only if they are true blockers
```

## Required First Response Shape

For a new project, JEBAT should answer in this order:

1. project snapshot
2. active skills
3. first plan
4. immediate risks or blockers

It should not jump straight into code unless the repo is already well understood.

## Recommended Skill Combinations

Use `hermes-agent` as the default anchor skill, then add one or two focused skills.

### General software project

- `hermes-agent`
- `cortex-reasoning`

### Python backend

- `hermes-agent`
- `python-patterns`

### React or frontend project

- `hermes-agent`
- `react-patterns`

### Security review

- `hermes-agent`
- `api-security-best-practices`

### Docker or infrastructure work

- `hermes-agent`
- `docker-expert`

### RAG, LLM, or AI workflow

- `hermes-agent`
- `rag-engineer`

## VS Code Workflow Patterns

### Pattern 1: Terminal-first

Best when you want reproducible project startup.

```bash
jebat-cli
jebat-cli skills list
jebat-cli chat-project "Take over this repo in Hermes mode and capture it first." --project-path . --skill hermes-agent
```

### Pattern 2: Continue or chat panel

Paste the capture-first prompt into the chat panel and explicitly name the active skills:

```text
Use hermes-agent and cortex-reasoning.
Capture this repo first, then propose the first work plan.
Do not start coding until the project snapshot is complete.
```

### Pattern 3: Session pinning

If you are staying in one repo for a while, pin the skill set for the session:

```bash
jebat-cli chat-repl --project-path . --skill hermes-agent --skill python-patterns
```

## JEBAT/Hermes Behavior Standard

When used at project start, JEBAT should:

- inspect before proposing
- plan before editing
- keep the plan small
- stay concise
- verify changes after implementation
- prefer one coherent response over multiple simulated personalities

Internally, the work can be split like this:

- `planner`: defines scope and first steps
- `builder`: makes code or config changes
- `reviewer`: checks for regressions and weak assumptions
- `operator`: verifies commands, runtime behavior, and usage

## Project Kickoff Checklist

Use this checklist at the beginning of each repo:

- repo root confirmed
- provider/auth working
- relevant skills selected
- project snapshot captured
- first plan written
- blockers identified
- only then start edits

## Suggested VS Code Workspace Notes

Keep a `PROJECT_START.md` or `.github/copilot-instructions.md` in each repo with:

- project goal
- coding standards
- deployment constraints
- testing commands
- preferred JEBAT skills

Recommended example:

```md
# Project Start Notes

- Default assistant mode: Hermes
- Preferred skills: hermes-agent, python-patterns
- Main test command: pytest
- Main run command: python -m app
- Main risk areas: auth, billing, migrations
```

## Good Opening Prompts

```text
Act as Hermes for this repo. Capture the project first, then give me the first plan.
```

```text
Use hermes-agent and python-patterns. Review the repo structure before suggesting changes.
```

```text
Use hermes-agent and cortex-reasoning. Summarize the architecture, risks, and best next action.
```

## Bad Opening Prompts

These usually produce worse outcomes:

- "fix everything"
- "build the app"
- "make this better"
- "do whatever you think"

They are too vague and skip project capture.

## Recommended Command Set

```bash
jebat-cli
jebat-cli llm-best-provider
jebat-cli skills list
jebat-cli skills search python
jebat-cli skills show hermes-agent
jebat-cli chat-project "Act as Hermes and capture this repo first." --project-path . --skill hermes-agent
jebat-cli chat-repl --project-path . --skill hermes-agent --skill cortex-reasoning
```

## Minimal Rule for Every New Project

If you remember only one thing, use this:

```text
Act as JEBAT in Hermes mode. Capture the project first, then plan, then implement.
```
