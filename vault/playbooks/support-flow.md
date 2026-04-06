# Support Flow Playbook

Use this playbook for onboarding friction, repeated support pain, help-content gaps, FAQ work, and post-launch customer-success improvements.

## Trigger

Use when the task affects activation, onboarding, support load, retention, or self-serve clarity.

## Primary Roles

- Panglima
- Khidmat Pelanggan
- Strategi Produk
- Senibina Antara Muka
- Tukang Web or Tukang if implementation is needed
- Pengkarya Kandungan when help content or FAQs are required
- Penyemak

## Workflow

1. Capture
- Define the user problem, current friction, and desired success outcome
- Identify whether the issue is product, UX, docs, or operations-driven

2. Diagnose
- Route through Khidmat Pelanggan first
- Separate symptoms from root cause
- Use `vault/templates/feature-brief.md` or `vault/templates/acceptance-spec.md` if the fix needs structured scope

3. Route
- Product ambiguity -> Strategi Produk
- Flow confusion -> Senibina Antara Muka
- Help content gap -> Pengkarya Kandungan
- Implementation need -> Tukang Web or Tukang

4. Execute
- Prefer the smallest change that reduces repeat confusion
- Capture any support-language or FAQ changes needed alongside product changes

5. Verify
- Use `vault/checklists/product-support-verification.md`
- Add `vault/checklists/uiux-verification.md` if user flow changed
- Add `vault/checklists/engineering-verification.md` if code changed
- Use Penyemak when the issue materially affects activation or retention

6. Consolidate
- Update project memory if support posture or onboarding flow changes
- Write a decision file if the support workflow or product policy changes future handling

## Deliverables

- support diagnosis
- scoped fix or support specification
- updated content or implementation artifacts
- verification summary and residual support risk
