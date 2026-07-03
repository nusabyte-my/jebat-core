# Q3 2026 Sprint 11-12: Multi-Tenancy

## Objective
Implement multi-tenant support with row-level security, tenant context management, resource quotas, and usage tracking for the JEBAT platform.

## Requirements
- Row-level security in PostgreSQL
- Tenant context middleware for FastAPI
- User isolation with tenant-aware queries
- Resource quotas (API calls, memory, agents, storage)
- Usage tracking and billing integration ready
- Tenant management API (create, update, delete, list)
- Admin dashboard for tenant oversight

## Package Structure
```
jebat/features/multi_tenant/
├── __init__.py
├── models.py              # Tenant, TenantUser, Quota, Usage models
├── middleware.py          # Tenant context middleware
├── security.py            # Row-level security policies
├── quota.py               # Quota enforcement
├── usage.py               # Usage tracking
├── api.py                 # Tenant management endpoints
├── migration.py           # Migration utilities
└── tests/
    ├── test_models.py
    ├── test_middleware.py
    ├── test_quota.py
    └── test_usage.py
```

## Sprint 11: Core Multi-Tenancy (Week 1-2)
- [ ] Database models with tenant_id on all entities
- [ ] Row-level security policies (PostgreSQL RLS)
- [ ] Tenant context middleware (extract from JWT/subdomain/header)
- [ ] Tenant-aware query base classes
- [ ] Migration for existing data (default tenant)
- [ ] Tests for tenant isolation

## Sprint 12: Quotas & Usage (Week 3-4)
- [ ] Quota definitions (per-tenant, per-user)
- [ ] Quota enforcement middleware
- [ ] Usage tracking (async, batched)
- [ ] Tenant management API
- [ ] Admin endpoints for tenant oversight
- [ ] Billing integration hooks
- [ ] Documentation & integration guides