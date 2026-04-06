# Automation Verification Checklist

Use for work led by Syahbandar or any task involving scripts, CI/CD, jobs, webhooks, or deploy flow.

## Before Sign-Off

- Idempotency was considered
- Failure handling and retries were reviewed
- Logging or observability is sufficient
- Permissions are limited to what the job needs
- External actions and deployment impact are understood

## Verification

- Dry-run or safe simulation was used where possible
- Trigger conditions and expected outcomes were checked
- Rollback or recovery path is stated
- Residual operational risk is documented
