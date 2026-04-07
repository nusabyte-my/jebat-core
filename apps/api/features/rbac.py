"""
Advanced RBAC Module — Q2 2027: Role-Based Access Control

Provides fine-grained role-based access control for JEBAT.
Supports custom roles, permissions, resource-level access, and audit integration.
"""

import os
import json
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class Permission(str, Enum):
    """All possible permissions in JEBAT."""
    # Memory
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    MEMORY_DELETE = "memory:delete"
    MEMORY_EXPORT = "memory:export"
    
    # Agents
    AGENT_EXECUTE = "agent:execute"
    AGENT_SPAWN = "agent:spawn"
    AGENT_CONFIGURE = "agent:configure"
    
    # Security
    SECURITY_SCAN = "security:scan"
    SECURITY_FIX = "security:fix"
    SECURITY_REPORT = "security:report"
    
    # Admin
    ADMIN_USERS = "admin:users"
    ADMIN_ROLES = "admin:roles"
    ADMIN_CONFIG = "admin:config"
    ADMIN_AUDIT = "admin:audit"
    
    # API
    API_READ = "api:read"
    API_WRITE = "api:write"
    API_ADMIN = "api:admin"
    
    # Voice
    VOICE_TRANSCRIBE = "voice:transcribe"
    VOICE_SYNTHESIZE = "voice:synthesize"
    
    # Knowledge Graph
    KG_READ = "kg:read"
    KG_WRITE = "kg:write"


class RoleType(str, Enum):
    """Built-in role types."""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    OPERATOR = "operator"
    DEVELOPER = "developer"
    ANALYST = "analyst"
    AUDITOR = "auditor"
    VIEWER = "viewer"


@dataclass
class Role:
    """Represents a role with permissions."""
    id: str
    name: str
    description: str
    permissions: list[str]
    is_system: bool = False  # System roles can't be deleted
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class User:
    """Represents a user with assigned roles."""
    id: str
    username: str
    email: str
    roles: list[str]  # Role IDs
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_login: str = ""


# ─── Built-in Roles ───────────────────────────────────────────────────────────

BUILTIN_ROLES: dict[str, Role] = {
    RoleType.SUPER_ADMIN: Role(
        id="super_admin",
        name="Super Admin",
        description="Full system access, cannot be restricted",
        permissions=[p.value for p in Permission],
        is_system=True,
    ),
    RoleType.ADMIN: Role(
        id="admin",
        name="Admin",
        description="Administrative access, no super-admin privileges",
        permissions=[
            Permission.MEMORY_READ.value, Permission.MEMORY_WRITE.value, Permission.MEMORY_DELETE.value,
            Permission.AGENT_EXECUTE.value, Permission.AGENT_SPAWN.value, Permission.AGENT_CONFIGURE.value,
            Permission.SECURITY_SCAN.value, Permission.SECURITY_FIX.value, Permission.SECURITY_REPORT.value,
            Permission.ADMIN_USERS.value, Permission.ADMIN_CONFIG.value,
            Permission.API_READ.value, Permission.API_WRITE.value,
            Permission.VOICE_TRANSCRIBE.value, Permission.VOICE_SYNTHESIZE.value,
            Permission.KG_READ.value, Permission.KG_WRITE.value,
        ],
        is_system=True,
    ),
    RoleType.OPERATOR: Role(
        id="operator",
        name="Operator",
        description="Can execute agents and use core features",
        permissions=[
            Permission.MEMORY_READ.value, Permission.MEMORY_WRITE.value,
            Permission.AGENT_EXECUTE.value, Permission.AGENT_SPAWN.value,
            Permission.SECURITY_SCAN.value,
            Permission.API_READ.value, Permission.API_WRITE.value,
            Permission.VOICE_TRANSCRIBE.value, Permission.VOICE_SYNTHESIZE.value,
            Permission.KG_READ.value,
        ],
        is_system=True,
    ),
    RoleType.DEVELOPER: Role(
        id="developer",
        name="Developer",
        description="Can develop and test, no production access",
        permissions=[
            Permission.MEMORY_READ.value, Permission.MEMORY_WRITE.value,
            Permission.AGENT_EXECUTE.value,
            Permission.API_READ.value, Permission.API_WRITE.value,
            Permission.KG_READ.value, Permission.KG_WRITE.value,
        ],
        is_system=True,
    ),
    RoleType.ANALYST: Role(
        id="analyst",
        name="Analyst",
        description="Can read data and generate reports",
        permissions=[
            Permission.MEMORY_READ.value,
            Permission.SECURITY_SCAN.value, Permission.SECURITY_REPORT.value,
            Permission.API_READ.value,
            Permission.KG_READ.value,
        ],
        is_system=True,
    ),
    RoleType.AUDITOR: Role(
        id="auditor",
        name="Auditor",
        description="Read-only access to audit logs and reports",
        permissions=[
            Permission.MEMORY_READ.value,
            Permission.SECURITY_REPORT.value,
            Permission.ADMIN_AUDIT.value,
            Permission.API_READ.value,
            Permission.KG_READ.value,
        ],
        is_system=True,
    ),
    RoleType.VIEWER: Role(
        id="viewer",
        name="Viewer",
        description="Read-only access to non-sensitive data",
        permissions=[
            Permission.MEMORY_READ.value,
            Permission.API_READ.value,
        ],
        is_system=True,
    ),
}


class RBACManager:
    """
    Role-Based Access Control manager for JEBAT.
    
    Manages users, roles, and permission checks.
    Supports custom roles beyond the built-in ones.
    """
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(os.getcwd(), "security", "rbac")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self._roles: dict[str, Role] = dict(BUILTIN_ROLES)
        self._users: dict[str, User] = {}
        
        self._load_from_disk()
    
    def _load_from_disk(self):
        """Load roles and users from disk."""
        roles_file = os.path.join(self.data_dir, "roles.json")
        if os.path.exists(roles_file):
            with open(roles_file) as f:
                data = json.load(f)
                for role_data in data:
                    role = Role(**role_data)
                    if not role.is_system:
                        self._roles[role.id] = role
        
        users_file = os.path.join(self.data_dir, "users.json")
        if os.path.exists(users_file):
            with open(users_file) as f:
                data = json.load(f)
                for user_data in data:
                    user = User(**user_data)
                    self._users[user.id] = user
    
    def _save_to_disk(self):
        """Save roles and users to disk."""
        roles_file = os.path.join(self.data_dir, "roles.json")
        with open(roles_file, "w") as f:
            json.dump([r.__dict__ for r in self._roles.values() if not r.is_system], f, indent=2)
        
        users_file = os.path.join(self.data_dir, "users.json")
        with open(users_file, "w") as f:
            json.dump([u.__dict__ for u in self._users.values()], f, indent=2)
    
    def add_user(self, user: User):
        """Add a user."""
        self._users[user.id] = user
        self._save_to_disk()
    
    def remove_user(self, user_id: str):
        """Remove a user."""
        if user_id in self._users:
            del self._users[user_id]
            self._save_to_disk()
    
    def add_role(self, role: Role):
        """Add a custom role."""
        if role.is_system:
            raise ValueError("Cannot modify system roles")
        self._roles[role.id] = role
        self._save_to_disk()
    
    def assign_role(self, user_id: str, role_id: str):
        """Assign a role to a user."""
        if user_id not in self._users:
            raise ValueError(f"User {user_id} not found")
        if role_id not in self._roles:
            raise ValueError(f"Role {role_id} not found")
        
        user = self._users[user_id]
        if role_id not in user.roles:
            user.roles.append(role_id)
            self._save_to_disk()
    
    def remove_role(self, user_id: str, role_id: str):
        """Remove a role from a user."""
        if user_id in self._users:
            user = self._users[user_id]
            if role_id in user.roles:
                user.roles.remove(role_id)
                self._save_to_disk()
    
    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if a user has a specific permission."""
        if user_id not in self._users:
            return False
        
        user = self._users[user_id]
        if not user.is_active:
            return False
        
        for role_id in user.roles:
            if role_id in self._roles:
                role = self._roles[role_id]
                if permission.value in role.permissions:
                    return True
        
        return False
    
    def get_user_permissions(self, user_id: str) -> list[str]:
        """Get all permissions for a user."""
        if user_id not in self._users:
            return []
        
        permissions = set()
        for role_id in self._users[user_id].roles:
            if role_id in self._roles:
                permissions.update(self._roles[role_id].permissions)
        
        return sorted(permissions)
    
    def get_all_roles(self) -> list[Role]:
        """Get all roles."""
        return list(self._roles.values())
    
    def get_all_users(self) -> list[User]:
        """Get all users."""
        return list(self._users.values())


# ─── FastAPI Integration ───────────────────────────────────────────────────────

def create_permission_checker(rbac: RBACManager, required_permission: Permission):
    """Create a FastAPI dependency for permission checking."""
    from fastapi import HTTPException, Depends
    
    async def check_permission(user_id: str):
        if not rbac.has_permission(user_id, required_permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {required_permission.value}"
            )
        return user_id
    
    return check_permission
