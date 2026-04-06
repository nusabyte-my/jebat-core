# Companion Script Inspection

## Scope
Inspected companion scripts from shortlisted external skills:
- `arc-trust-verifier/scripts/trust_verifier.py`
- `arc-security-audit/scripts/audit.py`

These are external/untrusted sources and were reviewed only for patterns and obvious risks.

---

## 1. arc-trust-verifier script

### Good signs
- uses SHA-256 hashing for file integrity
- avoids following symlinks in directory hashing
- uses realpath checks to reduce path traversal / symlink abuse
- has explicit trust-level mapping
- tries to score concrete signals rather than pure vibes

### Concerns
- some trust signals are simplistic (e.g. “has scripts”, “has docs”) and can be gamed
- suspicious-pattern matching is useful but shallow
- visible scoring model may over-trust clean-looking malicious skills
- file-size / count heuristics are weak as a trust indicator
- direct code snippet shown was truncated, so full review is incomplete

### Jebat takeaway
Adopt:
- integrity hashing concept
- symlink / realpath safety checks
- explicit trust-level output

Do not blindly adopt:
- naive scoring assumptions
- simplistic “documentation present = trust” signals

---

## 2. arc-security-audit script

### Good signs
- resolves paths with realpath
- checks sibling tool locations under expected skill base
- performs stack-wide audit pass
- combines scan + trust + report into one flow
- only generates attestations after cleaner conditions are met

### Concerns
- depends on companion skills being installed and importable
- inherited trust quality depends on trust-verifier quality
- if scanner or verifier are weak, consolidated output can look stronger than it really is
- script review was truncated before full output/rendering logic

### Jebat takeaway
Adopt:
- combined audit architecture
- explicit risk-level sorting
- conditional attestation generation

Do not blindly adopt:
- implicit dependence on external companion tooling
- confidence inflation from chained tools

---

## Net conclusion

The companion scripts make the shortlisted skills more credible, but still not enough for blind import.

Updated practical stance:
- safe to keep at **APPROVE WITH CAUTION**
- good source of implementation patterns
- still better adapted into Jebat than directly inherited wholesale
