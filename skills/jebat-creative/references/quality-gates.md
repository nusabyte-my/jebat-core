# JEBAT Creative Quality Gates

All gates are mandatory for UI delivery. A gate not exercised is `unknown`, never `pass`.

## Anti-template

- No default hero → three features → CTA rhythm for unrelated products.
- No gradient/glass/orb/dots/terminal/pricing-tier default.
- No decorative numbered sections or generic uppercase eyebrow labels.
- No one-note dark/acid or cream/serif/terracotta theme without a brief-specific reason.
- No fake browser, phone, IDE, terminal, media-player, or recording chrome.
- No nine-reference visual collage.

## Product truth

- Main artifact and primary action visible and usable.
- Copy describes real behavior and user outcomes.
- Metrics include source/unit/range; demo/sample/synthetic states visibly labeled.
- Empty/loading/error/success states explain what happens next.
- Privacy, local/cloud processing, and irreversible actions clearly indicated where relevant.

## Craft

- Semantic tokens cover text, surfaces, borders, status, focus, and disabled states.
- Typography roles deliberate; headings roman; measurements use tabular numerals.
- Layout groups by task, not by arbitrary equal-sized cards.
- Motion has a causal purpose and reduced-motion fallback.
- No mid-render random color, font, radius, or spacing decisions.

## Interaction and accessibility

- Default, hover, focus-visible, active, disabled, loading, error, success implemented where applicable.
- Keyboard access, semantic controls, accessible names, visible focus, and focus restoration after overlays.
- Body text contrast ≥4.5:1; large text/UI indicators ≥3:1.
- Touch targets usable on mobile; no two-line clickable CTA/nav labels.
- `prefers-reduced-motion` respected; no autoplay audio or uncontrolled flashing.

## Verification

- Actual surface exercised, not only unit tests or source inspection.
- 320, 375, 414, 768px plus desktop: no horizontal scroll or clipped primary actions.
- Real state transitions tested: primary action, loading, failure, retry, success.
- Visual evidence reviewed at representative mobile and desktop widths.
- Existing project tests run where affected; report unverified items explicitly.

## Anti-slop research anchors

- Hallmark: structural variety, honest content, token discipline, responsive and interaction gates — https://github.com/Nutlope/hallmark
- Frontend-design: subject-led direction, one justified risk, restraint, task-specific copy.
- Open Higgsfield source: restrained studio palette, domain-specific structure, accessible metadata, purposeful motion.
- OpenWhispr source: spatially coherent pill-to-panel transitions and explicit privacy/recording states.
- AppFlowy-Web design system: primitive → semantic tokens and theme-aware components.
- Tubik 2026 trends: clarity with signature and motion that explains, not decoration — https://blog.tubikstudio.com/ui-design-trends-2026
