# Design System: Supabase (Dark-Mode-Native)
## Source: awesome-design-md — supabase/DESIGN.md

## 1. Visual Theme & Atmosphere
Dark-mode-native (`#0f0f0f`, `#171717`) with emerald green accents (`#3ecf8e`). Terminal-born sophistication. Circular geometric sans with rounded terminals. HSL-based color tokens with alpha channels for translucent layering.

**Key Characteristics:**
- Circular font: geometric sans-serif with rounded terminals
- Source Code Pro for uppercase technical labels (1.2px letter-spacing)
- Emerald green brand accent used sparingly as identity marker
- HSL color tokens with alpha channels for translucency
- Pill buttons (9999px) for primary CTAs, 6px for secondary
- Almost no shadows — depth through border contrast
- Radix color primitives (crimson, purple, violet, indigo)
- Hero text: 72px, line-height 1.00 — zero-leading terminal density

## 2. Color Palette
| Token | Hex | Role |
|-------|-----|------|
| Near Black | `#0f0f0f` | Button bg, deepest surface |
| Dark | `#171717` | Page background |
| Dark Border | `#2e2e2e` | Card borders |
| Mid Border | `#363636` | Button borders |
| Light Border | `#393939` | Secondary borders |
| Mid Gray | `#898989` | Muted text |
| Off White | `#fafafa` | Primary text |
| Supabase Green | `#3ecf8e` | Brand, logo |
| Green Link | `#00c573` | Interactive links |
| Green Border | `rgba(62, 207, 142, 0.3)` | Accent border |
| Violet | `hsl(251, 63.2%, 63.2%)` | Accent |
| Tomato | `--colors-tomatoA4` | Error |

## 3. Typography
- **Primary**: Circular, fallbacks: Helvetica Neue, Helvetica, Arial
- **Monospace**: Source Code Pro, fallbacks: Office Code Pro, Menlo

| Role | Size | Weight | Line Height | Letter Spacing |
|------|------|--------|-------------|----------------|
| Display Hero | 72px | 400 | 1.00 | normal |
| Section Heading | 36px | 400 | 1.25 | normal |
| Card Title | 24px | 400 | 1.33 | -0.16px |
| Body | 16px | 400 | 1.50 | normal |
| Button | 14px | 500 | 1.14 | normal |
| Code Label | 12px | 400 | 1.33 | 1.2px (uppercase) |

## 4. Components
**Buttons**: 9999px radius (pill), `#0f0f0f` bg, `#fafafa` text, 8px 32px padding
**Cards**: 8-16px radius, `#171717` bg, border `1px solid #2e2e2e`
**Tabs**: 9999px radius (pill tabs), border `1px solid #2e2e2e`
**Border Radius Scale**: 6px (ghost buttons), 8px (cards), 16px (feature cards), 9999px (pills)

## 5. Layout
- Base unit: 8px
- Section spacing: 90px-128px (dramatic cinematic pacing)
- Content blocks: 16px-24px (dense clusters)
- Border-defined space instead of whitespace separation
- Breakpoints: Mobile (<600px), Desktop (>600px)

## 6. Agent Prompts
- "Create a hero on #171717. Headline at 72px Circular weight 400, line-height 1.00, #fafafa text. Pill CTA (#0f0f0f bg, #fafafa text, 9999px radius, 8px 32px padding)."
- "Design a feature card: #171717 bg, 1px solid #2e2e2e border, 16px radius. Title at 24px Circular weight 400, letter-spacing -0.16px."
- Green is the brand identity marker — use sparingly for links, logo, accent borders only.
- Depth comes from borders (#242424 → #2e2e2e → #363636), not shadows.
- Weight 400 is default for everything — 500 only for interactive elements.
