# Reviewed Skill Attestation Format

## Goal

Provide a Jebat-native attestation format for reviewed external skills.

---

## Required fields
- skillName
- source
- reviewedAt
- reviewer
- score
- maxScore
- trustClass
- verdict
- evidence
- concerns
- plannedUse
- scope

---

## Example
```json
{
  "skillName": "agent-team-orchestration",
  "source": "https://github.com/openclaw/skills/tree/main/skills/arminnaimi/agent-team-orchestration",
  "reviewedAt": "2026-03-30T00:54:00+08:00",
  "reviewer": "Jebat",
  "score": 25,
  "maxScore": 30,
  "trustClass": "adapt with caution",
  "verdict": "APPROVE WITH CAUTION",
  "evidence": [
    "clear frontmatter and trigger description",
    "uses references for progressive disclosure",
    "strong handoff and review workflow"
  ],
  "concerns": [
    "no full companion script audit yet",
    "not approved for blind install"
  ],
  "plannedUse": [
    "delegation patterns",
    "reviewer-builder split"
  ],
  "scope": "pattern adaptation only"
}
```
