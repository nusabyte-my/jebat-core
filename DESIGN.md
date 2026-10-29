# DESIGN.md — JEBAT Creative System

## Direction

JEBAT interfaces are **instruments for real work**, not decorative SaaS templates. The artifact—code, media, transcript, document, query result, booking, conversation, recording, or 3D asset—dominates the surface. Structure follows the task.

This is the governing design system for JEBAT product work. `jebat-creative` supplies domain-specific grammar and quality gates; this file supplies shared visual and interaction decisions.

## Principles

1. **Artifact before chrome.** Show the thing being created or controlled.
2. **One primary action.** Secondary actions remain available without competing for attention.
3. **Specific, not themed.** Layout, density, copy, and motion come from the product domain.
4. **One signature interaction.** Spend visual boldness once per surface.
5. **Honest states.** Never invent metrics, output, screenshots, activity, or customer proof.
6. **Accessible by construction.** Keyboard, contrast, responsive layout, reduced motion, and recovery are part of the design.

## Shape and composition

- Technical, precise, restrained surfaces; avoid generic pill-shaped everything.
- Radius: controls `6px`, inputs `6px`, cards/panels `10px`, modals `14px`, circular avatars/status only.
- Group by alignment, spacing, and hairline borders before shadows or cards.
- No automatic three-card rows, hero/feature/CTA template, decorative numbered sections, or fake application chrome.
- Expert workflows may be dense; every region must answer a user question or enable an action.

## Semantic color tokens

Use semantic tokens in components; raw palette values belong only in token definitions.

| Token | Value | Use |
|---|---|---|
| `--canvas` | `#101112` | Primary work surface |
| `--surface-1` | `#151719` | Panels and navigation |
| `--surface-2` | `#1A1D1F` | Raised/active surfaces |
| `--surface-3` | `#222629` | Hover and selected controls |
| `--border-subtle` | `rgba(255,255,255,.08)` | Structural separation |
| `--text-primary` | `#EDEFEF` | Main content |
| `--text-secondary` | `#A8AEAF` | Supporting content |
| `--text-muted` | `#7D8486` | Metadata; never disabled text |
| `--accent` | `#D1FE17` | Primary action, selection, live state |
| `--accent-ink` | `#141A02` | Text on accent |
| `--danger` | `#FF8D78` | Error/destructive |
| `--warning` | `#F3C969` | Warning |
| `--success` | `#72D6A0` | Confirmed success |
| `--focus` | `#D1FE17` | Focus-visible ring |

Dark surfaces are appropriate for media, code, and operational tools. Content-heavy reading surfaces may introduce a light semantic theme using the same tokens; do not force dark mode on documents.

## Typography

- **Display/product headings:** `Space Grotesk`, 600; roman only.
- **Body/interface:** `Inter`, 400/500/600.
- **Data/code:** `IBM Plex Mono`, 400/500.
- Use tabular numerals for timing, dimensions, token counts, metrics, and waveforms.
- Body text ≥14px in dense expert tools and ≥16px for sustained reading.
- Headings wrap naturally; no italic display type or decorative all-caps eyebrow labels.

## Spacing and layout

Base scale: `4, 8, 12, 16, 24, 32, 48, 64px`.

- Page gutters: 16px mobile, 24px tablet, 32px desktop.
- Main workspace uses fluid content with bounded readable columns where appropriate.
- Mobile: primary artifact and action precede secondary panels; sidebars become drawers or reorder.
- Test at 320, 375, 414, 768px and desktop. No horizontal page scroll.

## Iconography and imagery

- Lucide outline icons, consistent 2px stroke; standard meanings only.
- Icons supplement recognized controls; do not decorate every label.
- Real product captures and real artifacts only. AI-generated imagery must not impersonate product UI.
- Logos follow `logo-design`: original geometry, small-size tests, one-color/reversed tests, and no copied trademark artwork.

## Motion

- Motion communicates capture, playback, progress, causality, or spatial continuity.
- Standard UI: 140–200ms; complex panel transitions ≤320ms.
- No ambient motion that competes with the artifact.
- `prefers-reduced-motion`: remove spatial travel and nonessential transitions; preserve state feedback.

## Interaction states

Every applicable control defines: default, hover, focus-visible, active, disabled, loading, error, success.

- Focus: 2px high-contrast ring with offset; never removed.
- Loading: preserve control dimensions and expose `aria-busy`.
- Errors: explain cause and recovery; never apology-only messages.
- Empty states: direct the next useful action.
- Touch targets should be at least 44×44px on touch-primary surfaces.

## Domain structures

Use `skills/jebat-creative/references/product-grammar.md`:

- Media: studio canvas + model settings + history/compare.
- Voice: script + cast + waveform/timeline + playback.
- Analytics: question + evidence + prioritized action.
- Workspace: document canvas + semantic navigation.
- Dictation: voice presence + transcript + privacy state.
- Projects: work hierarchy + schedule/dependencies.
- Scheduling: availability + timezone + conflicts + confirmation.
- Support: conversation queue + dialogue + customer context.
- Recording: capture + recording state + preview/trim/share.
- Gaming: gameplay state + spatial readability + input feedback; see `epic.md`.

## 3D assets

Use `skills/image-to-3d`: one source object per generation, neutral reference, normalized scale/origin/grounding, mesh/material checks, and GLB plus preview export. No unreviewed automatic scene placement.

## Delivery gate

No UI is complete until the actual surface is exercised for primary workflow, loading, error/retry, success, keyboard/focus, reduced motion, and required breakpoints. Unexercised checks remain `unknown`.
