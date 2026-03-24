# OpenClaw JEBATCore Bundle

This directory packages the local JEBATCore OpenClaw setup into versioned repo assets.

Contents:

- `openclaw.template.json`: sanitized OpenClaw config template
- `.env.example`: required environment variables
- `workspace/`: JEBATCore workspace bootstrap files
- `workspace/skills/hermes-agent/`: Hermes skill for OpenClaw workspace loading

Use this bundle when you want to recreate the JEBATCore OpenClaw runtime on a new machine without copying private state directly from `~/.openclaw`.

## Apply Bundle

1. Copy `openclaw.template.json` to `~/.openclaw/openclaw.json`
2. Copy `workspace/` to `~/.openclaw/workspace/`
3. Copy `.env.example` to `~/.openclaw/.env`
4. Replace placeholders with real tokens and paths
5. Restart the gateway

```bash
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway.service
```

## Refresh From Live Runtime

To export the current local runtime back into this repo bundle:

```bash
python3 scripts/export_openclaw_jebatcore.py
```
