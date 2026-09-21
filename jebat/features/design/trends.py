"""Current (2025-2026) UI/UX design trends and conventions for JEBAT.

Documents modern, defensible design conventions with explicit adoption timelines,
anti-patterns to avoid, and verification checks.
"""

from __future__ import annotations
from typing import Any, Dict, List

TRENDS: List[Dict[str, Any]] = [
    {
        "id": "dark_mode_by_context",
        "name": "Contextual Dark Mode & System Preference",
        "surface": "web",
        "since": 2024,
        "convention": "Support `prefers-color-scheme` automatically via CSS media queries. Use semantic tokens (surface-primary, surface-muted, text-primary, border-subtle) rather than hardcoded hex values. Provide high-contrast dark surfaces with reduced saturation (e.g. zinc-900 #18181b) to prevent visual halation, and persist explicit user override via `data-theme` or a class toggle.",
        "avoid": "Pure #000000 pitch-black backgrounds for content areas (causes eye strain and contrast smear on OLED), inverted unadjusted brand saturation, or forcing dark mode without system preference detection.",
        "verify": "Verify `@media (prefers-color-scheme: dark)` is declared or semantic CSS variables adapt dynamically; ensure background luminance remains >= 0.05 (e.g. #18181b instead of #000000)."
    },
    {
        "id": "bento_grids",
        "name": "Bento Grid Layouts",
        "surface": "web",
        "since": 2024,
        "convention": "Use asymmetric CSS grid containers (`grid-cols-12` or `grid-cols-3`) with varying column and row spans (`col-span-1`, `col-span-2`, `row-span-2`), rounded card containers with subtle 1px borders, and authentic embedded micro-UI components (mini-buttons, interactive graphs, live toggles) instead of decorative marketing icons.",
        "avoid": "Symmetric 3x3 identical card grids, decorative generic icons in colored circles, or cards containing only text without concrete UI manifestation.",
        "verify": "Check for asymmetric `col-span-` or `row-span-` classes in grid containers and verify child cards contain real UI elements (buttons, inputs, charts)."
    },
    {
        "id": "variable_fonts",
        "name": "Variable Font & Fluid Typography",
        "surface": "web",
        "since": 2024,
        "convention": "Load a single variable font file supporting continuous optical sizing (`opsz`), weight ranges (`wght` 100-900), and fluid typography with CSS `clamp(min, preferred, max)` to eliminate abrupt breakpoint jumps.",
        "avoid": "Loading 6+ separate static `.woff2` font files for each weight/style combination, or using fixed `px` font sizes on mobile viewports that cause overflow or awkward wrapping.",
        "verify": "Confirm `@font-face` loads variable font format (`format('woff2-variations')` or single woff2) and headings use `clamp()` for responsive font sizing."
    },
    {
        "id": "motion_discipline",
        "name": "Motion Discipline & Prefers-Reduced-Motion",
        "surface": "web",
        "since": 2024,
        "convention": "Keep transition durations between 150ms and 300ms with natural easing curves (`cubic-bezier(0.16, 1, 0.3, 1)`). Wrap all decorative transforms, parallax, and transitions in `@media (prefers-reduced-motion: reduce)` to disable motion for sensitive users.",
        "avoid": "Infinite looping background animations, bouncy playful spring physics in professional tooling, or transitions exceeding 400ms that delay user input.",
        "verify": "Check CSS for `@media (prefers-reduced-motion: reduce)` rules that set `animation-duration: 0.01ms` or `transition: none`."
    },
    {
        "id": "ui_density_adaptation",
        "name": "Contextual UI Density: Expert Density vs Mobile Focus",
        "surface": "web",
        "since": 2025,
        "convention": "Apply high information density (compact 32-36px rows, tight 4-8px spacing, monospaced tabular numbers) for desktop operational and data tools. Switch to high-focus, thumb-friendly density (48-56px rows, 16px padding) on touch surfaces.",
        "avoid": "Sprawling consumer whitespace in enterprise/financial dashboards, or cramped desktop tables rendered without horizontal overflow management on mobile.",
        "verify": "Inspect component padding and row heights across breakpoints: desktop table row height <= 40px, mobile touch targets >= 44px."
    },
    {
        "id": "ai_native_interaction",
        "name": "AI-Era Native Patterns: Streaming & Optimistic UI",
        "surface": "web",
        "since": 2025,
        "convention": "Provide immediate visible feedback on user prompt submission (optimistic UI), stream responses with cursor indicators, render interactive generative UI widgets instead of raw markdown, and provide discrete stop/edit/retry controls.",
        "avoid": "Blocking spinner screens while waiting for full LLM completion, unformatted wall-of-text responses, or non-cancellable streaming requests.",
        "verify": "Check for streaming cursor states, cancel/abort buttons during generation, and structured interactive fallback blocks."
    },
    {
        "id": "accessibility_as_default",
        "name": "Accessibility as Default (WCAG 2.2 / EN 301 549)",
        "surface": "web",
        "since": 2025,
        "convention": "Ensure all interactive elements meet WCAG 2.2 AA standards ahead of the European Accessibility Act (EAA) June 2025 enforcement deadline: minimum 44×44px tap target (2.5.8), 4.5:1 body text contrast (1.4.3), visible focus rings with at least 3:1 contrast against adjacent colors (2.4.11), and full keyboard tab navigation.",
        "avoid": "Removing focus rings (`outline: none` without replacement), relying on color alone to indicate status, or missing `aria-label` on icon-only buttons.",
        "verify": "Verify `focus-visible:` focus indicator styles are present, image `alt` attributes exist, and contrast ratio meets 4.5:1."
    },
    {
        "id": "form_factor_paradigms",
        "name": "Form-Factor Paradigm Specialization",
        "surface": "web",
        "since": 2025,
        "convention": "Design distinct interaction models per form factor: desktop supports persistent multi-column sidebars, keyboard shortcuts, and hover states; mobile relies on bottom navigation, swipe sheets, and thumb-zone actions.",
        "avoid": "Shrinking desktop layouts proportionally to fit mobile screens, relying on hover-only disclosures on touch devices, or hiding primary actions behind multi-level hamburger menus.",
        "verify": "Check responsive markup: desktop uses sidebar/shortcuts (`hidden md:flex`), mobile uses bottom bar or sheet (`flex md:hidden`), no hover-dependent functionality."
    }
]
