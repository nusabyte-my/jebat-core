# DESIGN.md

## Workspace (top-level tree)

Purpose:
- Canonical source of truth for the workspace; the top-level tree is what runs and what changes
- `jebat-core/` (frozen 2026-07-04) was removed on 2026-09-30; its visual direction carries on in the top-level tree
- Its docs, generated interfaces, and setup experiences define the tone for the rest of the stack

Visual direction:
- Terminal-native, black/emerald/cyan identity
- Strong information hierarchy
- Premium technical minimalism, not startup landing-page aesthetics

Priority surfaces:
- setup flows
- status / doctor / health views
- memory and vault tooling
- orchestration and admin panels

Rules:
- Default to dense, useful layouts
- Make system state visible
- Prefer utility and correctness over decorative UI

## Public landing — original Malam / Tembaga / Pucuk palette

User-selected restoration (2026-10-07) applies to `index.html`, not the terminal/workspace surfaces above.
- Bone base `#F7F4EE`; copper `#C97A40`; green `#2F6F55`; near-black evidence panels `#080A09`. Darker copper action/text shades preserve readable contrast.
- Self-hosted Space Grotesk display, Inter body, Geist Mono code; assets/fonts includes OFL licenses.
- Hard-stop accent gradients, restrained glass/orbs, one accent per card, visible keyboard focus.
- Public tokens: `assets/jebat-creative-tokens.css`; layout: `assets/jebat-landing.css`.
- Command previews use actual recorded output from `assets/jebat-cli-captures.json`, explicitly labelled as captures, never live health.
- No clipped mobile content; native FAQ disclosures; accessible selected/menu state; copy errors name a recovery path.
- Shared 12px-radius buttons: minimum 44px targets, visible focus, distinct selected/pressed states, reduced-motion support, and fixed-size loading indicators.
- Copy controls reserve label/icon space, show persistent inline errors with manual-copy recovery, and cancel old success-reset timers on retry. Snippet buttons have contextual accessible names.
- Browser verification: 320/375/414/768/1440px; clipboard success and blocked-copy retry; capture failure/recovery; menu Escape and installation-tab arrows. Measured control-label contrast: 5.71:1 minimum among sampled buttons.
- Hero setup shortcuts target stable installation-tab anchors: `#install-tab-cli`, `#install-tab-ide`, and `#install-tab-remote`. Clicks and bookmarked routes select the existing tab, show its requirements, and move keyboard focus to it.
- `#project-audit` precedes architecture detail. Its copyable `workflow-audit` example prints a playbook, not fabricated findings or automatic execution.
- All five deployment methods show method-specific prerequisites above their command/copy control; remote setup distinguishes a server connection from local installation.
- Quick-win verification: no new content overflow at 320/375/414/768/1440px; hero route selection, bookmarked remote route, keyboard Home/ArrowRight, and native audit-command clipboard copy passed. The actual CLI example printed its scoped playbook successfully.
- IDE configuration tracks the selected installation method and client: CLI/IDE use `jebat` stdio, npx uses its launcher, Docker uses loopback HTTP on port 8100, and Remote HTTP uses a replaceable HTTPS endpoint. VS Code snippets use the `servers` root; Cursor/Windsurf use `mcpServers`. HTTP examples must be adapted to the gateway's authentication header and existing server key.
- Local post-install checks print `jebat doctor` and `jebat mcp ide-config` (through npx for that launcher). They check local state and print templates—not a live connection. Docker/remote checkpoints instead require authenticated IDE tool discovery.
- The archetype matrix belongs to `#workbench`, not installation. Tool tiers, model routing, and retrieval internals use native technical disclosures: collapsed by default at ≤640px, expanded above that breakpoint. Direct links expand the relevant disclosure; without JavaScript all remain open.
- Setup verification: all 15 installation/client combinations produced matching transports and client roots; checkpoint clipboard copy passed. No content overflow at 320/375/414/768/1440px. Native disclosure keyboard open/close and visible focus passed.
