# OpenClaw JEBATCore Integration

This document records the local OpenClaw runtime alignment for JEBATCore and the repo-packaged export bundle.

## Runtime Identity

The live OpenClaw workspace is configured to present the main agent as `JEBATCore` with Hermes operating behavior.

Current live runtime pieces:

- OpenClaw config: `~/.openclaw/openclaw.json`
- Workspace identity: `~/.openclaw/workspace/IDENTITY.md`
- Bootstrap and operating guides:
  - `~/.openclaw/workspace/BOOTSTRAP.md`
  - `~/.openclaw/workspace/SOUL.md`
  - `~/.openclaw/workspace/AGENTS.md`
- `~/.openclaw/workspace/ORCHESTRA.md`

Versioned repo bundle:

- `integrations/openclaw/openclaw.template.json`
- `integrations/openclaw/.env.example`
- `integrations/openclaw/workspace/`
- `scripts/export_openclaw_jebatcore.py`

## Agent Layout

The local OpenClaw runtime uses these agent identities:

- `main` -> `JEBATCore`
- `builder` -> `JEBAT Builder`
- `security` -> `JEBAT Security`
- `research` -> `JEBAT Research`

`main` is configured to use the workspace `hermes-agent` skill.

## Model Routing

The local OpenClaw model chain is optimized for response speed first:

1. `google-gemini-cli/gemini-3-flash-preview`
2. `google-gemini-cli/gemini-3.1-pro-preview`
3. `zai/glm-5`
4. `zai/glm-4.7-flash`
5. local Ollama fallbacks

## Dashboard Rebrand

The OpenClaw UI source tree was patched locally to rebrand the control UI from `OpenClaw` to `JEBATCore`.

Patched source files in the local OpenClaw repo:

- `tools/openclaw/ui/index.html`
- `tools/openclaw/ui/src/ui/components/dashboard-header.ts`
- `tools/openclaw/ui/src/ui/views/login-gate.ts`
- `tools/openclaw/ui/src/ui/app-render.ts`

## Important Note

Those UI changes are source-level changes in the local OpenClaw repo. The local UI bundle has already been rebuilt, but the source still lives outside this repo.

## Export Workflow

To refresh the repo bundle from the live local OpenClaw runtime:

```bash
python3 scripts/export_openclaw_jebatcore.py
```

This keeps `jebat-core` as the versioned source of the JEBATCore/OpenClaw operating setup without committing local secrets or unrelated runtime state.
