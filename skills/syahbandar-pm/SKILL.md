# Syahbandar Project Manager — Spec-Driven PM Workflow

**Role:** JEBAT's project management and execution coordinator
**Adapted from:** [automazeio/ccpm](https://github.com/automazeio/ccpm)
**Type:** Orchestration skill

## What We Adopt

### 5-Phase Discipline
Strict workflow ensuring every code commit traces back to a written specification:

```
Phase 1: Brainstorm  → Idea capture, requirement gathering, scope definition
Phase 2: Document    → PRD generation, technical specification
Phase 3: Plan        → Epic decomposition, task breakdown, dependency mapping
Phase 4: Execute     → Parallel agent orchestration, worktree isolation
Phase 5: Track       → Progress reporting, standups, queue management
```

### Key Patterns

1. **PRD → Epic → Task Flow**
   - Natural language → structured PRD → technical epic → decomposed tasks
   - Each task ≤ 10 items with explicit metadata (depends_on, parallel, conflicts_with)

2. **GitHub-Native State Tracking**
   - Uses GitHub Issues as audit trail (not Projects API)
   - Epic issues with sub-issue relationships
   - Local markdown mirrors (`~/.claude/prds/`, `~/.claude/epics/`)

3. **Parallel Agent Orchestration**
   - Analyzes task dependencies automatically
   - Spawns scoped agents for independent streams
   - Manages execution order with conflict boundaries

4. **Git Worktree Isolation**
   - Each epic gets its own worktree (`../epic-<feature>/`)
   - Agents commit directly to isolated branches
   - No context collision between parallel work

5. **Instant Progress Reporting**
   - Bash scripts scan local files for status
   - Zero LLM token cost, instant output
   - Real-time standups, blocked items, next steps

## Integration with JEBAT

Maps to Syahbandar (operations) + Penganalisis (analysis):

```
JEBAT Request → PRD (Syahbandar) → Epic → Tasks → Execute (parallel agents) → Track
```

## File Structure

```
.jebat/
  prds/
    <feature-name>.md          # Product Requirements Documents
  epics/
    <feature>/
      epic.md                  # Technical architecture & decisions
      <issue_id>.md            # Task files (renamed after GitHub sync)
      <issue_id>-analysis.md   # Parallel stream analysis
      updates/                 # Progress logs
```

## Commands

```
jebat plan "Build user auth system"       → Brainstorm → PRD
jebat epic "User auth"                    → Decompose to tasks
jebat sync                                 → Push to GitHub Issues
jebat start "Issue #42"                   → Execute in worktree
jebat status                              → Instant progress report
jebat standup                             → What's blocked, what's next
```

## Task Metadata Schema

```yaml
task_id: "T-001"
title: "Implement login endpoint"
depends_on: ["T-000"]
parallel: false
conflicts_with: ["T-003"]
effort: "2h"
validation: "npm test -- login"
status: "todo"  # todo → in-progress → review → done
github_issue: 42
worktree: "../epic-auth/login-endpoint"
```

## Safety

- NEVER execute tasks without a written epic
- ALWAYS validate dependencies before parallel execution
- NEVER skip the tracking phase
- ALWAYS use worktree isolation
- Log all execution decisions
