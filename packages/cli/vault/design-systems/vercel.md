# Design System: Vercel (Geist)
## Source: awesome-design-md — vercel/DESIGN.md

## 1. Visual Theme & Atmosphere
Near-pure white (`#ffffff`) canvas with `#171717` text. Minimalism as engineering principle. Geist font with aggressive negative letter-spacing. Shadow-as-border philosophy — no traditional CSS borders.

**Key Characteristics:**
- Geist Sans: -2.4px to -2.88px letter-spacing at display sizes
- Geist Mono for code/labels with OpenType `"liga"` globally
- Shadow-as-border: `box-shadow: 0px 0px 0px 1px rgba(0,0,0,0.08)`
- Multi-layer shadow stacks for depth
- Workflow accents: Ship Red (`#ff5b4f`), Preview Pink (`#de1d8d`), Develop Blue (`#0a72ef`)
- Pill badges (9999px) with tinted backgrounds

## 2. Color Palette
| Token | Hex | Role |
|-------|-----|------|
| Vercel Black | `#171717` | Primary text, headings |
| Pure White | `#ffffff` | Page background |
| Gray 600 | `#4d4d4d` | Secondary text |
| Gray 400 | `#808080` | Placeholder, disabled |
| Gray 100 | `#ebebeb` | Borders, dividers |
| Link Blue | `#0072f5` | Links |
| Focus Blue | `hsla(212, 100%, 48%, 1)` | Focus ring |
| Ship Red | `#ff5b4f` | Ship workflow |
| Preview Pink | `#de1d8d` | Preview workflow |
| Develop Blue | `#0a72ef` | Develop workflow |

## 3. Typography
- **Primary**: Geist, fallbacks: Arial, Apple Color Emoji, Segoe UI Emoji
- **Mono**: Geist Mono, fallbacks: ui-monospace, SFMono-Regular, Roboto Mono
- **OpenType**: `"liga"` enabled globally

| Role | Size | Weight | Line Height | Letter Spacing |
|------|------|--------|-------------|----------------|
| Display Hero | 48px | 600 | 1.00-1.17 | -2.4px to -2.88px |
| Section Heading | 40px | 600 | 1.20 | -2.4px |
| Card Title | 24px | 600 | 1.33 | -0.96px |
| Body | 16px | 400 | 1.50 | normal |
| Button | 14px | 500 | 1.43 | normal |
| Caption | 12px | 400-500 | 1.33 | normal |
| Mono Body | 16px | 400 | 1.50 | normal |

## 4. Components
**Buttons**: 6px radius, shadow-border `rgb(235,235,235) 0px 0px 0px 1px`, 8px 16px padding
**Cards**: 8px radius, shadow stack `rgba(0,0,0,0.08) 0px 0px 0px 1px, rgba(0,0,0,0.04) 0px 2px 2px, #fafafa 0px 0px 0px 1px`
**Pills**: 9999px radius, `#ebf5ff` bg, `#0068d6` text, 12px weight 500
**Border Radius Scale**: 2px (micro), 6px (buttons), 8px (cards), 12px (images), 9999px (pills)

## 5. Layout
- Base unit: 8px
- Max content width: ~1200px
- Section spacing: 80px-120px+
- Gallery emptiness philosophy

## 6. Agent Prompts
- "Create a hero section on white background. Headline at 48px Geist weight 600, line-height 1.00, letter-spacing -2.4px, color #171717."
- "Design a card: white background, shadow stack rgba(0,0,0,0.08) 0px 0px 0px 1px, rgba(0,0,0,0.04) 0px 2px 2px, #fafafa 0px 0px 0px 1px. Radius 8px."
- Always use shadow-as-border instead of CSS border.
- Three weights only: 400 (read), 500 (interact), 600 (announce).
