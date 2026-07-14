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

## Base URL convention

The **base URL must include the OpenAI-compatible API prefix** (typically `/v1`), e.g.
`https://go.opencode.example/v1`. JEBAT appends `/chat/completions` and `/models` to it, so
do **not** include the trailing `/v1/models` or `/v1/chat/completions` — just the base
ending in `/v1`.

## Setup via the shipped CLI (REPL — `jebat`)

The `jebat` command is the `jebat_cli_new` REPL. Add a custom provider interactively:

```
jebat
/provider add
❯ Pick provider (number or name): opencode_go
```

The wizard follows an **OpenCode-style** flow:

1. **Model** — pick from the curated (placeholder) catalog or type a model id.
2. **API base** — the gateway endpoint, e.g. `https://go.opencode.example/v1` (required).
3. **Model** — confirm or type a custom model name.
4. **API key** — paste the key, or leave blank and choose an auth method:
   - `key` — stored inline in `~/.jebat/jebat-cli-providers.json`
   - `env` — read from an env var at runtime (default `{KIND}_API_KEY`, e.g. `OPENCODE_GO_API_KEY`)
   - `store` — read from the JEBAT auth store (`/apikey`)
   For gateways with SSO/OAuth, complete the sign-in out-of-band and paste the resulting
   token as the API key (or store it under the env/store method).
5. The provider is registered and made active; connectivity is testable with `/provider test`.

## Setup via the legacy full CLI (`jebat init`)

The full-featured `jebat/cli/jebat_cli.py` also supports custom providers:

```bash
jebat init --provider opencode_go
```

It follows an **auth-first** flow: **(1)** Base URL → **(2)** optional SSO/OAuth token →
**(3)** API key → **(4)** live `/v1/models` catalog selection. Credentials are written to
`~/.jebat/secrets.env` and `provider`/`model` to `~/.jebat/config.yaml`. Verify with
`jebat auth test opencode_go` and `jebat doctor --probe`.

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

Once configured, the REPL makes the provider active automatically on `/provider add`
(stored in `~/.jebat/jebat-cli-providers.json`). For the legacy `jebat init` CLI, set it as
the active provider in `~/.jebat/config.yaml`:

```yaml
model:
  provider: opencode_go
  model: opencode-go/default
  temperature: 0.2
```

Both CLIs route custom providers through an OpenAI-compatible client that POSTs to
`{BASE_URL}/v1/chat/completions` with `Authorization: Bearer {API_KEY}`. Custom providers
also work as `fallback_providers`.

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
