# Adapter Sync Check

Use this file whenever the shared JEBAT operating model changes.

## Review Triggers

Run this check after changes to any of these:

- `skills/_core/CODEX_CORE.md`
- `AGENTS.md`
- `ORCHESTRA.md`
- `vault/playbooks/dispatch-matrix.md`
- `vault/templates/`
- `vault/checklists/`

## Adapter Files To Review

- `adapters/jebat-universal-prompt.md`
- `adapters/generic/JEBAT.md`
- `adapters/cursor/.cursorrules`
- `adapters/vscode/copilot-instructions.md`
- `adapters/zed/system-prompt.md`
- `adapters/install.py`

## Minimum Sync Checks

- canonical role list still matches the core
- routing references still match the dispatch matrix
- template and checklist references still exist
- `openclaw.json` safety rule is preserved
- Panglima is treated as the primary mode
- Hermes is only described as compatibility, if mentioned at all

## Validation

Run:

```bash
python adapters/validate.py
```

The validator checks for key shared references across adapter entrypoints.
