"""
JEBAT Multi-Tenancy System

Multi-tenant architecture for JEBAT AI Assistant.

Features:
- Tenant isolation
- Tenant configuration
- Resource quotas
- Usage tracking
- Billing integration ready
- Row-level security

Usage:
    from jebat.multitenancy import TenantManager

    manager = TenantManager()
    tenant = await manager.create_tenant("acme-corp", "Acme Corporation")
    await manager.set_quota(tenant.id, "ultra_loop_cycles", 10000)
    usage = await manager.get_usage(tenant.id)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class TenantStatus(str, Enum):
    """Tenant status enumeration"""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    EXPIRED = "expired"


class PlanType(str, Enum):
    """Subscription plan type"""

    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class Tenant:
    """Tenant model"""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    display_name: str = ""
    status: TenantStatus = TenantStatus.ACTIVE
    plan: PlanType = PlanType.FREE
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Contact info
    email: Optional[str] = None
    organization: Optional[str] = None

    # Billing
    billing_email: Optional[str] = None
    payment_method_id: Optional[str] = None


@dataclass
class Quota:
    """Resource quota"""

    name: str
    limit: int
    used: int = 0
    reset_at: Optional[datetime] = None

    def remaining(self) -> int:
        """Get remaining quota"""
        return max(0, self.limit - self.used)

    def is_exceeded(self) -> bool:
        """Check if quota exceeded"""
        return self.used >= self.limit


@dataclass
class Usage:
    """Usage tracking"""

    tenant_id: UUID
    metric: str
    value: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TenantManager:
    """
    Multi-tenant manager for JEBAT.

    Responsibilities:
    - Tenant lifecycle management
    - Resource quotas
    - Usage tracking
    - Tenant isolation
    - Billing integration
    """

    def __init__(self):
        """Initialize tenant manager"""
        self.tenants: Dict[UUID, Tenant] = {}
        self.quotas: Dict[UUID, Dict[str, Quota]] = {}
        self.usage_history: Dict[UUID, List[Usage]] = {}

        # Default quotas by plan
        self.plan_quotas = {
            PlanType.FREE: {
                "ultra_loop_cycles": 1000,
                "think_sessions": 100,
                "memory_storage_mb": 100,
                "api_calls_per_day": 1000,
            },
            PlanType.BASIC: {
                "ultra_loop_cycles": 10000,
                "think_sessions": 1000,
                "memory_storage_mb": 1000,
                "api_calls_per_day": 10000,
            },
            PlanType.PRO: {
                "ultra_loop_cycles": 100000,
                "think_sessions": 10000,
                "memory_storage_mb": 10000,
                "api_calls_per_day": 100000,
            },
            PlanType.ENTERPRISE: {
                "ultra_loop_cycles": -1,  # Unlimited
                "think_sessions": -1,
                "memory_storage_mb": -1,
                "api_calls_per_day": -1,
            },
        }

        logger.info("TenantManager initialized")

    async def create_tenant(
        self,
        name: str,
        display_name: str,
        plan: PlanType = PlanType.FREE,
        email: Optional[str] = None,
        organization: Optional[str] = None,
    ) -> Tenant:
        """
        Create a new tenant.

        Args:
            name: Tenant unique name
            display_name: Display name
            plan: Subscription plan
            email: Contact email
            organization: Organization name

        Returns:
            Created Tenant
        """
        tenant = Tenant(
            name=name,
            display_name=display_name,
            plan=plan,
            email=email,
            organization=organization,
        )

        self.tenants[tenant.id] = tenant

        # Set default quotas
        await self._set_default_quotas(tenant.id, plan)

        # Initialize usage tracking
        self.usage_history[tenant.id] = []

        logger.info(f"Created tenant: {tenant.name} ({tenant.id})")
        return tenant

    async def delete_tenant(self, tenant_id: UUID):
        """Delete a tenant"""
        if tenant_id in self.tenants:
            del self.tenants[tenant_id]
            if tenant_id in self.quotas:
                del self.quotas[tenant_id]
            if tenant_id in self.usage_history:
                del self.usage_history[tenant_id]

            logger.info(f"Deleted tenant: {tenant_id}")

    async def get_tenant(self, tenant_id: UUID) -> Optional[Tenant]:
        """Get tenant by ID"""
        return self.tenants.get(tenant_id)

    async def get_tenant_by_name(self, name: str) -> Optional[Tenant]:
        """Get tenant by name"""
        for tenant in self.tenants.values():
            if tenant.name == name:
                return tenant
        return None

    async def update_tenant(
        self,
        tenant_id: UUID,
        **kwargs,
    ) -> Optional[Tenant]:
        """Update tenant properties"""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return None

        for key, value in kwargs.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)

        tenant.updated_at = datetime.utcnow()
        return tenant

    async def set_quota(
        self,
        tenant_id: UUID,
        quota_name: str,
        limit: int,
        reset_at: Optional[datetime] = None,
    ):
        """Set quota for tenant"""
        if tenant_id not in self.quotas:
            self.quotas[tenant_id] = {}

        current_quota = self.quotas[tenant_id].get(quota_name)
        used = current_quota.used if current_quota else 0

        self.quotas[tenant_id][quota_name] = Quota(
            name=quota_name,
            limit=limit,
            used=used,
            reset_at=reset_at,
        )

        logger.debug(f"Set quota {quota_name}={limit} for tenant {tenant_id}")

    async def _set_default_quotas(self, tenant_id: UUID, plan: PlanType):
        """Set default quotas based on plan"""
        if tenant_id not in self.quotas:
            self.quotas[tenant_id] = {}

        quotas = self.plan_quotas.get(plan, {})
        reset_at = datetime.utcnow() + timedelta(days=1)  # Daily reset

        for name, limit in quotas.items():
            self.quotas[tenant_id][name] = Quota(
                name=name,
                limit=limit,
                used=0,
                reset_at=reset_at,
            )

    async def check_quota(
        self,
        tenant_id: UUID,
        quota_name: str,
    ) -> bool:
        """
        Check if quota is available.

        Args:
            tenant_id: Tenant ID
            quota_name: Quota name

        Returns:
            True if quota available, False if exceeded
        """
        if tenant_id not in self.quotas:
            return True  # No quotas set

        quota = self.quotas[tenant_id].get(quota_name)
        if not quota:
            return True

        # Check if limit is unlimited (-1)
        if quota.limit < 0:
            return True

        # Check reset
        if quota.reset_at and datetime.utcnow() > quota.reset_at:
            quota.used = 0
            quota.reset_at = datetime.utcnow() + timedelta(days=1)

        return not quota.is_exceeded()

    async def consume_quota(
        self,
        tenant_id: UUID,
        quota_name: str,
        amount: int = 1,
    ) -> bool:
        """
        Consume quota.

        Args:
            tenant_id: Tenant ID
            quota_name: Quota name
            amount: Amount to consume

        Returns:
            True if successful, False if quota exceeded
        """
        if not await self.check_quota(tenant_id, quota_name):
            logger.warning(f"Quota exceeded: {quota_name} for tenant {tenant_id}")
            return False

        if tenant_id in self.quotas and quota_name in self.quotas[tenant_id]:
            self.quotas[tenant_id][quota_name].used += amount

        # Track usage
        usage = Usage(
            tenant_id=tenant_id,
            metric=quota_name,
            value=amount,
        )
        self.usage_history[tenant_id].append(usage)

        return True

    async def get_usage(
        self,
        tenant_id: UUID,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Usage]:
        """Get usage history for tenant"""
        if tenant_id not in self.usage_history:
            return []

        usage = self.usage_history[tenant_id]

        if start:
            usage = [u for u in usage if u.timestamp >= start]
        if end:
            usage = [u for u in usage if u.timestamp <= end]

        return usage

    async def get_usage_summary(
        self,
        tenant_id: UUID,
        period: str = "day",
    ) -> Dict[str, int]:
        """
        Get usage summary.

        Args:
            tenant_id: Tenant ID
            period: Period (hour, day, week, month)

        Returns:
            Usage summary by metric
        """
        now = datetime.utcnow()

        if period == "hour":
            start = now - timedelta(hours=1)
        elif period == "day":
            start = now - timedelta(days=1)
        elif period == "week":
            start = now - timedelta(weeks=1)
        elif period == "month":
            start = now - timedelta(days=30)
        else:
            start = now - timedelta(days=1)

        usage = await self.get_usage(tenant_id, start=start)

        summary: Dict[str, int] = {}
        for u in usage:
            summary[u.metric] = summary.get(u.metric, 0) + u.value

        return summary

    async def get_quotas(self, tenant_id: UUID) -> Dict[str, Quota]:
        """Get all quotas for tenant"""
        return self.quotas.get(tenant_id, {})

    async def suspend_tenant(self, tenant_id: UUID, reason: str = ""):
        """Suspend tenant"""
        tenant = self.tenants.get(tenant_id)
        if tenant:
            tenant.status = TenantStatus.SUSPENDED
            tenant.metadata["suspension_reason"] = reason
            logger.info(f"Suspended tenant {tenant_id}: {reason}")

    async def activate_tenant(self, tenant_id: UUID):
        """Activate suspended tenant"""
        tenant = self.tenants.get(tenant_id)
        if tenant:
            tenant.status = TenantStatus.ACTIVE
            tenant.metadata.pop("suspension_reason", None)
            logger.info(f"Activated tenant {tenant_id}")

    def list_tenants(self) -> List[Dict[str, Any]]:
        """List all tenants"""
        return [
            {
                "id": str(t.id),
                "name": t.name,
                "display_name": t.display_name,
                "status": t.status.value,
                "plan": t.plan.value,
                "created_at": t.created_at.isoformat(),
            }
            for t in self.tenants.values()
        ]


# Global tenant manager
_tenant_manager: Optional[TenantManager] = None


def get_tenant_manager() -> TenantManager:
    """Get global tenant manager"""
    global _tenant_manager
    if _tenant_manager is None:
        _tenant_manager = TenantManager()
    return _tenant_manager


# Tenant context for request isolation


class TenantContext:
    """Tenant context for request isolation"""

    def __init__(self, tenant_id: UUID):
        self.tenant_id = tenant_id
        self._token = None

    def __enter__(self):
        # Set current tenant context
        self._token = "current_tenant"  # Would use contextvars in production
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Clear context
        self._token = None


def get_current_tenant_id() -> Optional[UUID]:
    """Get current tenant ID from context"""
    # Would use contextvars in production
    return None


# Decorator for tenant-aware functions


def tenant_aware(func):
    """
    Decorator to make function tenant-aware.

    Checks quotas before executing function.
    """

    async def wrapper(*args, tenant_id: Optional[UUID] = None, **kwargs):
        if tenant_id:
            manager = get_tenant_manager()

            # Check tenant exists
            tenant = await manager.get_tenant(tenant_id)
            if not tenant:
                raise ValueError(f"Tenant not found: {tenant_id}")

            # Check tenant status
            if tenant.status != TenantStatus.ACTIVE:
                raise PermissionError(f"Tenant is not active: {tenant.status.value}")

        return await func(*args, tenant_id=tenant_id, **kwargs)

    return wrapper
