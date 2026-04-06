# Security Review Playbook

Use this playbook for security reviews, hardening work, auth changes, exposed-surface analysis, and remediation planning.

## Trigger

Use when the task changes attack surface, auth, permissions, secret handling, or public exposure, or when a dedicated security review is requested.

## Primary Roles

- Panglima
- Hulubalang
- Tukang / Tukang Web / Bendahara / Syahbandar as needed
- Penyemak

## Workflow

1. Scope
- Confirm system boundaries, authorization, and non-goals
- Identify whether the task is review-only, hardening, or remediation

2. Surface Map
- Identify exposed assets, trust boundaries, auth paths, secrets, and high-risk flows
- Separate confirmed facts from hypotheses

3. Route
- Database exposure -> Bendahara
- Infra or deploy exposure -> Syahbandar
- Application or API exposure -> Tukang or Tukang Web

4. Review Or Remediate
- Record evidence before proposing fixes
- Prefer minimum-force review posture
- For remediation, keep fixes specific and traceable to the identified risk

5. Verify
- Use `vault/checklists/security-verification.md`
- Add `vault/checklists/engineering-verification.md` or `vault/checklists/database-verification.md` when code or data changes are involved
- Use Penyemak for an independent review on meaningful security changes

6. Consolidate
- Write a decision file if a policy, hardening rule, or security workflow changes future behavior
- Update project memory if operational security posture changes

## Deliverables

- scoped security review summary
- evidence and findings
- remediation plan or implemented fix summary
- residual risk and follow-up actions
