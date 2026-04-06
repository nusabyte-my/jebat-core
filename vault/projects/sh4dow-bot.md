# sh4dow.bot

**Status:** Active — web UI layer
**Repo:** https://github.com/nusabyte-my/sh4dow.bot
**Stack:** HTML/CSS/JS (single-page app)

## Active Roles
- Panglima
- Senibina Antara Muka
- Tukang Web
- Jurutulis Jualan
- Penjejak Carian
- Penggerak Pasaran
- Penyemak

## What It Is
Browser-based control UI for the JEBATCore gateway. 3-column OpenClaw-style layout. Dark theme with cyan accent.

## Connects To
- `sh4dow-gateway` on port `18789` (local or VPS)
- Primary API: `https://bot.sh4dow.tech/api` (Ollama)

## Providers Supported
- Ollama (sh4dow.tech), ZAI, OpenAI, Anthropic, Google Gemini, OpenRouter

## Features
- Multi-provider chat with model selector
- Tool call visualization badges (read/write/search/bash)
- Thinking indicator with shimmer effect
- Channel management (Telegram etc.)
- API key storage in localStorage (`nexus_api_key`)
