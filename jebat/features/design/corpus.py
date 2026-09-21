"""Curated UI/UX pattern corpus for JEBAT (Pawang Estetika).

Defines real-world, defensible design patterns organized by screen type and component intent.
All metrics are grounded in established standards:
- Apple Human Interface Guidelines (HIG): 44×44pt minimum touch target
- Android Material Design 3: 48×48dp minimum touch target, 56dp bottom bar
- WCAG 2.2 AA (Criterion 1.4.3): 4.5:1 text contrast ratio, 3.0:1 large text
- WCAG 2.2 AA (Criterion 1.4.11): 3.0:1 non-text contrast ratio
- WCAG 2.2 AA (Criterion 2.5.8): 24×24 CSS px target size with spacing
- WCAG 2.2 AA (Criterion 3.3.1): Error Identification
- Bringhurst / Web Style Guide: 45–75 characters per line for body copy
- 8pt Spatial Grid: 8px increments (4, 8, 16, 24, 32, 48, 64)
- Miller's Law: 7 ± 2 items in working memory
- Doherty Threshold / Nielsen Norman Group: 100ms perceived instant, 100-300ms transitions
- Steven Hoober Thumb Zone: bottom 35% screen area for one-handed reach
"""

from __future__ import annotations
from typing import Any, Dict, List

PATTERNS: Dict[str, List[Dict[str, Any]]] = {
    "hero": [
        {
            "name": "Split-Screen Value Proposition",
            "structure": "Desktop 12-column grid: left 7 columns contain category badge, H1 headline (max 10 words), supporting subhead (max 3 lines), primary CTA button, secondary link, and social proof avatars. Right 5 columns contain an authentic interactive product viewport or live code frame. Stacks vertically on mobile with text preceding media.",
            "why": "Enables rapid visual scanning by pairing immediate value statement with visual proof of capability above the fold, satisfying Nielsen's Visibility of System Status.",
            "anti_patterns": "Replaced real product screenshot with generic 3D abstract shapes, floating geometric glass spheres, or simulated macOS window chrome with red/yellow/green dots.",
            "metrics": {
                "max_heading_words": 10,
                "max_subhead_lines": 3,
                "min_cta_height_px": 44,
                "optimal_line_length_chars": "45-75",
                "grid_base_px": 8,
                "standard": "Apple HIG 44pt touch target; Bringhurst line length; 8pt spatial grid"
            },
            "use_when": "B2B SaaS or developer tools where demonstrating real interface capability builds immediate trust."
        },
        {
            "name": "Centered Single-Focus Hero",
            "structure": "Single-column centered layout: top pill badge announcing release, centered H1 headline (max 8 words), centered subhead (max 2 lines, max-width 640px), dual CTAs in a horizontal flex row with 16px gap, leading into an oversized centered product canvas below with 32px top margin.",
            "why": "Focuses user attention strictly on a single clear proposition and conversion path, eliminating distraction per Hick's Law.",
            "anti_patterns": "Everything centered down the entire page without layout alternation, center-aligned body paragraphs longer than 3 lines, or missing CTA contrast.",
            "metrics": {
                "max_heading_words": 8,
                "max_subhead_width_px": 640,
                "min_cta_height_px": 44,
                "cta_gap_px": 16,
                "perceived_instant_ms": 100,
                "standard": "Apple HIG 44pt touch target; NN/g 100ms response threshold; Hick's Law"
            },
            "use_when": "Consumer products, single-feature utilities, or mobile-first applications with one dominant conversion action."
        },
        {
            "name": "Proof-Led Outcome Hero",
            "structure": "Headline highlighting a verified quantitative outcome, followed by customer avatar cluster with verified review count, primary trial CTA, and an interactive before/after or ROI preview module in the primary viewport.",
            "why": "Anchors the purchasing decision on proven outcomes and social validation, overcoming initial user skepticism.",
            "anti_patterns": "Fabricated customer review statistics ('99.9% loved by everyone'), unqualified '10x faster' claims without benchmark data, or stock photo headshots.",
            "metrics": {
                "min_touch_target_px": 44,
                "avatar_size_px": 32,
                "contrast_ratio_body": "4.5:1",
                "contrast_ratio_large": "3.0:1",
                "standard": "Apple HIG 44pt touch target; WCAG 2.2 AA Criterion 1.4.3"
            },
            "use_when": "Direct-response landing pages and enterprise solutions where proof and social evidence drive qualification."
        },
        {
            "name": "Terminal / Code-First Developer Hero",
            "structure": "Left column: H1 headline, 1-sentence value description, copyable package manager command box (e.g. npm install / pip install) with 1-click copy button and feedback state. Right column: interactive syntax-highlighted code editor or terminal showing actual working API calls.",
            "why": "Developers evaluate tools by code ergonomics and time-to-first-run; showing real syntax delivers instant credibility.",
            "anti_patterns": "Fake code snippets that don't compile, code blocks without copy functionality, or non-monospace fonts in code displays.",
            "metrics": {
                "min_touch_target_px": 44,
                "code_font_size_px": 14,
                "line_height_ratio": 1.5,
                "copy_feedback_duration_ms": 2000,
                "standard": "Apple HIG 44pt; WCAG 2.5.8 Target Size; NN/g feedback duration"
            },
            "use_when": "Developer tools, open-source libraries, APIs, and CLI utilities."
        }
    ],
    "landing": [
        {
            "name": "Narrative Long-Scroll Section Cadence",
            "structure": "Sequential full-width sections alternating background surfaces (e.g. white -> zinc-50 -> white -> zinc-900). Order: 1. Hero, 2. Problem Statement, 3. Solution Workflow, 4. Feature Grid, 5. Proof / Testimonials, 6. Pricing, 7. FAQ Accordion, 8. Final CTA. Each section has 64px vertical padding.",
            "why": "Guides the visitor through a natural psychological narrative from problem recognition to solution evaluation and purchase decision.",
            "anti_patterns": "Monolithic single-color background throughout the entire page with no visual rest, or unstructured random ordering of sections.",
            "metrics": {
                "section_padding_y_px": 64,
                "grid_base_px": 8,
                "max_body_width_ch": 65,
                "contrast_ratio_body": "4.5:1",
                "standard": "8pt spatial grid; Bringhurst line length; WCAG 2.2 AA Criterion 1.4.3"
            },
            "use_when": "Primary marketing homepages and high-intent product landing pages."
        },
        {
            "name": "Bento Feature Grid",
            "structure": "Asymmetric 12-column responsive grid with 1 primary card spanning 8 columns, 2 secondary cards spanning 4 columns, and lower row with 3 equal 4-column cards. Each card features rounded-2xl corners, 1px subtle border, and embedded functional micro-UI (not decorative icons).",
            "why": "Breaks visual monotony by establishing natural focal hierarchy while showing multiple product capabilities in dense, graspable cards.",
            "anti_patterns": "Symmetric 3x3 grid of identical cards, cards containing only generic stock icons in colored circles, or cards with no internal layout structure.",
            "metrics": {
                "card_gap_px": 24,
                "card_padding_px": 24,
                "border_radius_px": 16,
                "grid_base_px": 8,
                "standard": "8pt spatial grid convention; Gestalt proximity principle"
            },
            "use_when": "Feature highlight sections showcasing a suite of capabilities or multi-faceted product updates."
        },
        {
            "name": "Sticky Anchor Navigation Landing",
            "structure": "Fixed or sticky secondary header below main navigation (48px height) displaying section anchor links ('Overview', 'Architecture', 'Security', 'Pricing'). Active section is highlighted via scrollspy with a bottom border pill. Includes a compact primary CTA.",
            "why": "Provides direct random access to long-form landing page sections, reducing cognitive load and scroll fatigue for research-oriented buyers.",
            "anti_patterns": "Sticky header obscuring section titles on jump due to missing scroll-margin-top, or unresponsive anchor links on mobile viewports.",
            "metrics": {
                "nav_height_px": 48,
                "min_tap_target_px": 44,
                "scroll_offset_px": 64,
                "standard": "Apple HIG 44pt; Material Design 48dp touch target"
            },
            "use_when": "Technical product overviews, multi-section product launches, and documentation-style landing pages."
        },
        {
            "name": "Comparison / Teardown Matrix",
            "structure": "Sticky table header listing competitors or legacy approaches vs this product. Left column: capability categories and features. Right columns: checkmarks, crossmarks, and quantitative metrics with accessible text labels. Bottom row: tier pricing and CTA.",
            "why": "Simplifies complex evaluation by positioning direct feature and capability differences side-by-side in a transparent matrix.",
            "anti_patterns": "Using color alone (green/red) without icons or text labels to indicate support, or biased strawman competitor comparisons.",
            "metrics": {
                "row_height_px": 48,
                "non_text_contrast": "3.0:1",
                "min_touch_target_px": 44,
                "standard": "WCAG 2.2 AA Criterion 1.4.11; WCAG 1.4.1 (Use of Color); Apple HIG 44pt"
            },
            "use_when": "Competitive alternative landing pages ('vs' pages) and migration campaign pages."
        }
    ],
    "pricing": [
        {
            "name": "Three-Tiered SaaS Card Matrix",
            "structure": "3-column grid on desktop, single column on mobile. Tiers: Starter, Professional (visually elevated with 1.03 scale or distinctive border and 'Most Popular' badge), Enterprise. Top: monthly/annual billing toggle with savings callout. Card body: price, billing cadence, CTA button, and feature checklist.",
            "why": "Leverages the compromise effect and Miller's Law (chunking) to guide the majority of buyers toward the optimal mid-tier plan.",
            "anti_patterns": "More than 4 tiers shown simultaneously, hidden pricing cadences, or unclear CTA distinctions between self-serve and sales-assisted tiers.",
            "metrics": {
                "tier_count": 3,
                "min_cta_height_px": 44,
                "highlight_scale": 1.03,
                "contrast_ratio_body": "4.5:1",
                "standard": "Miller's Law (7±2 chunking); Apple HIG 44pt; WCAG 2.2 AA Criterion 1.4.3"
            },
            "use_when": "Standard SaaS products with self-serve signup and differentiated usage limits."
        },
        {
            "name": "Usage-Based Slider Calculator",
            "structure": "Interactive range slider allowing users to adjust expected volume (e.g. monthly active users, API requests, seats). Dynamic readout displays computed total monthly price, cost per unit, and tier threshold transitions in real time.",
            "why": "Removes pricing ambiguity for usage-based products by allowing prospects to estimate their exact bill before commitment.",
            "anti_patterns": "Slider thumb too small for touch interaction, sluggish non-debounced price calculation, or absence of numerical input fallback for accessibility.",
            "metrics": {
                "slider_thumb_min_px": 44,
                "update_debounce_ms": 16,
                "contrast_ratio_large": "3.0:1",
                "standard": "Apple HIG 44pt; 60fps frame budget (16.6ms); WCAG 2.2 AA Criterion 1.4.3"
            },
            "use_when": "Consumption-based pricing models, API platforms, cloud infrastructure, and email delivery services."
        },
        {
            "name": "Single Plan with Add-Ons",
            "structure": "One prominent base plan card detailing core platform access, accompanied by a clean list of optional modular add-on cards with individual toggles/checkboxes and price adjustments that update a sticky summary drawer.",
            "why": "Minimizes choice overload per Hick's Law while supporting diverse customer requirements through modularity.",
            "anti_patterns": "Unclear whether add-ons are recurring or one-time, or hidden base platform prerequisites.",
            "metrics": {
                "checkbox_touch_target_px": 44,
                "row_gap_px": 12,
                "contrast_ratio_body": "4.5:1",
                "standard": "Apple HIG 44pt; WCAG 2.2 AA Criterion 1.4.3; Hick's Law"
            },
            "use_when": "Specialized B2B software where the core product is universal but specific extensions (e.g. SSO, audit logs) vary by customer maturity."
        },
        {
            "name": "Feature Comparison Table",
            "structure": "Comprehensive table grouped by capability headers (e.g. 'Security', 'Collaboration', 'Analytics'). Left column: feature description with info tooltip. Columns 2-4: tier capabilities with text or checkmark. Column headers remain sticky while scrolling.",
            "why": "Supports rigorous procurement and technical evaluation by providing exhaustive capability breakdown without cluttering top-level cards.",
            "anti_patterns": "Non-sticky table headers that lose context on long tables, or tooltips that disappear on hover before being readable.",
            "metrics": {
                "min_row_height_px": 44,
                "tooltip_delay_ms": 200,
                "non_text_contrast": "3.0:1",
                "standard": "Apple HIG 44pt; NN/g tooltip timing; WCAG 2.2 AA Criterion 1.4.11"
            },
            "use_when": "Enterprise software evaluation, multi-product tiers, and detailed technical feature grids."
        }
    ],
    "dashboard": [
        {
            "name": "Executive KPI Metric Grid",
            "structure": "Top 4-column responsive grid of summary cards. Each card displays: muted uppercase metric label (12px), prominent numerical value (28-32px font-semibold), directional trend pill with percentage delta and icon, and compact sparkline.",
            "why": "Provides immediate high-level situation awareness at a glance, adhering to Nielsen's Visibility of System Status.",
            "anti_patterns": "More than 5 KPI cards in a single row causing cognitive overload, missing baseline context for percentages, or color-only trend indications.",
            "metrics": {
                "kpi_count_max": 4,
                "trend_icon_contrast": "3.0:1",
                "number_font_weight": 600,
                "grid_gap_px": 16,
                "standard": "Miller's Law (7±2); WCAG 2.2 AA Criterion 1.4.11; 8pt spatial grid"
            },
            "use_when": "Analytics dashboards, operational control panels, and executive summary overviews."
        },
        {
            "name": "Master-Detail Data Explorer",
            "structure": "Split-pane layout: left 35% contains a filterable, searchable list of entities with status badges. Right 65% contains the detail pane showing selected entity metadata, action toolbar (Edit, Export, Delete), and tabbed activity logs.",
            "why": "Enables rapid triage and inspection without navigating away from the broader dataset context.",
            "anti_patterns": "Forgetting keyboard arrow navigation between list items, or unhandled empty states when no list item is selected.",
            "metrics": {
                "list_item_min_height_px": 48,
                "search_debounce_ms": 300,
                "min_tap_target_px": 44,
                "standard": "Material Design 48dp list item; Apple HIG 44pt; NN/g search latency"
            },
            "use_when": "Customer support desks, CRM contact managers, code review tools, and inbox-style interfaces."
        },
        {
            "name": "Interactive Time-Series Panel",
            "structure": "Full-width chart container with top controls: time range pills ('24h', '7d', '30d', '1y'), metric selector dropdown, and export button. Below: SVG/Canvas area or line chart with interactive crosshair tooltip and toggleable legend.",
            "why": "Allows domain experts to correlate temporal events and identify trends across variable time horizons.",
            "anti_patterns": "Charts without accessible tabular data alternatives, unreadable overlapping axis labels, or missing hover tooltip coordinates.",
            "metrics": {
                "tooltip_activation_ms": 50,
                "legend_tap_target_px": 44,
                "chart_aspect_ratio": "16:9",
                "standard": "Apple HIG 44pt; NN/g response time thresholds; WCAG 2.2 AA"
            },
            "use_when": "Financial monitoring, server performance metrics, and telemetry data visualization."
        },
        {
            "name": "Operational Activity Stream",
            "structure": "Vertical reverse-chronological list of system events. Each entry includes: actor avatar or system category icon (32px), actor name, event description with highlighted entity link, relative timestamp (e.g. '12m ago'), and optional metadata badge.",
            "why": "Maintains an immutable audit trail and communicates ongoing system activity in multi-user collaborative environments.",
            "anti_patterns": "Unbounded lists without pagination or virtualization, absolute timestamps without timezone clarity, or generic icon usage for all events.",
            "metrics": {
                "timestamp_update_interval_s": 60,
                "min_chip_height_px": 32,
                "chip_touch_target_px": 44,
                "standard": "Apple HIG 44pt touch target; WCAG 2.2 AA Criterion 2.5.8"
            },
            "use_when": "Audit logs, team collaboration feeds, deployment histories, and security alert monitors."
        }
    ],
    "data_display": [
        {
            "name": "Sortable Paginated Data Table",
            "structure": "Table with sticky header row, interactive column sort arrows, row hover highlight, multi-select checkboxes on left, inline action icons on right, and bottom pagination bar with rows-per-page selector and total count.",
            "why": "Standardized pattern for structured data exploration, sorting, and batch operational workflows.",
            "anti_patterns": "Horizontal table overflow on mobile viewports without container scrolling, missing sort direction indicators, or non-keyboard-accessible row selection.",
            "metrics": {
                "row_height_compact_px": 36,
                "row_height_comfortable_px": 48,
                "checkbox_target_px": 44,
                "default_page_size": 25,
                "standard": "Material Design 48dp; Apple HIG 44pt; WCAG 2.2 AA Criterion 2.5.8"
            },
            "use_when": "Data-dense enterprise lists, inventory management, user rosters, and transaction histories."
        },
        {
            "name": "Multi-View Toggle Display",
            "structure": "Top toolbar with search input, filter chips, and segmented view toggle (Table / Grid / Kanban / List). Selecting a view preserves filter and sort state while re-rendering data in the chosen structural paradigm.",
            "why": "Accommodates diverse user tasks—such as bulk data editing in tables versus visual status management in boards.",
            "anti_patterns": "Resetting filter or pagination state when toggling views, or inconsistent item representations between views.",
            "metrics": {
                "switcher_button_min_px": 44,
                "transition_duration_ms": 150,
                "grid_columns_desktop": 3,
                "standard": "Apple HIG 44pt; NN/g 100-200ms transition threshold"
            },
            "use_when": "Project management tools, digital asset managers, and e-commerce product catalogs."
        },
        {
            "name": "Key-Value Definition List",
            "structure": "Two-column vertical stack or horizontal pair: left column displays muted uppercase attribute label (12px, font-medium), right column displays value with high-contrast text, accompanied by an optional 1-click copy button.",
            "why": "Formats unstructured or semi-structured metadata into predictable, scannable pairs for verification and audit.",
            "anti_patterns": "Low-contrast gray text on light gray background for values, or inconsistent horizontal alignment between labels and values.",
            "metrics": {
                "label_contrast_ratio": "4.5:1",
                "value_contrast_ratio": "4.5:1",
                "inline_action_target_px": 44,
                "standard": "WCAG 2.2 AA Criterion 1.4.3; Apple HIG 44pt touch target"
            },
            "use_when": "Entity details panels, order confirmation summaries, and server configuration sheets."
        },
        {
            "name": "Status Badge & Indicator Set",
            "structure": "Inline pill badge containing a circular dot indicator (8px) and a capitalized text label. Semantic color tokens: neutral (gray), info (blue), success (green), warning (amber), error (red). Always pairs color with text.",
            "why": "Communicates operational lifecycle status quickly while strictly adhering to WCAG 1.4.1 (not relying on color alone).",
            "anti_patterns": "Color-only circles without text labels, unreadable white text on bright yellow backgrounds, or inconsistent status vocabulary.",
            "metrics": {
                "dot_size_px": 8,
                "badge_padding_x_px": 8,
                "non_text_contrast": "3.0:1",
                "text_contrast": "4.5:1",
                "standard": "WCAG 2.2 AA Criterion 1.4.1 (Use of Color); Criterion 1.4.11; Criterion 1.4.3"
            },
            "use_when": "Displaying state across tables, cards, order summaries, and deployment monitors."
        }
    ],
    "auth": [
        {
            "name": "Single-Field Progressive Auth",
            "structure": "Clean card container: email input field with autofocus, primary 'Continue' CTA, and OAuth provider buttons below. System checks email domain to determine whether to prompt for password, trigger SSO redirect, or send magic link.",
            "why": "Reduces upfront cognitive friction and supports corporate SSO routing seamlessly without confusing consumers.",
            "anti_patterns": "Asking for both password and SSO options simultaneously without routing, or failing to preserve entered email on step transition.",
            "metrics": {
                "input_min_height_px": 44,
                "optimal_label_length_chars": "10-25",
                "contrast_ratio_body": "4.5:1",
                "standard": "Apple HIG 44pt; WCAG 2.2 AA Criterion 1.4.3"
            },
            "use_when": "Modern SaaS applications supporting both individual users and enterprise SSO."
        },
        {
            "name": "Social + Credential Split Auth",
            "structure": "Top section: primary OAuth buttons (Google, GitHub, Apple) spanning full width with brand icons. Subtle horizontal divider with 'Or continue with email'. Bottom section: email and password inputs, 'Forgot password?' link, and submit button.",
            "why": "Presents fastest 1-click authentication paths first per Hick's Law, while retaining universal credential fallback.",
            "anti_patterns": "Showing more than 3 OAuth buttons, cluttering with obsolete social providers, or hiding the password reset link.",
            "metrics": {
                "oauth_button_height_px": 44,
                "divider_margin_y_px": 24,
                "oauth_provider_max": 3,
                "standard": "Hick's Law; Apple HIG 44pt; 8pt spatial grid"
            },
            "use_when": "Standard consumer and developer authentication screens."
        },
        {
            "name": "Multi-Factor Verification Challenge",
            "structure": "Centered modal card: instruction text specifying where the code was sent, 6 separate numeric input boxes with auto-advance and backspace regression, paste handler accepting full code, and a 60-second countdown for 'Resend code'.",
            "why": "Streamlines two-factor verification by guiding input character-by-character and supporting seamless clipboard pasting.",
            "anti_patterns": "Blocking clipboard paste of 6-digit codes, missing automatic focus progression, or no cooldown timer on resend requests.",
            "metrics": {
                "otp_box_size_px": 48,
                "otp_digit_count": 6,
                "resend_cooldown_s": 60,
                "min_tap_target_px": 44,
                "standard": "Material Design 48dp; Apple HIG 44pt touch target"
            },
            "use_when": "Two-factor authentication (2FA), SMS/email verification, and sensitive action confirmation."
        },
        {
            "name": "Passkey / WebAuthn Biometric Prompt",
            "structure": "Prominent primary button: 'Sign in with Passkey' with biometric fingerprint/face icon. Secondary text: 'Fast, secure login without passwords'. Fallback text link below: 'Sign in with password instead'.",
            "why": "Promotes modern phishing-resistant FIDO2 authentication while providing accessible recovery paths.",
            "anti_patterns": "Hiding passkey option beneath legacy password fields, or trapping users when biometric hardware is unavailable.",
            "metrics": {
                "primary_button_height_px": 48,
                "min_tap_target_px": 44,
                "contrast_ratio_body": "4.5:1",
                "standard": "Material Design 48dp; Apple HIG 44pt; WCAG 2.2 AA Criterion 1.4.3"
            },
            "use_when": "Modern web applications implementing WebAuthn / Passkeys authentication."
        }
    ],
    "signup": [
        {
            "name": "Frictionless 2-Step Signup",
            "structure": "Step 1: work email and password with inline real-time strength validation. Step 2: user full name, organization title, and role selector. Clear progress indicator (Step 1 of 2). No credit card required upfront.",
            "why": "Minimizes initial conversion abandonment by postponing secondary profile configuration until account commitment is made.",
            "anti_patterns": "Requesting credit card details for a free trial, asking for phone numbers without clear necessity, or multi-page forms with unannounced length.",
            "metrics": {
                "max_fields_step_1": 2,
                "input_min_height_px": 44,
                "contrast_ratio_body": "4.5:1",
                "standard": "Fitts's Law; Apple HIG 44pt; WCAG 2.2 AA Criterion 1.4.3"
            },
            "use_when": "Self-serve SaaS and product-led growth onboarding."
        },
        {
            "name": "Product-Led Live Preview Signup",
            "structure": "Split screen: left 50% contains minimal signup form (Email, Password, Create Account). Right 50% displays an interactive preview of the user's future workspace dynamically updating with their typed organization name.",
            "why": "Builds anticipatory excitement and concrete mental ownership of the product before the user even finishes registration.",
            "anti_patterns": "Static stock illustration on the right instead of authentic product interface, or sluggish input synchronization.",
            "metrics": {
                "input_min_height_px": 44,
                "grid_gap_px": 32,
                "contrast_ratio_large": "3.0:1",
                "standard": "Apple HIG 44pt; 8pt spatial grid; WCAG 2.2 AA Criterion 1.4.3"
            },
            "use_when": "Workspace collaboration tools, design platforms, and website builders."
        },
        {
            "name": "Team Invitation Acceptance Flow",
            "structure": "Dedicated view displaying inviter avatar and name: '[Name] invited you to join [Team] on [Product]'. Pre-filled invited email address, single password creation field, and high-contrast 'Join Team' button.",
            "why": "Eliminates redundant data entry for invited users and establishes immediate context and trust.",
            "anti_patterns": "Treating invited users like cold signups and forcing them through standard marketing questions.",
            "metrics": {
                "button_min_height_px": 44,
                "avatar_size_px": 40,
                "contrast_ratio_body": "4.5:1",
                "standard": "Apple HIG 44pt; WCAG 2.2 AA Criterion 1.4.3"
            },
            "use_when": "Collaborative SaaS team expansion and invitation links."
        },
        {
            "name": "Self-Serve Free Trial Activation",
            "structure": "Top badge: '14-day full-access trial — no card required'. Clear 3-item checklist of what's included. Single work email input and primary CTA button: 'Start Building Today'. Terms and privacy policy links in subtle 13px text.",
            "why": "Reassures prospective users against unexpected charges and maximizes signup velocity.",
            "anti_patterns": "Vague trial duration, hidden automatic conversion to paid status, or confusing trial limits.",
            "metrics": {
                "cta_min_height_px": 48,
                "terms_font_size_px": 13,
                "contrast_ratio_body": "4.5:1",
                "standard": "Material Design 48dp; WCAG 2.2 AA Criterion 1.4.3"
            },
            "use_when": "B2B SaaS free trial acquisition funnels."
        }
    ],
    "onboarding": [
        {
            "name": "Checklist Getting-Started Widget",
            "structure": "Persistent collapsible card in bottom-right corner or dashboard top. Features: circular progress indicator (e.g. '2 of 5 completed'), actionable checklist items with direct deep-links, and a dismiss button.",
            "why": "Leverages the Zeigarnik effect (tendency to complete unfinished tasks) and guides users to their 'Aha!' activation moment.",
            "anti_patterns": "Checklists longer than 5 items, non-dismissible intrusive cards, or tasks that require off-platform actions.",
            "metrics": {
                "task_count_max": 5,
                "progress_ring_size_px": 36,
                "item_touch_target_px": 44,
                "standard": "Miller's Law (5±2); Apple HIG 44pt touch target"
            },
            "use_when": "Post-signup user activation in complex web applications."
        },
        {
            "name": "Interactive Product Tour / Spotlight",
            "structure": "Darkened backdrop scrim highlighting an actual UI element on screen. Attached popover dialog contains: step indicator ('Step 2 of 4'), concise guidance text, 'Skip Tour' secondary link, and 'Next' primary button.",
            "why": "Contextual in-situ learning is proven far more effective than detached video tutorials or static docs.",
            "anti_patterns": "Tours with more than 4 steps, locking the entire interface without escape/skip options, or pointing at obvious buttons.",
            "metrics": {
                "max_steps": 4,
                "popover_max_width_px": 320,
                "button_min_height_px": 44,
                "standard": "Cognitive load limits; Apple HIG 44pt touch target"
            },
            "use_when": "Introducing key workflows to first-time users or rolling out major navigation updates."
        },
        {
            "name": "Role / Persona Customizer Wizard",
            "structure": "Full-screen modal wizard: Step 1 asks 'What best describes your role?' with 4 selectable card tiles. Step 2 asks 'What is your primary goal?' with 3 options. Final step tailors the workspace layout to the selected persona.",
            "why": "Enables personalized default experiences and helps software cater to both engineers and managers without clutter.",
            "anti_patterns": "Forcing users through extensive survey questions before letting them touch the software, or failing to save choices.",
            "metrics": {
                "card_min_height_px": 80,
                "options_per_step_max": 4,
                "min_tap_target_px": 44,
                "standard": "Hick's Law; Apple HIG 44pt touch target"
            },
            "use_when": "Multi-persona platforms such as project management, BI, and devops tools."
        },
        {
            "name": "Empty-State First-Action Canvas",
            "structure": "Centered in an empty workspace: relevant functional graphic or diagram, clear H3 heading ('Create your first project'), 1-sentence explanatory body (max 120 chars), and prominent primary CTA button ('+ New Project').",
            "why": "Transforms intimidating blank slate syndrome into a clear, single-path call to constructive action.",
            "anti_patterns": "Blank white screens with no direction, technical error messages ('Query returned 0 rows'), or disabled action buttons.",
            "metrics": {
                "cta_min_height_px": 44,
                "helper_text_max_chars": 120,
                "contrast_ratio_body": "4.5:1",
                "standard": "Apple HIG 44pt; Bringhurst line length; WCAG 2.2 AA Criterion 1.4.3"
            },
            "use_when": "Initial dashboard, project lists, and collection views before data is created."
        }
    ],
    "ecommerce_product": [
        {
            "name": "Split Product Detail Gallery & Purchase Pane",
            "structure": "Desktop 12-column layout: left 7 columns contain a sticky vertical image gallery with thumbnail strip and image zoom. Right 5 columns contain product title, customer rating stars with review count, price, variant swatches, quantity stepper, and full-width 'Add to Cart' button.",
            "why": "Ensures the purchase action and pricing remain anchored in view while the user browses multiple product images.",
            "anti_patterns": "Sticky buy buttons that obscure product descriptions on mobile, or swatches that fail to update the displayed image.",
            "metrics": {
                "variant_chip_min_px": 44,
                "sticky_cta_height_px": 48,
                "contrast_ratio_body": "4.5:1",
                "standard": "Apple HIG 44pt; Material Design 48dp; WCAG 2.2 AA Criterion 1.4.3"
            },
            "use_when": "E-commerce product detail pages (PDP)."
        },
        {
            "name": "Product Card with Variant Preview",
            "structure": "Aspect-ratio 1:1 image container with subtle hover zoom. Card footer: brand name in 12px uppercase, product title clamped to 2 lines, current price with strikethrough original price, and color swatch dots.",
            "why": "Enables fast product discovery and variant awareness in category listings without requiring page navigation.",
            "anti_patterns": "Unclamped product titles breaking grid alignment, missing image aspect ratio causing layout shift (CLS), or swatches smaller than 24px.",
            "metrics": {
                "image_aspect_ratio": "1:1",
                "title_max_lines": 2,
                "swatch_min_size_px": 24,
                "swatch_tap_target_px": 44,
                "standard": "WCAG 2.2 AA Criterion 2.5.8 (Target Size); Apple HIG 44pt"
            },
            "use_when": "Product listing pages (PLP), search results, and recommended item carousels."
        },
        {
            "name": "Slide-Over Mini-Cart Drawer",
            "structure": "Right-docked drawer sliding in upon 'Add to Cart'. Displays: list of cart items with thumbnail, title, price, and quantity stepper [- 1 +], free shipping progress bar, subtotal summary, and 'Proceed to Checkout' button.",
            "why": "Provides immediate confirmation of item addition while keeping the user on the shopping page to encourage continued browsing.",
            "anti_patterns": "Forcing a full page redirect to a cart page for every added item, or hiding quantity controls.",
            "metrics": {
                "drawer_width_max_px": 400,
                "stepper_button_min_px": 44,
                "checkout_cta_min_px": 48,
                "standard": "Apple HIG 44pt; Material Design 48dp"
            },
            "use_when": "E-commerce storefronts with multi-item purchasing behaviors."
        },
        {
            "name": "Faceted Filter Sidebar",
            "structure": "Left sidebar on desktop, slide-out sheet on mobile. Accordion sections for: Price Range (dual-handle slider), Category (checkboxes with item counts), Rating (stars), and In Stock (toggle). Top active filter chips with 'Clear all'.",
            "why": "Empowers shoppers to narrow broad catalogs systematically using multiple overlapping criteria.",
            "anti_patterns": "Applying filters without updating URL query parameters, or filter checkboxes with tap areas under 44px.",
            "metrics": {
                "checkbox_row_height_px": 40,
                "checkbox_target_px": 44,
                "clear_all_tap_target_px": 44,
                "standard": "Apple HIG 44pt touch target; WCAG 2.2 AA Criterion 2.5.8"
            },
            "use_when": "Large-catalog e-commerce, marketplace search, and filtered inventory browsers."
        }
    ],
    "navigation": [
        {
            "name": "Responsive Global Header",
            "structure": "Top bar: logo left (max height 32px), primary navigation links center (max 6 links), right utilities: global search shortcut button ('Cmd+K' / 'Ctrl+K'), notifications bell, and user avatar dropdown menu.",
            "why": "Establishes a permanent orientation anchor across the application, satisfying Nielsen's Heuristic #1.",
            "anti_patterns": "More than 7 primary links in top bar causing wrapping, missing mobile hamburger/bottom-bar transition, or non-keyboard-accessible menus.",
            "metrics": {
                "header_height_desktop_px": 64,
                "header_height_mobile_px": 56,
                "max_primary_links": 6,
                "min_tap_target_px": 44,
                "standard": "Miller's Law (7±2); Material Design 56dp mobile bar; Apple HIG 44pt"
            },
            "use_when": "Top-level application chrome and public marketing websites."
        },
        {
            "name": "Collapsible Sidebar Navigation",
            "structure": "Vertical navigation container on left: top team/workspace switcher, scrollable navigation item group (icon + label + optional count badge), bottom collapse toggle button transitioning sidebar to 64px icon-only rail.",
            "why": "Offers scalable hierarchy for deep application sections while letting power users reclaim horizontal screen real estate.",
            "anti_patterns": "Icon-only sidebars without tooltips explaining what each icon represents, or missing active state indicators.",
            "metrics": {
                "expanded_width_px": 240,
                "collapsed_width_px": 64,
                "item_min_height_px": 44,
                "active_indicator_width_px": 3,
                "standard": "Apple HIG 44pt touch target; 8pt spatial grid"
            },
            "use_when": "Desktop web apps, admin portals, and IDE environments."
        },
        {
            "name": "Command Palette / Quick Switcher",
            "structure": "Centered modal overlay triggered by Cmd+K or Ctrl+K. Search input with autofocus, categorized result list ('Recent', 'Pages', 'Actions', 'Settings') navigable with arrow keys, and keyboard shortcut hints on right.",
            "why": "Provides keyboard power users with lightning-fast navigation across hundreds of destinations without mouse traversal.",
            "anti_patterns": "Missing keyboard arrow navigation, slow non-instant search indexing, or failure to close on Escape key.",
            "metrics": {
                "modal_width_px": 600,
                "item_height_px": 44,
                "max_visible_items": 8,
                "search_debounce_ms": 150,
                "standard": "Miller's Law (7±2); Apple HIG 44pt; NN/g response limits"
            },
            "use_when": "Productivity applications, developer portals, and complex B2B platforms."
        },
        {
            "name": "Breadcrumb Hierarchy Trail",
            "structure": "Horizontal breadcrumb trail above page title: Home / Section / Sub-section / Current Page. Separators use subtle slash or chevron icon. Intermediate nodes are active links; final node is plain text indicating current location.",
            "why": "Communicates hierarchical location within deep information architectures and provides single-click parent navigation.",
            "anti_patterns": "Making the current active page a clickable link to itself, or missing truncation for deep paths >4 levels.",
            "metrics": {
                "separator_contrast": "3.0:1",
                "item_min_tap_target_px": 44,
                "max_visible_crumb_levels": 4,
                "standard": "WCAG 2.2 AA Criterion 1.4.11; Apple HIG 44pt touch target"
            },
            "use_when": "Hierarchical document stores, nested settings panels, and multi-tier product catalogs."
        }
    ],
    "settings_configuration": [
        {
            "name": "Categorized Settings Layout",
            "structure": "Two-pane layout: left vertical sub-navigation ('General', 'Security', 'Billing', 'Team', 'Integrations') with 220px width. Right pane: settings card (max-width 800px) with grouped form rows and a sticky bottom save bar.",
            "why": "Organizes complex configuration into modular mental categories, preventing single-page cognitive overload.",
            "anti_patterns": "Unsaved changes lost silently on tab switch, or putting all settings into a single infinite-scroll page.",
            "metrics": {
                "subnav_width_px": 220,
                "content_max_width_px": 800,
                "sticky_bar_height_px": 64,
                "min_tap_target_px": 44,
                "standard": "Apple HIG 44pt; 8pt spatial grid; Bringhurst line length"
            },
            "use_when": "User profile settings, workspace administration, and developer project configuration."
        },
        {
            "name": "Form Row Field Group",
            "structure": "Standardized two-column row: left 40% contains setting title (14px font-semibold) and brief explanation (13px text-muted). Right 60% contains interactive control (Input, Select, Toggle switch) with inline helper text.",
            "why": "Establishes a predictable visual rhythm where the purpose of every configuration option is explained directly beside its control.",
            "anti_patterns": "Unclear toggle labels where users cannot tell if enabling means on or off, or missing error feedback.",
            "metrics": {
                "row_gap_y_px": 24,
                "helper_text_contrast": "4.5:1",
                "input_min_height_px": 44,
                "standard": "WCAG 2.2 AA Criterion 1.4.3; Apple HIG 44pt touch target; 8pt grid"
            },
            "use_when": "System preference panels, profile forms, and configuration dialogs."
        },
        {
            "name": "Danger Zone Panel",
            "structure": "Distinct panel with red border (1px) and subtle red-tinted header: 'Danger Zone'. Destructive actions ('Delete Workspace', 'Transfer Ownership') require an explicit confirmation modal with typed confirmation (e.g. type workspace name).",
            "why": "Implements Nielsen's Heuristic #5 (Error Prevention) by adding friction to irreversible, high-consequence operations.",
            "anti_patterns": "Single-click destructive deletion, generic 'Are you sure?' dialogs without typing requirement, or red styling on non-destructive actions.",
            "metrics": {
                "border_color_contrast": "3.0:1",
                "confirm_input_min_height_px": 44,
                "button_min_height_px": 44,
                "standard": "Nielsen Heuristic #5 (Error Prevention); WCAG 2.2 AA 1.4.11; Apple HIG 44pt"
            },
            "use_when": "Account deletion, repository removal, API key revocation, and subscription cancellations."
        },
        {
            "name": "API Keys / Secret Management Table",
            "structure": "Table listing active API tokens: Key Name, Masked Secret (e.g. 'jeb_live_...4a9f') with 1-click reveal and copy button, Created Date, Last Used timestamp, and 'Revoke' action button.",
            "why": "Balances security by never displaying plain-text secrets after initial creation while enabling audits of token usage.",
            "anti_patterns": "Displaying full API keys in plaintext in the DOM, or failing to record last-used dates for security auditing.",
            "metrics": {
                "row_height_px": 48,
                "copy_button_target_px": 44,
                "masked_chars_preview": 4,
                "standard": "Material Design 48dp; Apple HIG 44pt touch target"
            },
            "use_when": "Developer portals, webhook configurations, and API credential management."
        }
    ],
    "empty_error_states": [
        {
            "name": "Zero-Data Empty State",
            "structure": "Centered in viewport or card: relevant semantic illustration or icon (max 160px height), clear H3 title ('No projects yet'), 1-sentence supportive explanation (max 120 chars), and prominent primary action button ('Create Project').",
            "why": "Guides first-time users directly toward their primary task rather than leaving them in a confusing dead-end.",
            "anti_patterns": "Technical error jargon on empty datasets, missing call-to-action buttons, or generic sad-face illustrations.",
            "metrics": {
                "illustration_max_height_px": 160,
                "heading_max_words": 6,
                "body_max_chars": 120,
                "button_min_height_px": 44,
                "standard": "Apple HIG 44pt; Bringhurst line length; Nielsen Heuristic #1"
            },
            "use_when": "First-run experience in new workspaces, empty search results, and cleared inboxes."
        },
        {
            "name": "404 Not Found Recovery Screen",
            "structure": "Centered layout: prominent '404' indicator in font-bold, clear message ('Page not found'), search input to find existing content, and quick navigation links ('Back to Dashboard', 'Documentation', 'Contact Support').",
            "why": "Prevents visitor bounce by acknowledging the error gracefully and offering immediate recovery paths.",
            "anti_patterns": "Dead-end error pages with no navigation links, confusing humorous text that fails to explain what happened, or broken search bars.",
            "metrics": {
                "search_input_height_px": 44,
                "button_min_height_px": 44,
                "contrast_ratio_body": "4.5:1",
                "standard": "Apple HIG 44pt; WCAG 2.2 AA Criterion 1.4.3"
            },
            "use_when": "HTTP 404 error pages and broken link redirects."
        },
        {
            "name": "Inline Form Field Error Feedback",
            "structure": "Form input highlighted with red border (1px solid), accompanied by an inline error icon and descriptive message immediately below the input. Input element carries aria-invalid='true' and aria-describedby pointing to the error message ID.",
            "why": "Satisfies WCAG 3.3.1 (Error Identification) by communicating exact validation failures inline to all users including screen readers.",
            "anti_patterns": "Error messages shown only at the top of the page far from the failing input, or using red border color alone without text.",
            "metrics": {
                "error_text_contrast": "4.5:1",
                "border_error_contrast": "3.0:1",
                "icon_size_px": 16,
                "standard": "WCAG 2.2 AA Criterion 3.3.1; Criterion 1.4.3; Criterion 1.4.11"
            },
            "use_when": "Form validation errors, password requirement mismatches, and duplicate entity errors."
        },
        {
            "name": "Network / Service Degradation Banner",
            "structure": "Full-width persistent top banner: warning triangle icon, clear status message ('Service degradation detected — real-time updates may be delayed'), 'Retry' button, and link to public status page.",
            "why": "Informs users of external issues before they suspect bugs in their own work, honoring Nielsen's Visibility of System Status.",
            "anti_patterns": "Silent background failures without user alerts, or aggressive modal dialogs that interrupt current unsaved work.",
            "metrics": {
                "banner_min_height_px": 48,
                "retry_button_min_px": 44,
                "text_contrast": "4.5:1",
                "non_text_contrast": "3.0:1",
                "standard": "Material Design 48dp; Apple HIG 44pt; WCAG 2.2 AA Criterion 1.4.3; Criterion 1.4.11"
            },
            "use_when": "Offline connectivity alerts, API rate limits, and cloud maintenance windows."
        }
    ],
    "mobile_patterns": [
        {
            "name": "Bottom Navigation Bar",
            "structure": "Fixed bottom bar on mobile screens (56px height): 3 to 5 evenly spaced tabs with icon (24px) and text label (11px). Active tab is indicated by primary color and font weight. Includes safe-area-inset-bottom padding.",
            "why": "Places top destinations directly inside the natural thumb reach zone for one-handed mobile ergonomics.",
            "anti_patterns": "More than 5 tabs causing overlapping labels, omitting text labels (icons-only), or failing to respect device bottom home indicator safe area.",
            "metrics": {
                "min_tap_target_px": 44,
                "bar_height_px": 56,
                "tab_count_min": 3,
                "tab_count_max": 5,
                "safe_area_padding_bottom": "env(safe-area-inset-bottom)",
                "standard": "Apple HIG 44pt tap target; Material Design 3 56dp bottom bar; Miller's Law"
            },
            "use_when": "Primary mobile app navigation and mobile web application chrome."
        },
        {
            "name": "Thumb-Zone Action Placement",
            "structure": "Screen layout divided into zones: top 25% for passive status and navigation titles; middle 40% for content consumption; bottom 35% for primary interactive controls, action buttons, and floating action buttons (FAB).",
            "why": "Aligns with Steven Hoober's mobile ergonomics research showing 49% of users hold phones with one hand and navigate with their thumb.",
            "anti_patterns": "Placing critical primary actions or confirmation buttons in the top-left corner where one-handed reach is impossible.",
            "metrics": {
                "thumb_zone_vertical_pct": "bottom 35%",
                "fab_min_size_px": 56,
                "min_tap_target_px": 44,
                "standard": "Steven Hoober Thumb Zone Research; Material Design 56dp FAB; Apple HIG 44pt"
            },
            "use_when": "Mobile-first web designs, responsive web applications, and iOS/Android client interfaces."
        },
        {
            "name": "Swipe Actions on List Items",
            "structure": "Horizontal swipe gesture on list rows: swiping left reveals destructive/secondary actions (e.g. 'Delete', 'Archive' with 72px width); swiping right reveals primary/completion action. Threshold triggers full activation with tactile feedback.",
            "why": "Enables rapid single-gesture triage of items in mobile lists without opening individual detail views.",
            "anti_patterns": "Swipe actions with no visual icon/text label, missing undo toast notification for destructive swipes, or conflicting horizontal scroll containers.",
            "metrics": {
                "swipe_threshold_px": 72,
                "action_button_width_px": 72,
                "min_tap_target_px": 44,
                "drag_deadzone_px": 10,
                "standard": "Apple HIG swipe gestures; Apple HIG 44pt touch target"
            },
            "use_when": "Mobile inboxes, task management lists, notification centers, and shopping cart items."
        },
        {
            "name": "Modal Bottom Sheet / Action Sheet",
            "structure": "Bottom sheet sliding up over a 50% opacity backdrop scrim. Features a top drag handle pill (36×4px), title header, list of options or form controls with 44px tap targets, and a cancel button at the bottom.",
            "why": "Keeps secondary actions and choices within thumb reach while maintaining spatial awareness of the underlying screen.",
            "anti_patterns": "Full-screen dialogs for simple 2-choice decisions, missing drag handle indicator, or non-dismissible sheets.",
            "metrics": {
                "handle_pill_width_px": 36,
                "handle_pill_height_px": 4,
                "min_tap_target_px": 44,
                "backdrop_opacity": 0.5,
                "standard": "Apple HIG sheets; Material Design bottom sheet; Apple HIG 44pt touch target"
            },
            "use_when": "Mobile contextual menus, sharing sheets, filters, and short mobile forms."
        }
    ]
}
