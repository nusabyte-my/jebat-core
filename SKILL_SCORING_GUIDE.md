# Skill Scoring Guide

## Goal

Make external skill review more consistent by assigning simple numeric scores.

---

## Dimensions (0-5 each)

### Provenance
- 0: unknown / sketchy
- 3: somewhat credible but limited signal
- 5: strong source confidence and coherent ownership

### Structure
- 0: broken / chaotic
- 3: usable but messy
- 5: clean frontmatter, references, scripts, scope discipline

### Tool realism
- 0: fantasy capabilities
- 3: partly realistic
- 5: clearly maps to real OpenClaw tools

### Safety
- 0: unsafe or manipulative
- 3: mixed / unclear
- 5: strong boundaries, no obvious red flags

### Usefulness
- 0: irrelevant or redundant
- 3: maybe useful
- 5: strong direct value for Jebat

### Version / integrity
- 0: suspicious changes or unclear integrity
- 3: acceptable but limited evidence
- 5: coherent versioning and integrity posture

---

## Totals
- 26-30 → APPROVE
- 20-25 → APPROVE WITH CAUTION
- 13-19 → PATTERN ONLY
- 0-12 → REJECT

---

## Example
```powershell
pwsh ./scripts/skill-trust-score.ps1 \
  -SkillName "agent-team-orchestration" \
  -Provenance 3 \
  -Structure 5 \
  -ToolRealism 5 \
  -Safety 4 \
  -Usefulness 5 \
  -VersionIntegrity 3
```
