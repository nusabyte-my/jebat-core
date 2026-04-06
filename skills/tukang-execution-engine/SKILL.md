# Tukang Execution Engine — Autonomous Plan Execution

**Role:** JEBAT's autonomous code execution pipeline
**Adapted from:** [umputun/ralphex](https://github.com/umputun/ralphex)
**Type:** Execution skill

## What We Adopt

### Autonomous Execution Pipeline

ralphex solves Claude Code's context-degradation problem by breaking plans into discrete tasks, each executed in a fresh, minimal-context session:

```
Phase 1: Task Execution → Parse plan, run task in fresh Claude session, validate, commit
Phase 2: First Code Review → 5 parallel review agents (quality, implementation, testing, simplicity, docs)
Phase 3: External Review → Independent reviewer (OpenAI Codex or custom LLM)
Phase 4: Second Code Review → 2 focused agents (quality + implementation)
Optional: Finalize → Rebase/squash commits
```

### Key Patterns to Adopt

1. **Plan Parser** — Markdown plans with `### Task N:` headers, `[ ]` checkboxes, `## Validation Commands`
2. **Task Runner** — Fresh session per task, auto-commit on completion
3. **Parallel Review** — 5 agents reviewing simultaneously via Task tool
4. **Git Worktree Isolation** — Concurrent plan execution without branch conflicts
5. **Docker Sandbox** — Restricted filesystem access, non-root execution
6. **Ctrl+\ Pause** — Mid-run plan editing capability

### Integration with JEBAT

Maps to Tukang + Penyemak agents:
- Tukang = Task execution (Phase 1)
- Penyemak = Review pipeline (Phases 2-4)

```
JEBAT Plan → Parse → Execute (Tukang) → Review (Penyemak x5) → External Review → Finalize
```

## Plan Format

```markdown
# Feature: [Name]

### Task 1: [Description]
- [ ] Implement X in file Y
- Validation: `npm test`, `npm run lint`

### Task 2: [Description]
- [ ] Add tests in tests/
- Validation: `npm test`

## Validation Commands
- `npm run lint`
- `npm test`
- `npm run build`
```

## Review Agent Prompts (Adapted)

### Quality Agent
```
Review this implementation for:
- Code correctness and edge cases
- Error handling completeness
- Input validation
- Type safety
```

### Implementation Agent
```
Review for:
- Architecture and design patterns
- Abstraction quality
- Code duplication
- Performance implications
```

### Testing Agent
```
Review for:
- Test coverage gaps
- Missing edge cases
- Integration test needs
- Test quality
```

### Simplification Agent
```
Review for:
- Over-engineering
- Unnecessary abstractions
- Code that can be removed
- Simpler alternatives
```

### Documentation Agent
```
Review for:
- Missing documentation
- Outdated comments
- API documentation needs
- README updates
```

## Configuration

```yaml
tukang:
  max_iterations: 3
  review_patience: 2  # max review loops before stalemate
  sandbox: docker     # or "local" for dev
  auto_commit: true
  validation_commands:
    - "npm run lint"
    - "npm test"
    - "npm run build"
```

## Safety

- NEVER execute without a written plan
- ALWAYS run validation commands before marking task complete
- NEVER skip the review pipeline
- ALWAYS commit after each task
- Docker sandbox for untrusted code
- Git worktree isolation for parallel work
