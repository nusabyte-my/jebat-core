"""Enterprise RBAC — Role-Based Access Control for JEBAT Platform."""

from .models import (
    ResourceType, Action, Scope,
    RoleCreate, RoleUpdate, RoleResponse,
    OrgCreate, OrgUpdate, OrgResponse,
    TeamCreate, TeamUpdate, TeamResponse,
    TeamMemberAdd, TeamMemberUpdate, TeamMemberResponse,
    ProjectCreate, ProjectUpdate, ProjectResponse,
    ProjectMemberAdd, ProjectMemberUpdate, ProjectMemberResponse,
    RoleAssignRequest, AuditLogEntryResponse, EffectivePermissionsResponse,
    ServiceAccountCreate, ServiceAccountUpdate, ServiceAccountResponse,
    ServiceAccountKeyCreate, ServiceAccountKeyResponse,
    SSOConfigCreate, SSOConfigUpdate, SSOConfigResponse, SSOTestResponse,
    check_permission, resolve_effective_permissions, DEFAULT_ROLES,
)

from .api import router

__all__ = [
    # Enums
    "ResourceType", "Action", "Scope",
    # Roles
    "RoleCreate", "RoleUpdate", "RoleResponse",
    # Orgs
    "OrgCreate", "OrgUpdate", "OrgResponse",
    # Teams
    "TeamCreate", "TeamUpdate", "TeamResponse",
    "TeamMemberAdd", "TeamMemberUpdate", "TeamMemberResponse",
    # Projects
    "ProjectCreate", "ProjectUpdate", "ProjectResponse",
    "ProjectMemberAdd", "ProjectMemberUpdate", "ProjectMemberResponse",
    # RBAC
    "RoleAssignRequest", "AuditLogEntryResponse", "EffectivePermissionsResponse",
    # Service Accounts
    "ServiceAccountCreate", "ServiceAccountUpdate", "ServiceAccountResponse",
    "ServiceAccountKeyCreate", "ServiceAccountKeyResponse",
    # SSO
    "SSOConfigCreate", "SSOConfigUpdate", "SSOConfigResponse", "SSOTestResponse",
    # Permissions
    "check_permission", "resolve_effective_permissions", "DEFAULT_ROLES",
    # API
    "router",
]