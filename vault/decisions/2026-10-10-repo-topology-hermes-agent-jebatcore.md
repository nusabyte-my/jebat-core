# 2026-10-10 — Repo topology: `jebat-core` (public) vs `hermes-agent-jebatcore` (private)

## Decision

Repositories stay **separate**:

- **`nusabyte-my/jebat-core`** (public) — remains the JEBAT codebase and install/clone home. All
  `raw.githubusercontent.com/nusabyte-my/jebat-core/main/install.sh` URLs stay as they are.
- **`nusabyte-my/hermes-agent-jebatcore`** (private) — the **control-room / fleet repo** (formerly
  `nusabyte-my/nusabyte-hermes`; recreated + history-merged 2026-10-09 ~22:04 MYT). Agents, bus,
  runbooks, fleet skills live there; it does not host the JEBAT installer.

## Context / evidence

- On 2026-10-09 the control room was renamed/recreated as `hermes-agent-jebatcore` and set **private**
  (anonymous 404s are the expected response for private repos — this initially read as "rename not done").
- A control-checkout commit (`b95b39a`, "point install/clone URLs at hermes-agent-jebatcore") rewrote
  JEBAT's README install/clone URLs to the new repo. Pushing it would have broken public installs:
  the target repo has **no `install.sh`** (verified via API) and is **private** (raw installs would 401/404).
- That commit was parked as branch `park/hermes-urls`, then **dropped** on 2026-10-10 per this decision.

## Consequences

- `D:/Jebat` and `D:/jebatcore` remotes remain `github.com/nusabyte-my/jebat-core.git`.
- The landing/docs/README install URLs are unchanged and live.
- If consolidation is ever revisited, the parked changes can be recreated from this record; the
  blocking questions then are (a) repo visibility and (b) monorepo layout (root collisions on
  README/LICENSE/scripts/docs/skills).
