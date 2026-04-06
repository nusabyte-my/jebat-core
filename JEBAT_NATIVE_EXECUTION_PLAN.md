# JEBAT Native Execution Plan

## Goal

Convert selected reviewed patterns into more executable Jebat-native workflows.

---

## Near-term build targets

### 1. Memory execution
- daily memory review helper
- memory promotion helper
- session wrap-up helper
- stronger entity-memory separation later

### 2. Trust execution
- skill trust scoring
- reviewed skill audit
- reviewed skill delta checking
- reviewed skill attestation generation

### 3. Ops execution
- skill snapshot helper
- skill rollback helper
- snapshot inventory helper
- lifecycle logging
- provenance logging

### 4. Admin execution
- unify common actions behind `jebat-admin.ps1`
- prefer small composable helpers over one giant script

---

## Implementation philosophy
- small tools
- readable outputs
- reversible actions
- local-first
- human-reviewable state

---

## Next likely native builds
1. entity memory helper
2. reviewed-skill manifest updater
3. lifecycle diff helper
4. stronger ops dashboard generation
