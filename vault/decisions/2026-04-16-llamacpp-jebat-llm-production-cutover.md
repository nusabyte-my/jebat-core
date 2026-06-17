# 2026-04-16: `llama.cpp` production cutover for JEBAT chat

## Status

Accepted and deployed on the active VPS pair.

## Decision

JEBAT chat now uses a self-hosted `llama.cpp` backend as the primary production LLM path across the active VPS pair:

- `72.62.254.65` is the public-facing JEBAT node for `jebat.online`
- `72.62.255.206` is the stronger active `llama.cpp` model host for the live JEBAT stack

The active local model identity is:

- runtime model id: `jebat-llm`
- source model family: `HauhauCS/Gemma-4-E4B-Uncensored-HauhauCS-Aggressive`
- deployed file alias: `/srv/models/jebat-llm.gguf`

JEBAT runtime is configured with:

- `JEBAT_LLM_PROVIDER=llamacpp`
- `JEBAT_LLM_MODEL=jebat-llm`
- `LLAMA_CPP_HOST` routed from Dockerized JEBAT services to the host `llama-server`

## Why

- The project needed a VPS-resident primary LLM instead of depending on external providers.
- CPU-only VPS hardware made `llama.cpp` the practical serving path.
- Using a stable local alias, `jebat-llm`, keeps JEBAT config independent from upstream HF naming and quant file details.

## Operational notes

- `llama.cpp` is installed on both VPSes and served as a systemd service: `llama-cpp-jebat.service`
- The active public JEBAT stack on `.65` now uses `LLAMA_CPP_HOST=http://72.62.255.206:8081`
- JEBAT API and WebUI run in Docker and reach `llama.cpp` through the configured remote host path, not container loopback
- `.206` allows TCP `8081` only from `.65` for this production route
- Earlier Docker bridge UFW allowances were needed while the model was hosted locally on `.65`
- The current `.65 -> .206` production chat path was verified live with `provider: "llamacpp"`

## VPS topology and tuning

### `72.62.254.65`

- CPU-only
- public-facing JEBAT API/WebUI node
- remote model client for live chat
- fallback-capable local `llama.cpp` install remains available if routing changes back

### `72.62.255.206`

- CPU-only
- active production `llama.cpp` host
- tuned higher
- `ctx-size 4096`
- `threads 8`
- `parallel 2`

## Chat presets added

Three practical preset identities were added for day-to-day use:

- `jebatcpp-coding`
- `jebatcpp-roleplay`
- `jebatcpp-uncensored`

These presets map to different system prompts and sampling defaults while still routing through the same `llama.cpp` backend.

## Verification state

Verified on both VPSes via the live OpenAI-compatible chat endpoint:

- `jebat-llm`
- `jebatcpp-coding`
- `jebatcpp-roleplay`
- `jebatcpp-uncensored`

All returned successful completions with `provider: "llamacpp"`.

The active production route was also verified from `.65` through the remote `.206` host:

- `.65` JEBAT API returned successful chat completions with `provider: "llamacpp"`
- `LLAMA_CPP_HOST` on `.65` was confirmed as `http://72.62.255.206:8081`
- `.206` health and completion traffic were reachable only after the narrow allow rule from `.65`

## Follow-up expectations

- Keep `llamacpp` as the default local provider path unless the user explicitly changes production routing.
- Prefer updating the preset prompts and sampling in shared runtime code rather than scattering them across multiple entrypoints.
- When debugging production chat regressions, check:
  - `llama-cpp-jebat.service`
  - Docker bridge reachability to port `8081`
  - UFW rules for the active Docker bridge subnets
  - JEBAT API `/api/v1/chat/completions` provider field
