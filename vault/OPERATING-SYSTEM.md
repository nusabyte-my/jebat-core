# JEBAT Operating System

This file is the top-level map of the JEBAT workspace operating model.

Use it as the fastest way to understand:

- who the agents are
- how work is routed
- which playbook to use
- which template to start from
- which checklist to verify with
- how to run structural validation

## Core Files

- Shared core: `skills/_core/CODEX_CORE.md`
- Routing policy: `AGENTS.md`
- Canonical roster: `ORCHESTRA.md`
- Operating index: `MEMORY.md`
- Workspace validation: `validate-workspace.ps1`

## Agent Roster

### Command Layer

- `Panglima`: orchestration, synthesis, capture-first planning
- `Hikmat`: memory and continuity
- `Agent Dispatch`: multi-domain routing and sequencing

### Delivery Layer

- `Tukang`: implementation and builds
- `Tukang Web`: browser-facing work
- `Pembina Aplikasi`: cross-layer app delivery
- `Bendahara`: database and schema
- `Syahbandar`: automation and deployment

### Quality And Risk

- `Hulubalang`: security and hardening
- `Penyemak`: QA and independent verification

### Design, Growth, And Strategy

- `Senibina Antara Muka`: UI/UX
- `Pengkarya Kandungan`: content creation
- `Jurutulis Jualan`: copywriting
- `Penjejak Carian`: SEO
- `Penggerak Pasaran`: marketing
- `Penganalisis`: metrics and experiment analysis
- `Strategi Jenama`: brand strategy
- `Strategi Produk`: product strategy

### Commercial And Client Operations

- `Khidmat Pelanggan`: support and onboarding
- `Penulis Cadangan`: proposals and SOWs
- `Penggerak Jualan`: sales enablement

## Workflow Phases

1. Capture
- define objective, audience, constraints, risks, and outcome

2. Route
- use `vault/playbooks/dispatch-matrix.md`

3. Execute
- choose the minimum useful specialist set

4. Verify
- use matching files in `vault/checklists/`
- use Penyemak on meaningful work

5. Consolidate
- update `memory/YYYY-MM-DD.md`
- write a decision file if future behavior changes

## Playbooks

### Delivery And Operations

- `vault/playbooks/feature-delivery.md`
- `vault/playbooks/launch-flow.md`
- `vault/playbooks/security-review.md`
- `vault/playbooks/support-flow.md`

### Commercial Lifecycle

- `vault/playbooks/discovery-call.md`
- `vault/playbooks/client-proposal.md`
- `vault/playbooks/sales-enablement.md`
- `vault/playbooks/retainer-ops.md`
- `vault/playbooks/monthly-review.md`
- `vault/playbooks/quarterly-planning.md`
- `vault/playbooks/renewal-strategy.md`

### Routing

- `vault/playbooks/dispatch-matrix.md`

## Templates

- `vault/templates/feature-brief.md`
- `vault/templates/campaign-brief.md`
- `vault/templates/seo-audit.md`
- `vault/templates/acceptance-spec.md`
- `vault/templates/discovery-brief.md`
- `vault/templates/proposal-brief.md`
- `vault/templates/sales-brief.md`
- `vault/templates/retainer-brief.md`
- `vault/templates/monthly-review.md`
- `vault/templates/quarterly-plan.md`
- `vault/templates/renewal-brief.md`

## Examples

- `vault/examples/discovery-brief-example.md`
- `vault/examples/feature-brief-example.md`
- `vault/examples/campaign-brief-example.md`
- `vault/examples/acceptance-spec-example.md`
- `vault/examples/seo-audit-example.md`
- `vault/examples/proposal-brief-example.md`
- `vault/examples/sales-brief-example.md`
- `vault/examples/retainer-brief-example.md`
- `vault/examples/monthly-review-example.md`
- `vault/examples/quarterly-plan-example.md`
- `vault/examples/renewal-brief-example.md`

## Checklists

- `vault/checklists/engineering-verification.md`
- `vault/checklists/security-verification.md`
- `vault/checklists/database-verification.md`
- `vault/checklists/automation-verification.md`
- `vault/checklists/uiux-verification.md`
- `vault/checklists/seo-verification.md`
- `vault/checklists/content-copy-verification.md`
- `vault/checklists/analytics-verification.md`
- `vault/checklists/product-support-verification.md`

## Validation

Run adapter-only validation:

```bash
python adapters/validate.py
```

Run full workspace validation:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\validate-workspace.ps1
```

## Recommended Sequences

### New Client Opportunity

1. `discovery-call`
2. `client-proposal`
3. `sales-enablement` if support collateral is needed

### Product Or Engineering Work

1. `feature-delivery`
2. matching checklists
3. `monthly-review` if work is part of a recurring cycle

### Ongoing Client Work

1. `retainer-ops`
2. `monthly-review`
3. `quarterly-planning`
4. `renewal-strategy`

### Public-Facing Growth Work

1. `launch-flow`
2. `sales-enablement` if collateral is needed
3. `monthly-review`
