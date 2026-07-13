"""Enterprise RBAC — Data Models."""

from __future__ import annotations

import uuid
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, EmailStr


class ResourceType(str, Enum):
    ORG = "org"
    TEAM = "team"
    PROJECT = "project"
    CORE = "core"
    SENTINEL = "sentinel"
    DEVSUITE = "devsuite"
    COMPANION = "companion"
    NEXUS = "nexus"
    ADMIN = "admin"
    MCP = "mcp"
    RBAC = "rbac"


class Action(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    MANAGE_MEMBERS = "manage_members"
    MANAGE_BILLING = "manage_billing"
    VIEW_AUDIT = "view_audit"
    MANAGE_SSO = "manage_sso"
    MANAGE_ROLES = "manage_roles"
    MANAGE_PROJECTS = "manage_projects"
    DEPLOY = "deploy"
    MANAGE_SECRETS = "manage_secrets"
    MANAGE_KEYS = "manage_keys"
    CHAT = "chat"
    THINK = "think"
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    AGENT_MANAGE = "agent_manage"
    SCAN = "scan"
    CVE_READ = "cve_read"
    REPORT_READ = "report_read"
    CONFIG_WRITE = "config_write"
    GENERATE = "generate"
    REVIEW = "review"
    SANDBOX_RUN = "sandbox_run"
    IDE_CONFIG = "ide_config"
    BRIEFING = "briefing"
    MEETING = "meeting"
    TASKS = "tasks"
    BOT_MANAGE = "bot_manage"
    CHANNEL_MANAGE = "channel_manage"
    BROADCAST = "broadcast"
    TOOLS_CALL = "tools_call"
    RESOURCES_READ = "resources_read"
    PROMPTS_MANAGE = "prompts_manage"
    KEYS_MANAGE = "keys_manage"
    CONFIG_MANAGE = "config_manage"
    HEALTH_READ = "health_read"
    AUDIT_READ = "audit_read"
    ROLES_MANAGE = "roles_manage"
    ASSIGNMENTS_MANAGE = "assignments_manage"


class Scope(str, Enum):
    ORG = "org"
    TEAM = "team"
    PROJECT = "project"


class RoleOrigin(str, Enum):
    SYSTEM = "system"
    CUSTOM = "custom"


@dataclass
class Permission:
    resource: ResourceType
    action: Action

    def __str__(self) -> str:
        return f"{self.resource.value}:{self.action.value}"

    @classmethod
    def from_string(cls, s: str) -> "Permission":
        resource_str, action_str = s.split(":", 1)
        return cls(ResourceType(resource_str), Action(action_str))


# ─── Built-in Role Definitions ───────────────────────────────────────

DEFAULT_ROLES: dict[str, dict] = {
    "org:owner": {
        "display_name": "Organization Owner",
        "description": "Full organization control",
        "is_system": True,
        "permissions": ["*"],
    },
    "org:admin": {
        "display_name": "Organization Admin",
        "description": "Organization administration",
        "is_system": True,
        "permissions": [
            "org:read", "org:write", "org:manage_members", "org:manage_billing",
            "org:view_audit", "org:manage_sso", "org:manage_roles",
            "team:*", "project:*", "admin:*",
        ],
    },
    "org:billing_admin": {
        "display_name": "Billing Admin",
        "description": "Billing only access",
        "is_system": True,
        "permissions": ["org:read", "org:manage_billing", "org:view_audit"],
    },
    "org:auditor": {
        "display_name": "Auditor",
        "description": "Read-only audit access",
        "is_system": True,
        "permissions": ["org:read", "org:view_audit", "admin:health_read", "admin:audit_read"],
    },
    "team:lead": {
        "display_name": "Team Lead",
        "description": "Team leadership",
        "is_system": True,
        "permissions": [
            "team:read", "team:write", "team:manage_members", "team:manage_projects",
            "project:*", "core:*", "sentinel:*", "devsuite:*", "companion:*", "nexus:*", "mcp:*",
        ],
    },
    "team:member": {
        "display_name": "Team Member",
        "description": "Team contributor",
        "is_system": True,
        "permissions": [
            "team:read",
            "project:read", "project:write", "project:deploy",
            "core:chat", "core:think", "core:memory_read",
            "sentinel:scan", "sentinel:cve_read",
            "devsuite:generate", "devsuite:review", "devsuite:sandbox_run",
            "companion:*", "nexus:bot_manage", "mcp:tools_call",
        ],
    },
    "role:developer": {
        "display_name": "Developer",
        "description": "Application developer",
        "is_system": True,
        "permissions": [
            "project:read", "project:write", "project:deploy", "project:manage_secrets",
            "core:chat", "core:think", "core:memory_read", "core:memory_write",
            "devsuite:*", "mcp:tools_call", "mcp:resources_read",
        ],
    },
    "role:security": {
        "display_name": "Security Analyst",
        "description": "Security operations",
        "is_system": True,
        "permissions": [
            "project:read", "sentinel:*", "core:memory_read", "admin:audit_read",
        ],
    },
    "role:viewer": {
        "display_name": "Viewer",
        "description": "Read-only access",
        "is_system": True,
        "permissions": [
            "project:read", "core:chat", "core:think", "core:memory_read",
            "sentinel:cve_read", "sentinel:report_read",
            "companion:chat", "companion:briefing",
        ],
    },
    "role:service": {
        "display_name": "Service Account",
        "description": "Automation service account",
        "is_system": True,
        "permissions": [
            "core:chat", "core:think", "core:memory_read", "core:memory_write", "core:agent_manage",
            "devsuite:generate", "devsuite:review", "devsuite:sandbox_run",
            "mcp:tools_call", "mcp:resources_read", "mcp:prompts_manage",
        ],
    },
}


# ─── Pydantic Models for API ─────────────────────────────────────────

class RoleBase(BaseModel):
    name: str = Field(..., pattern=r"^[a-z0-9:_-]+$", max_length=64)
    display_name: str = Field(..., max_length=128)
    description: str = Field(default="", max_length=512)
    is_system: bool = False


class RoleCreate(RoleBase):
    permissions: list[str] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=128)
    description: str | None = Field(default=None, max_length=512)
    permissions: list[str] | None = None


class RoleResponse(RoleBase):
    id: str
    permissions: list[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrgBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    slug: str = Field(..., pattern=r"^[a-z0-9-]+$", max_length=64)
    billing_email: EmailStr | None = None


class OrgCreate(OrgBase):
    pass


class OrgUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    billing_email: EmailStr | None = None


class OrgResponse(OrgBase):
    id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TeamBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    slug: str = Field(..., pattern=r"^[a-z0-9-]+$", max_length=64)
    description: str = Field(default="", max_length=512)


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=512)


class TeamMemberBase(BaseModel):
    user_id: str
    role: str = Field(..., pattern=r"^(lead|member)$")


class TeamMemberAdd(TeamMemberBase):
    pass


class TeamMemberUpdate(BaseModel):
    role: str | None = Field(default=None, pattern=r"^(lead|member)$")


class TeamMemberResponse(BaseModel):
    id: str
    team_id: str
    user_id: str
    role: str
    joined_at: datetime
    invited_by: str | None = None

    class Config:
        from_attributes = True


class TeamResponse(TeamBase):
    id: str
    org_id: str
    member_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    slug: str = Field(..., pattern=r"^[a-z0-9-]+$", max_length=64)
    description: str = Field(default="", max_length=512)
    environment: str = Field(default="development", pattern=r"^(development|staging|production)$")


class ProjectCreate(ProjectBase):
    team_id: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=512)
    environment: str | None = Field(default=None, pattern=r"^(development|staging|production)$")


class ProjectMemberBase(BaseModel):
    user_id: str
    role: str = Field(..., pattern=r"^(owner|admin|developer|viewer)$")


class ProjectMemberAdd(ProjectMemberBase):
    pass


class ProjectMemberUpdate(BaseModel):
    role: str | None = Field(default=None, pattern=r"^(owner|admin|developer|viewer)$")


class ProjectMemberResponse(BaseModel):
    id: str
    project_id: str
    user_id: str
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class ProjectResponse(ProjectBase):
    id: str
    org_id: str
    team_id: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoleAssignRequest(BaseModel):
    user_id: str
    role: str
    scope: Scope
    scope_id: str | None = None
    expires_at: datetime | None = None


class AuditLogEntryResponse(BaseModel):
    id: str
    timestamp: datetime
    actor: dict[str, str]
    action: str
    resource: dict[str, str]
    outcome: str
    severity: str
    metadata: dict[str, Any]

    class Config:
        from_attributes = True


class ServiceAccountBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(default="", max_length=512)
    role: str = Field(default="role:service")
    expires_in_days: int | None = Field(default=None, ge=1, le=3650)


class ServiceAccountCreate(ServiceAccountBase):
    pass


class ServiceAccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=512)
    is_active: bool | None = None


class ServiceAccountResponse(BaseModel):
    id: str
    org_id: str
    name: str
    description: str
    role: str
    created_by: str
    created_at: datetime
    last_used_at: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool

    class Config:
        from_attributes = True


class ServiceAccountKeyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    expires_in_days: int | None = Field(default=None, ge=1, le=3650)
    ip_allowlist: list[str] = Field(default_factory=list)
    allowed_paths: list[str] = Field(default_factory=list)


class ServiceAccountKeyCreate(ServiceAccountKeyBase):
    pass


class ServiceAccountKeyResponse(BaseModel):
    id: str
    name: str
    key: str  # Only shown once!
    prefix: str
    created_at: datetime
    last_used_at: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool
    ip_allowlist: list[str] = Field(default_factory=list)
    allowed_paths: list[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class SSOConfigBase(BaseModel):
    provider: str = Field(..., pattern=r"^(oidc|saml|ldap)$")
    config: dict[str, Any]
    auto_provision: bool = True
    default_role: str = "role:viewer"
    group_mapping: dict[str, str] = Field(default_factory=dict)


class SSOConfigCreate(SSOConfigBase):
    pass


class SSOConfigUpdate(BaseModel):
    config: dict[str, Any] | None = None
    auto_provision: bool | None = None
    default_role: str | None = None
    group_mapping: dict[str, str] | None = None
    is_enabled: bool | None = None


class SSOConfigResponse(SSOConfigBase):
    id: str
    org_id: str
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SSOTestResponse(BaseModel):
    success: bool
    user_info: dict[str, Any] | None = None
    error: str | None = None


class EffectivePermissionsResponse(BaseModel):
    permissions: list[str]
    roles: list[str]


# ─── Permission Resolution Helpers ───────────────────────────────────

def expand_permissions(perms: list[str]) -> set[str]:
    """Expand wildcard permissions (e.g., 'team:*' -> all team permissions)."""
    expanded = set()
    for perm in perms:
        if perm == "*":
            # All permissions
            for rt in ResourceType:
                for act in Action:
                    expanded.add(f"{rt.value}:{act.value}")
        elif perm.endswith(":*"):
            resource = perm[:-2]
            for act in Action:
                expanded.add(f"{resource}:{act.value}")
        else:
            expanded.add(perm)
    return expanded


def resolve_effective_permissions(
    direct_perms: list[str],
    team_roles: list[str],
    project_roles: list[str],
    service_account_roles: list[str],
) -> set[str]:
    """Resolve all effective permissions from all sources."""
    all_perms = set()

    # Direct role assignments
    for role_name in direct_perms:
        if role_name in DEFAULT_ROLES:
            all_perms.update(expand_permissions(DEFAULT_ROLES[role_name]["permissions"]))

    # Team memberships
    for team_role in team_roles:
        if team_role in DEFAULT_ROLES:
            all_perms.update(expand_permissions(DEFAULT_ROLES[team_role]["permissions"]))

    # Project memberships
    for project_role in project_roles:
        if project_role in DEFAULT_ROLES:
            all_perms.update(expand_permissions(DEFAULT_ROLES[project_role]["permissions"]))

    # Service account roles
    for sa_role in service_account_roles:
        if sa_role in DEFAULT_ROLES:
            all_perms.update(expand_permissions(DEFAULT_ROLES[sa_role]["permissions"]))

    return all_perms


def check_permission(user_perms: set[str], required: str) -> bool:
    """Check if user has required permission (supports wildcards)."""
    if "*" in user_perms:
        return True
    if required in user_perms:
        return True
    # Check wildcard match
    resource, action = required.split(":", 1)
    if f"{resource}:*" in user_perms:
        return True
    return False