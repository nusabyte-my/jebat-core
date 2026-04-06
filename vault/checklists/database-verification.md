# Database Verification Checklist

Use for work led by Bendahara or any task involving schema, queries, migrations, or persistence behavior.

## Before Sign-Off

- Data model impact is understood
- Backward compatibility was considered
- Index or performance impact was checked where relevant
- Migration path and rollback posture were considered
- Soft-delete, nullability, and constraint behavior were reviewed

## Verification

- Migration or query sanity was checked
- ORM and schema expectations still align
- Data integrity risks are documented
- Penyemak is used if the change is production-relevant or difficult to reverse
