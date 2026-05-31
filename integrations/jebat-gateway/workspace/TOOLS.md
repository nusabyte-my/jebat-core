# TOOLS.md

## Local Runtime Notes

- Primary gateway config: `~/.jebat-gateway/jebat-gateway.json`
- State dir: `~/.jebat-gateway`
- Main workspace: `~/.jebat-gateway/workspace`
- Gateway service: `jebat-gateway-gateway.service`

## Model Routing

- Primary: Google Gemini Flash via `google-gemini-cli`
- Fallbacks: Google Pro, ZAI, then local Ollama

## Working Mode

- `JEBATCore` is the main assistant identity
- Jebat Agent is the capture-first operating mode
- Workspace skills are the preferred way to add repeatable behaviors
