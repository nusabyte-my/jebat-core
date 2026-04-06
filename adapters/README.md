# JEBAT Adapters ⚔️

Deploy JEBAT context to any IDE or LLM interface.

## Quick Install

```bash
# From jebatcore/adapters/
python install.py --ide cursor      --target /path/to/project
python install.py --ide vscode      --target /path/to/project
python install.py --ide zed         --target /path/to/project
python install.py --ide trae        --target /path/to/project
python install.py --ide antigravity --target /path/to/project
python install.py --ide all         --target /path/to/project

# Print universal prompt to stdout
python install.py --print
```

## IDE-Specific Notes

| IDE | File Installed | How It Loads |
|-----|----------------|--------------|
| Cursor | `.cursorrules` | Auto-loaded from project root |
| VS Code (Copilot) | `.github/copilot-instructions.md` | Auto-loaded by GitHub Copilot |
| Zed | `.zed/jebat-system-prompt.md` | Paste into Settings → assistant → system_prompt |
| Trae | `.trae/jebat-context.md` | Paste into Trae custom instructions |
| Antigravity | `.antigravity/jebat-context.md` | Paste into AI context field |
| Generic / any LLM | `JEBAT-CONTEXT.md` | Paste SYSTEM PROMPT block into any chat UI |

## Universal Prompt

`jebat-universal-prompt.md` — master compiled context.
Use for Open WebUI, LM Studio, any API LLM, or IDEs not listed above.

## What Gets Injected

- JEBAT identity and role
- emmet's user profile and stack
- Behaviour rules (direct, no basa-basi)
- Adat Panglima (capture-first protocol)
- Canonical roles + routing rules
- Safety rules
- Active ecosystem context

## Validation

```bash
python validate.py
```

Use `sync-check.md` after changes to the core, routing, templates, or checklists.

For a broader repo check from the workspace root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\validate-workspace.ps1
```
