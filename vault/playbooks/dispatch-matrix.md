# Dispatch Matrix

This matrix defines the default routing path for common NusaByte task types.

## Rules

- Route to the minimum useful specialist set.
- Use `Panglima` for ambiguous, cross-domain, or high-impact work.
- Use `Penyemak` when implementation risk, public exposure, or cross-agent complexity is meaningful.
- If security risk is involved, include `Hulubalang` early.
- Use a matching checklist from `vault/checklists/` during verification when one exists.
- Use `vault/playbooks/feature-delivery.md` for implementation work and `vault/playbooks/launch-flow.md` for public-facing launches.
- Use `vault/playbooks/support-flow.md` for onboarding and support work.
- Use `vault/playbooks/security-review.md` for security review and hardening work.
- Use `vault/playbooks/client-proposal.md` for client proposals and SOW drafting.
- Use `vault/playbooks/sales-enablement.md` for one-pagers, outbound support, and sales collateral.
- Use `vault/playbooks/discovery-call.md` for early client discovery and qualification.
- Use `vault/playbooks/retainer-ops.md` for ongoing client cadence and recurring work management.
- Use `vault/playbooks/monthly-review.md` for end-of-cycle reviews and next-period planning.
- Use `vault/playbooks/quarterly-planning.md` for next-quarter prioritization and roadmap alignment.
- Use `vault/playbooks/renewal-strategy.md` for renewals, upsells, and scope renegotiation.

## Matrix

| Task Type | Primary Role | Supporting Roles | Verifier |
|-----------|--------------|------------------|----------|
| New project or ambiguous scope | Panglima | Pawang, Brand Strategy, Analyst as needed | Penyemak if execution follows |
| Research, comparison, investigation | Pawang | Analyst, Hikmat | Optional |
| Web UI build or frontend fix | Tukang Web | Senibina Antara Muka, Tukang | Penyemak |
| Cross-layer product feature | Pembina Aplikasi | Tukang, Bendahara, Hulubalang, Analyst | Penyemak |
| Backend/API delivery | Tukang | Bendahara, Hulubalang | Penyemak |
| DB schema or migration | Bendahara | Tukang, Hulubalang | Penyemak |
| Automation, deploy, CI/CD | Syahbandar | Tukang, Hulubalang, Bendahara | Penyemak |
| Security review or hardening | Hulubalang | Tukang, Syahbandar, Bendahara | Penyemak |
| UX redesign or flow repair | Senibina Antara Muka | Tukang Web, Copywriting | Penyemak |
| Landing page or campaign page | Jurutulis Jualan | Senibina Antara Muka, Tukang Web, SEO, Brand Strategy | Penyemak |
| SEO content or search improvement | Penjejak Carian | Content Creation, Copywriting, Tukang Web, Analyst | Penyemak |
| Campaign planning | Penggerak Pasaran | Brand Strategy, Copywriting, Content Creation, SEO, Analyst | Optional |
| Brand architecture or messaging reset | Brand Strategy | Marketing, Copywriting, Content Creation | Optional |
| Product scope or roadmap shaping | Product Strategy | Pembina Aplikasi, Analyst, Brand Strategy | Optional |
| Onboarding or support workflow improvement | Customer Success | Senibina Antara Muka, Product Strategy, Tukang Web, Content Creation | Penyemak |
| Discovery call or qualification intake | Panglima | Pawang, Product Strategy, Brand Strategy, Proposal Writing | Optional |
| Client proposal or SOW drafting | Proposal Writing | Product Strategy, Brand Strategy, Marketing, Analyst | Penyemak if commitments are significant |
| Sales collateral or objection handling | Sales Enablement | Brand Strategy, Copywriting, Marketing, Proposal Writing | Optional |
| Retainer planning or recurring client ops | Panglima | Customer Success, Analyst, Product Strategy, Marketing, Proposal Writing | Penyemak if scope or commitments change |
| Monthly review or renewal preparation | Panglima | Analyst, Customer Success, Product Strategy, Marketing, Proposal Writing | Optional |
| Quarterly planning or roadmap alignment | Panglima | Product Strategy, Marketing, Analyst, Customer Success, Proposal Writing | Optional |
| Renewal strategy or scope renegotiation | Panglima | Proposal Writing, Analyst, Customer Success, Product Strategy, Marketing, Sales Enablement | Penyemak if commitments are material |
| Content system or editorial asset | Pengkarya Kandungan | Brand Strategy, Copywriting, SEO | Optional |
| KPI, funnel, experiment review | Analyst | Marketing, SEO, Product roles | Optional |

## Standard Handoff Fields

- Objective
- Audience or user
- Constraints and risks
- Allowed files/scope
- Output format
- Acceptance criteria
- Verification required
- Checklist path when applicable

## Escalation Patterns

- `security + data` -> Hulubalang + Bendahara
- `security + ops` -> Hulubalang + Syahbandar
- `growth + implementation` -> Penggerak Pasaran + Tukang Web + relevant growth specialists
- `brand + campaign` -> Brand Strategy + Penggerak Pasaran + Jurutulis Jualan
- `product + analytics` -> Pembina Aplikasi + Analyst
- `product + support` -> Customer Success + Product Strategy + relevant delivery roles
- `proposal + scope` -> Proposal Writing + Product Strategy + Brand Strategy
- `sales + proposal` -> Sales Enablement + Proposal Writing + Brand Strategy
- `discovery + proposal` -> Panglima + Pawang + Proposal Writing
- `retainer + scope` -> Panglima + Customer Success + Proposal Writing
- `review + renewal` -> Panglima + Analyst + Proposal Writing
- `quarter + roadmap` -> Panglima + Product Strategy + Analyst
- `renewal + upsell` -> Panglima + Proposal Writing + Analyst + Customer Success
