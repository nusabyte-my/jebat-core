# Feature Delivery Playbook

Use this playbook for product or engineering work that turns a request into a shipped implementation slice.

## Trigger

Use when the task involves a feature, bug fix, scope decision, or cross-layer implementation.

## Primary Roles

- Panglima
- Strategi Produk
- Pembina Aplikasi
- Tukang / Tukang Web / Bendahara / Hulubalang as needed
- Penyemak

## Workflow

1. Capture
- Define the objective, user, constraints, risks, and desired outcome
- Use `vault/templates/feature-brief.md` if the task needs a formal brief

2. Shape
- Route through Strategi Produk if scope is unclear
- Turn the request into explicit acceptance criteria
- Decide the minimum useful slice

3. Route
- Use `vault/playbooks/dispatch-matrix.md`
- Add specialists only for the domains actually touched

4. Execute
- Assign clear ownership by layer or artifact
- Keep changes within the smallest shippable slice

5. Verify
- Use `vault/checklists/engineering-verification.md`
- Add domain-specific checklists if security, DB, automation, UI/UX, or support are involved
- Use Penyemak for a fresh validation pass on meaningful work

6. Consolidate
- Update `memory/YYYY-MM-DD.md` if the work changes the operating state
- Write a decision file if the workflow or architecture changes future behavior

## Deliverables

- implementation spec or feature brief
- changed code or content artifacts
- verification summary
- residual risk and next action
