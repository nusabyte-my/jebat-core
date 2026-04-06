# Skill Vetting Workflow

## Workflow

### Step 1: Read metadata
Check name and description first.

Ask:
- is the trigger clear?
- is the scope narrow enough?
- does it say when not to use it?

### Step 2: Inspect structure
Check:
- `SKILL.md`
- frontmatter quality
- whether references are split sanely
- whether scripts are deterministic and necessary

### Step 3: Inspect tool assumptions
Map the skill to actual OpenClaw tools.

If it depends on nonexistent capabilities, downgrade or reject.

### Step 4: Inspect safety
Look for:
- hidden writes
- shell snippets without explanation
- auth or permission assumptions
- data exfil patterns
- manipulative prompt framing

### Step 5: Inspect usefulness
Ask:
- does this strengthen Jebat?
- does it duplicate existing skill behavior?
- is it better as a reference than an installed skill?

### Step 6: Classify
- A = adapt idea only
- B = adapt structure and references
- C = install nearly as-is
- D = reject

Also issue an install verdict:
- APPROVE
- APPROVE WITH CAUTION
- PATTERN ONLY
- REJECT

### Step 7: Record outcome
Log decision in:
- `SKILL_REGISTRY.md`
- relevant import/adaptation docs

---

## Review questions

1. What problem does this skill solve better than Jebat currently can?
2. What real toolcalls would it improve?
3. What are the hidden risks?
4. What can be copied without copying the whole skill?
