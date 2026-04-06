# Design System: Cursor (Warm Minimalism)
## Source: awesome-design-md — cursor/DESIGN.md

## 1. Visual Theme & Atmosphere
Warm off-white (`#f2f1ed`) with warm brown text (`#26251e`). Craft publication feel, not tech website. Three-font system: CursorGothic display, jjannon serif body, berkeleyMono code.

**Key Characteristics:**
- CursorGothic: -2.16px letter-spacing at 72px display
- jjannon serif with OpenType `"cswh"` contextual swashes
- berkeleyMono for code/technical labels
- Warm off-white `#f2f1ed` background (not pure white)
- oklab-space borders for perceptually uniform warmth browns
- Accent orange `#f54e00` for brand/links
- Pill shapes: 33.5M px radius (effectively full-pill)
- AI Timeline: Thinking (peach), Grep (sage), Read (blue), Edit (lavender)

## 2. Color Palette
| Token | Hex | Role |
|-------|-----|------|
| Cursor Dark | `#26251e` | Primary text (warm near-black) |
| Cursor Cream | `#f2f1ed` | Page background |
| Cursor Light | `#e6e5e0` | Card backgrounds |
| Surface 100 | `#f7f7f4` | Lightest surface |
| Surface 400 | `#e6e5e0` | Secondary surface |
| Cursor Orange | `#f54e00` | Brand accent, CTA |
| Gold | `#c08532` | Secondary accent |
| Error | `#cf2d56` | Warm crimson |
| Success | `#1f8a65` | Muted teal |
| Thinking | `#dfa88f` | AI timeline peach |
| Grep | `#9fc9a2` | AI timeline sage |
| Read | `#9fbbe0` | AI timeline blue |
| Edit | `#c0a8dd` | AI timeline lavender |
| Border Primary | `oklab(0.263 / 0.1)` | Warm brown border |

## 3. Typography
- **Display**: CursorGothic, fallbacks: system-ui, Helvetica Neue
- **Body**: jjannon, fallbacks: Iowan Old Style, Palatino, Georgia
- **Code**: berkeleyMono, fallbacks: SFMono-Regular, Menlo, Consolas
- **OpenType**: `"cswh"` on jjannon, `"ss09"` on CursorGothic buttons

| Role | Font | Size | Weight | Line Height | Letter Spacing |
|------|------|------|--------|-------------|----------------|
| Display Hero | CursorGothic | 72px | 400 | 1.10 | -2.16px |
| Section Heading | CursorGothic | 36px | 400 | 1.20 | -0.72px |
| Sub-heading | CursorGothic | 26px | 400 | 1.25 | -0.325px |
| Body Serif | jjannon | 19.2px | 500 | 1.50 | normal |
| Body Sans | CursorGothic | 16px | 400 | 1.50 | normal |
| Button | CursorGothic | 14px | 400 | 1.00 | normal |
| Mono Body | berkeleyMono | 12px | 400 | 1.67 | normal |

## 4. Components
**Buttons**: 8px radius, `#ebeae5` bg, hover text shift to `#cf2d56`
**Cards**: 8px radius, oklab border `1px solid oklab(0.263 / 0.1)`, large blur shadows (28px, 70px)
**Pills**: full-pill radius (9999px), `#e6e5e0` bg, `oklab(0.263 / 0.6)` text
**Border Radius**: 4px (compact), 8px (standard), 10px (featured), 9999px (pills)

## 5. Layout
- Base unit: 8px, fine scale: 1.5px-6px sub-8px increments
- Max content width: ~1200px
- Warm negative space philosophy
- Alternating surface tones for section differentiation

## 6. Agent Prompts
- "Create a hero section on #f2f1ed warm cream. Headline at 72px CursorGothic weight 400, line-height 1.10, letter-spacing -2.16px, color #26251e. Subtitle at 17.28px jjannon weight 400."
- "Design a card: #e6e5e0 background, border 1px solid rgba(38,37,30,0.1). Radius 8px. Title at 22px CursorGothic weight 400."
- Always use warm tones — never pure white/black for primary surfaces.
- Hover states use `#cf2d56` text color — the warm crimson shift is signature.
