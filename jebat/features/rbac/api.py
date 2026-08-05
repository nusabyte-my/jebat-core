"""Enterprise RBAC — FastAPI Routes."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import EmailStr

from .models import (
    # Enums
    ResourceType, Action, Scope,
    # Roles
    RoleCreate, RoleUpdate, RoleResponse,
    # Orgs
    OrgCreate, OrgUpdate, OrgResponse,
    # Teams
    TeamCreate, TeamUpdate, TeamResponse, TeamMemberAdd, TeamMemberUpdate, TeamMemberResponse,
    # Projects
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectMemberAdd, ProjectMemberUpdate, ProjectMemberResponse,
    # RBAC
    RoleAssignRequest, AuditLogEntryResponse, EffectivePermissionsResponse,
    # Service Accounts
    ServiceAccountCreate, ServiceAccountUpdate, ServiceAccountResponse,
    ServiceAccountKeyCreate, ServiceAccountKeyResponse,
    # SSO
    SSOConfigCreate, SSOConfigUpdate, SSOConfigResponse, SSOTestResponse,
    # Permissions
    check_permission, resolve_effective_permissions,
    # Constants
    DEFAULT_ROLES,
)

router = APIRouter(prefix="/api/v1/rbac", tags=["RBAC"])
security = HTTPBearer()


# ─── Mock User/Org Context (replace with real auth) ──────────────────

async def get_current_user() -> dict:
    """Get current authenticated user. Replace with real auth."""
    return {"id": "user_123", "email": "admin@example.com", "org_id": "org_123", "role": "org:owner"}


async def get_org_id(user: dict = Depends(get_current_user)) -> str:
    return user.get("org_id", "org_123")


async def get_user_permissions(user: dict = Depends(get_current_user), org_id: str = Depends(get_org_id)) -> set[str]:
    """Resolve user's effective permissions. Mock implementation."""
    if user.get("role") == "org:owner":
        return {"*"}
    return {"org:read", "project:read", "core:chat"}


def require_permission(permission: str):
    """Dependency factory for permission checks."""
    async def check(
        user_perms: set[str] = Depends(get_user_permissions),
    ):
        if not check_permission(user_perms, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required permission: {permission}",
            )
    return check


def check_permission(user_perms: set[str], required: str) -> bool:
    """Check if user has required permission (supports wildcards)."""
    if "*" in user_perms:
        return True
    if required in user_perms:
        return True
    resource, action = required.split(":", 1)
    if f"{resource}:*" in user_perms:
        return True
    return False


# ─── Role Management ─────────────────────────────────────────────────

@router.get("/roles", response_model=list[dict], dependencies=[Depends(require_permission("rbac:roles_manage"))])
async def list_roles(org_id: str = Depends(get_org_id)):
    """List all roles in organization (system + custom)."""
    roles = []
    for name, data in DEFAULT_ROLES.items():
        roles.append({
            "id": name,
            "name": name,
            "display_name": data["display_name"],
            "description": data["description"],
            "is_system": data["is_system"],
            "permissions": data["permissions"],
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        })
    return roles


@router.post("/roles", response_model=dict, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("rbac:roles_manage"))])
async def create_role(role: dict, org_id: str = Depends(get_org_id)):
    """Create a custom role."""
    return {
        "id": f"role_{uuid4().hex[:8]}",
        "name": role["name"],
        "display_name": role["display_name"],
        "description": role.get("description", ""),
        "is_system": False,
        "permissions": role.get("permissions", []),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/roles/{role_id}", response_model=dict, dependencies=[Depends(require_permission("rbac:roles_manage"))])
async def get_role(role_id: str, org_id: str = Depends(get_org_id)):
    """Get role by ID."""
    if role_id in DEFAULT_ROLES:
        data = DEFAULT_ROLES[role_id]
        return {
            "id": role_id,
            "name": role_id,
            "display_name": data["display_name"],
            "description": data["description"],
            "is_system": data["is_system"],
            "permissions": data["permissions"],
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
    raise HTTPException(status_code=404, detail="Role not found")


@router.patch("/roles/{role_id}", response_model=dict, dependencies=[Depends(require_permission("rbac:roles_manage"))])
async def update_role(role_id: str, updates: dict, org_id: str = Depends(get_org_id)):
    """Update a custom role (system roles cannot be modified)."""
    if role_id in DEFAULT_ROLES:
        raise HTTPException(status_code=400, detail="Cannot modify system roles")
    return {
        "id": role_id,
        "name": updates.get("name", role_id),
        "display_name": updates.get("display_name", ""),
        "description": updates.get("description", ""),
        "is_system": False,
        "permissions": updates.get("permissions", []),
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }


@router.delete("/roles/{role_id}", dependencies=[Depends(require_permission("rbac:roles_manage"))])
async def delete_role(role_id: str, org_id: str = Depends(get_org_id)):
    """Delete a custom role."""
    if role_id in DEFAULT_ROLES:
        raise HTTPException(status_code=400, detail="Cannot delete system roles")
    return {"deleted": True, "id": role_id}


# ─── Organization Management ─────────────────────────────────────────

@router.post("/orgs", response_model=dict, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("org:manage_members"))])
async def create_org(org: dict, user: dict = Depends(get_current_user)):
    """Create a new organization."""
    return {
        "id": f"org_{uuid4().hex[:8]}",
        "name": org["name"],
        "slug": org["slug"],
        "owner_id": user["id"],
        "created_at": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/orgs/{org_id}", response_model=dict, dependencies=[Depends(require_permission("org:read"))])
async def get_org(org_id: str):
    """Get organization details."""
    return {
        "id": org_id,
        "name": "Acme Corp",
        "slug": "acme",
        "owner_id": "user_123",
        "created_at": "2026-01-01T00:00:00Z",
    }


@router.get("/orgs/{org_id}/members", response_model=list[dict], dependencies=[Depends(require_permission("org:manage_members"))])
async def list_org_members(org_id: str):
    """List organization members with their roles."""
    return [
        {
            "user_id": "user_123",
            "email": "admin@example.com",
            "role": "org:owner",
            "joined_at": "2026-01-01T00:00:00Z",
        }
    ]


@router.post("/orgs/{org_id}/invite", dependencies=[Depends(require_permission("org:manage_members"))])
async def invite_member(org_id: str, invite: dict):
    """Invite a user to the organization."""
    return {
        "invite_id": f"inv_{uuid4().hex[:8]}",
        "email": invite["email"],
        "role": invite["role"],
        "team_id": invite.get("team_id"),
        "status": "pending",
        "expires_at": (datetime.utcnow().replace(day=datetime.utcnow().day + 7)).isoformat() + "Z",
    }


@router.delete("/orgs/{org_id}/members/{user_id}", dependencies=[Depends(require_permission("org:manage_members"))])
async def remove_member(org_id: str, user_id: str):
    """Remove a member from the organization."""
    return {"removed": True, "user_id": user_id}


@router.post("/orgs/{org_id}/members/{user_id}/roles", dependencies=[Depends(require_permission("org:manage_roles"))])
async def assign_role(org_id: str, user_id: str, role: dict):
    """Assign a role to a member."""
    return {
        "user_id": user_id,
        "role": role["role"],
        "scope": role.get("scope", "org"),
        "scope_id": role.get("scope_id"),
        "assigned_at": datetime.utcnow().isoformat() + "Z",
    }


@router.delete("/orgs/{org_id}/members/{user_id}/roles/{role_id}", dependencies=[Depends(require_permission("org:manage_roles"))])
async def unassign_role(org_id: str, user_id: str, role_id: str):
    """Remove a role assignment from a member."""
    return {"unassigned": True, "role_id": role_id}


# ─── Team Management ─────────────────────────────────────────────────

@router.post("/orgs/{org_id}/teams", response_model=dict, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("team:manage_members"))])
async def create_team(org_id: str, team: dict, user: dict = Depends(get_current_user)):
    """Create a new team."""
    return {
        "id": f"team_{uuid4().hex[:8]}",
        "name": team["name"],
        "slug": team["slug"],
        "description": team.get("description", ""),
        "org_id": org_id,
        "member_count": 1,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/orgs/{org_id}/teams", response_model=list[dict], dependencies=[Depends(require_permission("team:read"))])
async def list_teams(org_id: str):
    """List all teams in organization."""
    return [
        {
            "id": "team_123",
            "name": "Platform",
            "slug": "platform",
            "description": "Core platform team",
            "org_id": org_id,
            "member_count": 5,
            "created_at": "2026-01-01T00:00:00Z",
        }
    ]


@router.get("/teams/{team_id}", response_model=dict, dependencies=[Depends(require_permission("team:read"))])
async def get_team(team_id: str):
    return {
        "id": team_id,
        "name": "Platform",
        "slug": "platform",
        "description": "Core platform team",
        "org_id": "org_123",
        "member_count": 5,
        "created_at": "2026-01-01T00:00:00Z",
    }


@router.get("/teams/{team_id}/members", response_model=list[dict], dependencies=[Depends(require_permission("team:read"))])
async def list_team_members(team_id: str):
    return [
        {
            "id": "tm_123",
            "team_id": team_id,
            "user_id": "user_123",
            "role": "lead",
            "joined_at": "2026-01-01T00:00:00Z",
            "invited_by": "admin",
        }
    ]


@router.post("/teams/{team_id}/members", dependencies=[Depends(require_permission("team:manage_members"))])
async def add_team_member(team_id: str, member: dict):
    return {
        "id": f"tm_{uuid4().hex[:8]}",
        "team_id": team_id,
        "user_id": member["user_id"],
        "role": member["role"],
        "joined_at": datetime.utcnow().isoformat() + "Z",
        "invited_by": "current_user",
    }


@router.delete("/teams/{team_id}/members/{user_id}", dependencies=[Depends(require_permission("team:manage_members"))])
async def remove_team_member(team_id: str, user_id: str):
    return {"removed": True, "team_id": team_id, "user_id": user_id}


@router.patch("/teams/{team_id}/members/{user_id}", dependencies=[Depends(require_permission("team:manage_members"))])
async def update_team_member(team_id: str, user_id: str, update: dict):
    return {
        "id": f"tm_{uuid4().hex[:8]}",
        "team_id": team_id,
        "user_id": user_id,
        "role": update["role"],
        "joined_at": "2026-01-01T00:00:00Z",
    }


# ─── Project Management ──────────────────────────────────────────────

@router.post("/orgs/{org_id}/projects", response_model=dict, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("project:write"))])
async def create_project(org_id: str, project: dict):
    return {
        "id": f"proj_{uuid4().hex[:8]}",
        "name": project["name"],
        "slug": project["slug"],
        "description": project.get("description", ""),
        "org_id": org_id,
        "team_id": project.get("team_id"),
        "environment": project.get("environment", "development"),
        "created_at": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/orgs/{org_id}/projects", response_model=list[dict], dependencies=[Depends(require_permission("project:read"))])
async def list_projects(org_id: str):
    return [
        {
            "id": "proj_123",
            "name": "API Gateway",
            "slug": "api-gateway",
            "description": "Main API gateway",
            "org_id": org_id,
            "team_id": "team_123",
            "environment": "production",
            "created_at": "2026-01-01T00:00:00Z",
        }
    ]


@router.get("/projects/{project_id}", response_model=dict, dependencies=[Depends(require_permission("project:read"))])
async def get_project(project_id: str):
    return {
        "id": project_id,
        "name": "API Gateway",
        "slug": "api-gateway",
        "description": "Main API gateway",
        "org_id": "org_123",
        "team_id": "team_123",
        "environment": "production",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }


@router.get("/projects/{project_id}/members", response_model=list[dict], dependencies=[Depends(require_permission("project:read"))])
async def list_project_members(project_id: str):
    return [
        {
            "id": "pm_123",
            "project_id": project_id,
            "user_id": "user_123",
            "role": "owner",
            "joined_at": "2026-01-01T00:00:00Z",
        }
    ]


@router.post("/projects/{project_id}/members", dependencies=[Depends(require_permission("project:manage_members"))])
async def add_project_member(project_id: str, member: dict):
    return {
        "id": f"pm_{uuid4().hex[:8]}",
        "project_id": project_id,
        "user_id": member["user_id"],
        "role": member["role"],
        "joined_at": datetime.utcnow().isoformat() + "Z",
    }


@router.delete("/projects/{project_id}/members/{user_id}", dependencies=[Depends(require_permission("project:manage_members"))])
async def remove_project_member(project_id: str, user_id: str):
    return {"removed": True, "project_id": project_id, "user_id": user_id}


@router.patch("/projects/{project_id}/members/{user_id}", dependencies=[Depends(require_permission("project:manage_members"))])
async def update_project_member(project_id: str, user_id: str, update: dict):
    return {
        "id": f"pm_{uuid4().hex[:8]}",
        "project_id": project_id,
        "user_id": user_id,
        "role": update["role"],
        "joined_at": "2026-01-01T00:00:00Z",
    }


# ─── Role Assignments ────────────────────────────────────────────────

@router.post("/roles/assign", dependencies=[Depends(require_permission("rbac:assignments_manage"))])
async def assign_role(assignment: dict, user: dict = Depends(get_current_user)):
    return {
        "id": f"ra_{uuid4().hex[:8]}",
        "org_id": assignment.get("org_id", "org_123"),
        "user_id": assignment["user_id"],
        "role_id": assignment["role"],
        "scope": assignment.get("scope", "org"),
        "scope_id": assignment.get("scope_id"),
        "assigned_by": user["id"],
        "assigned_at": datetime.utcnow().isoformat() + "Z",
        "expires_at": assignment.get("expires_at"),
    }


@router.delete("/roles/assign/{assignment_id}", dependencies=[Depends(require_permission("rbac:assignments_manage"))])
async def unassign_role(assignment_id: str):
    return {"unassigned": True, "assignment_id": assignment_id}


@router.get("/effective-permissions", response_model=dict, dependencies=[Depends(require_permission("rbac:roles_manage"))])
async def get_effective_permissions(user_id: str = Query(...), org_id: str = Depends(get_org_id)):
    """Get all effective permissions for a user."""
    # Mock implementation
    perms = {"org:read", "project:read", "core:chat"}
    return {"permissions": list(perms)}


# ─── Audit Logs ──────────────────────────────────────────────────────

@router.get("/orgs/{org_id}/audit", response_model=list[dict], dependencies=[Depends(require_permission("org:view_audit"))])
async def list_audit_logs(
    org_id: str,
    user_id: str | None = Query(None),
    action: str | None = Query(None),
    resource: str | None = Query(None),
    resource_id: str | None = Query(None),
    from_date: datetime | None = Query(None),
    to_date: datetime | None = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
):
    """Query audit logs with filters."""
    return [
        {
            "id": f"evt_{uuid4().hex[:8]}",
            "timestamp": "2026-07-11T10:30:00Z",
            "actor": {"type": "user", "id": "user_123", "email": "admin@example.com", "ip": "192.168.1.1"},
            "action": "org.member.invite",
            "resource": {"type": "organization", "id": "org_123", "name": "Acme"},
            "outcome": "success",
            "severity": "info",
            "metadata": {"invited_email": "new@company.com", "role": "team:member"},
        }
    ]


# ─── Service Accounts ────────────────────────────────────────────────

@router.post("/orgs/{org_id}/service-accounts", response_model=dict, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("org:manage_members"))])
async def create_service_account(org_id: str, sa: dict, user: dict = Depends(get_current_user)):
    key = f"jebat_svc_{uuid4().hex[:16]}"
    return {
        "id": f"sa_{uuid4().hex[:8]}",
        "name": sa["name"],
        "description": sa.get("description", ""),
        "org_id": org_id,
        "role": sa.get("role", "role:service"),
        "api_key": key,
        "key_prefix": f"jebat_svc_{uuid4().hex[:8]}_",
        "expires_at": (datetime.utcnow().replace(day=datetime.utcnow().day + 365)).isoformat() + "Z" if sa.get("expires_in_days") else None,
        "created_by": user["id"],
        "created_at": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/service-accounts/{sa_id}", response_model=dict, dependencies=[Depends(require_permission("org:manage_members"))])
async def get_service_account(sa_id: str):
    return {
        "id": sa_id,
        "name": "github-actions",
        "description": "CI/CD service account",
        "org_id": "org_123",
        "role": "role:service",
        "last_used_at": "2026-07-11T10:00:00Z",
        "expires_at": "2027-07-11T00:00:00Z",
        "created_by": "user_123",
        "created_at": "2026-01-01T00:00:00Z",
    }


@router.post("/service-accounts/{sa_id}/keys", response_model=dict, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("org:manage_members"))])
async def create_service_account_key(sa_id: str, key: dict):
    key_value = f"jebat_svc_{uuid4().hex[:24]}"
    return {
        "id": f"sak_{uuid4().hex[:8]}",
        "name": key["name"],
        "key": key_value,
        "prefix": f"jebat_svc_{uuid4().hex[:8]}",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "expires_at": (datetime.utcnow().replace(day=datetime.utcnow().day + 365)).isoformat() + "Z" if key.get("expires_in_days") else None,
        "is_active": True,
        "ip_allowlist": key.get("ip_allowlist", []),
        "allowed_paths": key.get("allowed_paths", []),
    }


@router.delete("/service-accounts/{sa_id}/keys/{key_id}", dependencies=[Depends(require_permission("org:manage_members"))])
async def revoke_service_account_key(sa_id: str, key_id: str):
    return {"revoked": True, "key_id": key_id}


# ─── SSO Configuration ──────────────────────────────────────────────

@router.post("/orgs/{org_id}/sso", response_model=dict, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("org:manage_sso"))])
async def configure_sso(org_id: str, sso: dict):
    return {
        "id": f"sso_{uuid4().hex[:8]}",
        "org_id": org_id,
        "provider": sso["provider"],
        "config": sso["config"],
        "auto_provision": sso.get("auto_provision", True),
        "default_role": sso.get("default_role", "role:viewer"),
        "group_mapping": sso.get("group_mapping", {}),
        "is_enabled": True,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/orgs/{org_id}/sso", response_model=dict, dependencies=[Depends(require_permission("org:manage_sso"))])
async def get_sso_config(org_id: str):
    return {
        "id": "sso_123",
        "org_id": org_id,
        "provider": "oidc",
        "config": {"issuer_url": "https://auth.company.com", "client_id": "jebat"},
        "auto_provision": True,
        "default_role": "role:viewer",
        "group_mapping": {"jebat-admins": "org:admin"},
        "is_enabled": True,
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }


@router.patch("/orgs/{org_id}/sso", dependencies=[Depends(require_permission("org:manage_sso"))])
async def update_sso(org_id: str, updates: dict):
    return {"updated": True, "updated_at": datetime.utcnow().isoformat() + "Z"}


@router.delete("/orgs/{org_id}/sso", dependencies=[Depends(require_permission("org:manage_sso"))])
async def disable_sso(org_id: str):
    return {"disabled": True}


@router.post("/orgs/{org_id}/sso/test", response_model=dict, dependencies=[Depends(require_permission("org:manage_sso"))])
async def test_sso(org_id: str):
    return {
        "success": True,
        "user_info": {"email": "test@company.com", "name": "Test User", "groups": ["jebat-admins"]},
    }


# ─── Built-in Permissions Reference ────────────────────────────────

@router.get("/permissions", response_model=list[dict])
async def list_permissions():
    """List all available permissions."""
    perms = []
    for rt in ResourceType:
        for act in Action:
            perms.append({"resource": rt.value, "action": act.value, "permission": f"{rt.value}:{act.value}"})
    return perms


# ─── Health Check ────────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    return {"status": "healthy", "rbac": "operational"}