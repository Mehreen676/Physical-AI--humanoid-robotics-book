"""
Role-Based Access Control (RBAC) Utilities (Phase 6).
Handles permission checking, caching, and role management.
"""

import logging
from typing import Set, Optional, List, Dict, Tuple
from datetime import datetime, timedelta
from functools import lru_cache

logger = logging.getLogger(__name__)

# Simple in-memory cache for permissions (production should use Redis)
_permission_cache: Dict[str, Tuple[Set[str], datetime]] = {}


# Default permissions for seeding database
DEFAULT_PERMISSIONS = [
    # Query permissions
    ("read:queries", "queries", "read", "View query history and results"),
    ("write:queries", "queries", "write", "Submit new queries"),
    ("delete:queries", "queries", "delete", "Delete queries"),
    # Session permissions
    ("read:sessions", "sessions", "read", "View chat sessions"),
    ("write:sessions", "sessions", "write", "Create and modify sessions"),
    ("delete:sessions", "sessions", "delete", "Delete sessions"),
    # Admin permissions
    ("read:admin_dashboard", "admin", "read", "View admin dashboard"),
    ("write:admin", "admin", "write", "Modify admin settings"),
    ("admin:users", "admin", "admin", "Manage user accounts"),
    ("admin:roles", "admin", "admin", "Manage roles and permissions"),
]

# Default roles for seeding database
DEFAULT_ROLES = {
    "user": {
        "description": "Standard user with access to queries and sessions",
        "is_default": True,
        "permissions": [
            "read:queries",
            "write:queries",
            "read:sessions",
            "write:sessions",
        ],
    },
    "admin": {
        "description": "Administrator with full access",
        "is_default": False,
        "permissions": [
            "read:queries",
            "write:queries",
            "delete:queries",
            "read:sessions",
            "write:sessions",
            "delete:sessions",
            "read:admin_dashboard",
            "write:admin",
            "admin:users",
            "admin:roles",
        ],
    },
    "viewer": {
        "description": "Read-only user for auditing and analytics",
        "is_default": False,
        "permissions": [
            "read:queries",
            "read:sessions",
            "read:admin_dashboard",
        ],
    },
}


def cache_user_permissions(
    user_id: str, permissions: Set[str], ttl_seconds: int = 300
) -> None:
    """
    Cache user permissions in memory.

    Args:
        user_id: User ID to cache
        permissions: Set of permission names
        ttl_seconds: Time-to-live for cache (default 300 = 5 minutes)

    Note:
        Simple in-memory cache; production should use Redis
    """
    expiry = datetime.utcnow() + timedelta(seconds=ttl_seconds)
    _permission_cache[user_id] = (permissions, expiry)


def get_cached_permissions(user_id: str) -> Optional[Set[str]]:
    """
    Get cached user permissions if still valid.

    Args:
        user_id: User ID to lookup

    Returns:
        Optional[Set[str]]: Cached permissions if valid, None if expired or not cached
    """
    if user_id not in _permission_cache:
        return None

    permissions, expiry = _permission_cache[user_id]

    # Check if cache is expired
    if datetime.utcnow() >= expiry:
        del _permission_cache[user_id]
        return None

    return permissions


def clear_user_cache(user_id: str) -> None:
    """
    Clear cached permissions for a user.

    Args:
        user_id: User ID to clear cache for

    Note:
        Call when user roles/permissions are modified
    """
    if user_id in _permission_cache:
        del _permission_cache[user_id]
        logger.info(f"Cleared permission cache for user {user_id}")


def clear_all_cache() -> None:
    """
    Clear entire permission cache.

    Note:
        Call when system roles/permissions are modified
    """
    global _permission_cache
    _permission_cache.clear()
    logger.info("Cleared entire permission cache")


def has_permission(permissions: Set[str], required_permission: str) -> bool:
    """
    Check if a user has a specific permission.

    Args:
        permissions: Set of user permissions
        required_permission: Required permission to check

    Returns:
        bool: True if user has permission, False otherwise

    Note:
        Supports wildcard permissions:
        - "admin:*" includes "admin:users", "admin:roles", etc.
        - "write:*" includes "write:queries", "write:sessions", etc.
    """
    # Exact match
    if required_permission in permissions:
        return True

    # Wildcard match: check if user has wildcard permission
    # Example: user has "admin:*", checking for "admin:users"
    for perm in permissions:
        if perm.endswith("*"):
            prefix = perm[:-1]  # Remove the *
            if required_permission.startswith(prefix):
                return True

    return False


def check_permissions(
    permissions: Set[str], required_permissions: List[str], require_all: bool = True
) -> bool:
    """
    Check if user has all or any of required permissions.

    Args:
        permissions: Set of user permissions
        required_permissions: List of permissions to check
        require_all: True = user must have ALL permissions, False = user must have ANY

    Returns:
        bool: True if permission check passes, False otherwise

    Note:
        Use require_all=True for operations requiring multiple checks
        Use require_all=False for operations where user has alternative paths
    """
    if not required_permissions:
        return True  # No requirements = no access needed

    results = [has_permission(permissions, perm) for perm in required_permissions]

    if require_all:
        return all(results)  # User must have ALL permissions
    else:
        return any(results)  # User must have ANY permission


def validate_permission_format(permission: str) -> bool:
    """
    Validate that a permission string is in valid format.

    Args:
        permission: Permission to validate

    Returns:
        bool: True if valid format, False otherwise

    Note:
        Valid format: "resource:action" or "resource:action*"
        Examples: "read:queries", "admin:*", "write:sessions"
    """
    if not permission or not isinstance(permission, str):
        return False

    # Must contain a colon
    if ":" not in permission:
        return False

    parts = permission.split(":")
    if len(parts) != 2:
        return False

    resource, action = parts

    # Both parts must be non-empty
    if not resource or not action:
        return False

    # Action must be alphanumeric or "*"
    if action != "*" and not action.replace("_", "").isalnum():
        return False

    # Resource must be alphanumeric
    if not resource.replace("_", "").isalnum():
        return False

    return True


def validate_role_name(role_name: str) -> bool:
    """
    Validate that a role name is in valid format.

    Args:
        role_name: Role name to validate

    Returns:
        bool: True if valid format, False otherwise

    Note:
        Role names must be lowercase alphanumeric with underscores
        Examples: "user", "admin", "viewer", "custom_role"
    """
    if not role_name or not isinstance(role_name, str):
        return False

    if len(role_name) < 1 or len(role_name) > 50:
        return False

    # Must be lowercase alphanumeric with underscores
    return role_name.replace("_", "").isalnum() and role_name.islower()


def build_permission_from_parts(resource: str, action: str) -> str:
    """
    Build a permission string from resource and action components.

    Args:
        resource: Resource name (e.g., "queries", "admin")
        action: Action name (e.g., "read", "write", "*")

    Returns:
        str: Formatted permission string (e.g., "read:queries")

    Note:
        Returns "resource:action" format
    """
    return f"{action}:{resource}"


def parse_permission(permission: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse a permission string into resource and action components.

    Args:
        permission: Permission string (e.g., "read:queries")

    Returns:
        Tuple[Optional[str], Optional[str]]: (resource, action) or (None, None) if invalid

    Note:
        Returns "resource" and "action" in that order (action first in string)
    """
    if not validate_permission_format(permission):
        return None, None

    action, resource = permission.split(":", 1)
    return resource, action.rstrip("*")


def check_admin_permission(permissions: Set[str]) -> bool:
    """
    Check if user has any admin permission.

    Args:
        permissions: Set of user permissions

    Returns:
        bool: True if user has any admin permission

    Note:
        Convenient helper for checking admin access
    """
    return has_permission(permissions, "admin:*")


def get_default_permissions_list() -> List[Tuple[str, str, str, str]]:
    """
    Get list of default permissions for seeding database.

    Returns:
        List[Tuple[str, str, str, str]]: List of (name, resource, action, description)
    """
    return DEFAULT_PERMISSIONS


def get_default_roles_dict() -> Dict[str, Dict]:
    """
    Get dictionary of default roles for seeding database.

    Returns:
        Dict[str, Dict]: Dictionary of role definitions
    """
    return DEFAULT_ROLES
