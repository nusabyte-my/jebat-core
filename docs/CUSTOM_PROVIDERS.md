# Custom Providers For JEBAT

This guide covers JEBAT's five built-in **custom** (non-standard) LLM gateways and how to
configure, authenticate, and use them. Custom providers are all **OpenAI-compatible**
(`/v1/chat/completions` + `/v1/models`) so any gateway that speaks that protocol works.

## Supported custom providers

| Provider        | Env key                  | Base URL env              | Notes                                  |
| --------------- | ------------------------ | ------------------------- | -------------------------------------- |
| `opencode_go`   | `OPENCODE_GO_API_KEY`    | `OPENCODE_GO_BASE_URL`    | OpenCode Go gateway                    |
| `opencode_zen`  | `OPENCODE_ZEN_API_KEY`   | `OPENCODE_ZEN_BASE_URL`   | OpenCode Zen, supports SSO/OAuth       |
| `zenmux`        | `ZENMUX_API_KEY`         | `ZENMUX_BASE_URL`         | Token-multiplexing router             |
| `tokerrouter`   | `TOKERROUTER_API_KEY`    | `TOKERROUTER_BASE_URL`    | Token-usage router                     |
| `agent_router`  | `AGENT_ROUTER_API_KEY`   | `AGENT_ROUTER_BASE_URL`   | Agent orchestration, supports SSO/OAuth|

## Setup via CLI (recommended)

Run the first-run wizard and pick a custom provider:

```bash
jebat init --provider opencode_go
```

The wizard follows an **auth-first** flow (OpenCode style):

1. **Base URL** — the gateway endpoint (e.g. `https://go.opencode.example/v1`).
2. **Auth** — if the gateway supports SSO/OAuth, answer `y`, open the URL, and paste the
   access token. The token is stored as the bearer credential.
3. **API key** — paste the API key. If you already used OAuth, leave this blank to reuse the
   token, or enter an additional key.
4. **Model** — JEBAT fetches the live `/v1/models` catalog and lets you pick one. If the
   gateway is unreachable it falls back to the placeholder catalog (see below) or free text.
5. Credentials are written to `~/.jebat/secrets.env` and `provider`/`model` to
   `~/.jebat/config.yaml`. Connectivity is probed automatically.

Verify later with:

```bash
jebat auth test opencode_go
jebat doctor --probe
```

## Setup via environment / WebUI

You can set the same values directly:

```bash
export OPENCODE_GO_BASE_URL="https://go.opencode.example/v1"
export OPENCODE_GO_API_KEY="sk-..."
```

Or use the WebUI provider picker (`/webui` → Provider Auth): select the custom provider,
enter the API key (and the base URL in the host field), and save. The WebUI writes these to
its `provider_auth.json` store, which `get_provider_secret` reads automatically.

## Using a custom provider for inference

Once configured, set it as the active provider in `~/.jebat/config.yaml`:

```yaml
model:
  provider: opencode_go
  model: opencode-go/default
  temperature: 0.2
```

JEBAT's LLM router (`jebat/llm/providers.py` → `CustomOpenAIProvider`) will POST to
`{BASE_URL}/v1/chat/completions` with `Authorization: Bearer {API_KEY}`. Custom providers
also work as entries in `fallback_providers`.

## Placeholder model catalog

Each custom provider ships with a small **placeholder** `default_models` list
(`jebat/features/auth/custom_providers.py`). These are shown only when the live
`/v1/models` fetch is unreachable. Replace them with real model ids, or rely on the live
catalog from the init wizard / WebUI. Example:

```python
"opencode_go": CustomProvider(
    ...
    default_models=("opencode-go/default", "opencode-go/go-large"),
)
```

## Adding a new custom provider

1. Add a `CustomProvider` entry to `CUSTOM_PROVIDERS` in
   `jebat/features/auth/custom_providers.py` (id, label, `*_API_KEY` env, `*_BASE_URL` env,
   `models_path`).
2. Add the `*_API_KEY` to `PROVIDER_ENV_MAP` in `jebat/llm/auth.py`.
3. Done — `SUPPORTED_PROVIDERS`, the CLI wizard, `auth test`, the LLM router, and the WebUI
   catalog all pick it up automatically via `CUSTOM_PROVIDERS`.
