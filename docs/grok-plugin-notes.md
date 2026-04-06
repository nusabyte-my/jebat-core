# Grok / xAI Auth Plugin Notes

## Current status

The attempted `xai-grok-auth` config was rolled back because the plugin is **not actually installed**.
OpenClaw CLI on this machine does **not** accept raw HTTPS URLs as plugin install specs.

Observed error:
- `unsupported npm spec: URLs are not allowed`

Observed consequence:
- `grok-sso` provider is unavailable until the plugin is truly installed
- stale config entries cause warnings and should be removed

## What is working now

- Built-in `xai` provider is loaded and available
- `xai/grok-4` remains the valid Grok path for OpenClaw right now
- fish helper `use-grok-api` remains useful

## What is not working yet

- `grok-sso` provider
- `xai-grok-auth` plugin entry
- `use-grok-sso` as a real model target

## Next step

Find the correct install source format for the plugin, likely one of:
- marketplace id
- clawhub/package spec
- npm package name
- local path

Only after that should the config be re-added.
