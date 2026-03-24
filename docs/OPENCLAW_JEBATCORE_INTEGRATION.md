# OpenClaw JEBATCore Integration

This document records the local OpenClaw runtime alignment for JEBATCore.

## Runtime Identity

The live OpenClaw workspace is configured to present the main agent as `JEBATCore` with Hermes operating behavior.

Current local runtime pieces:

- OpenClaw config: `~/.openclaw/openclaw.json`
- Workspace identity: `~/.openclaw/workspace/IDENTITY.md`
- Bootstrap and operating guides:
  - `~/.openclaw/workspace/BOOTSTRAP.md`
  - `~/.openclaw/workspace/SOUL.md`
  - `~/.openclaw/workspace/AGENTS.md`
  - `~/.openclaw/workspace/ORCHESTRA.md`

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

Those UI changes are source-level changes in the local OpenClaw repo and still require a UI build/deploy step to affect the served dashboard bundle.
