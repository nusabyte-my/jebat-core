# TOOLS.md

## Local Runtime Notes

- Primary gateway config: `~/.openclaw/openclaw.json`
- State dir: `~/.openclaw`
- Main workspace: `~/.openclaw/workspace`
- Gateway service: `openclaw-gateway.service`

## Model Routing

- Primary: Google Gemini Flash via `google-gemini-cli`
- Fallbacks: Google Pro, ZAI, then local Ollama

## Working Mode

- `JEBATCore` is the main assistant identity
- Hermes is the capture-first operating mode
- Workspace skills are the preferred way to add repeatable behaviors
