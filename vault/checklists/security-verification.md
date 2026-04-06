# Security Verification Checklist

Use for work led by Hulubalang or any task that changes attack surface, auth, secrets, permissions, or exposed systems.

## Before Sign-Off

- Scope and authorization are explicit
- Secret handling was reviewed
- Access control assumptions were checked
- Negative-path behavior was tested where relevant
- Risk of data exposure or privilege escalation was considered

## Verification

- Evidence of the finding or mitigation is recorded
- Security-sensitive changes were reviewed independently
- Residual risk and untested paths are stated clearly
- External or production actions were not taken without explicit approval
