"""
Tests for RBAC (Role-Based Access Control) - Phase 6.
Tests cover permissions, roles, caching, and role assignment.
"""

import pytest
import sys
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from main import app
from rbac import (
    has_permission, check_permissions, cache_user_permissions,
    get_cached_permissions, clear_user_cache, clear_all_cache,
    validate_permission_format, validate_role_name,
    parse_permission, check_admin_permission,
    get_default_permissions_list, get_default_roles_dict,
    build_permission_from_parts
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


# ============================================================================
# Permission Checking Tests
# ============================================================================

class TestPermissionChecking:
    """Tests for permission checking logic."""

    def test_has_permission_exact_match(self):
        """Test permission check with exact match."""
        permissions = {"read:queries", "write:sessions"}
        assert has_permission(permissions, "read:queries") is True

    def test_has_permission_not_present(self):
        """Test permission check when permission not present."""
        permissions = {"read:queries", "write:sessions"}
        assert has_permission(permissions, "admin:users") is False

    def test_has_permission_wildcard_match(self):
        """Test permission check with wildcard."""
        permissions = {"admin:*", "read:queries"}
        assert has_permission(permissions, "admin:users") is True
        assert has_permission(permissions, "admin:roles") is True

    def test_has_permission_wildcard_no_match(self):
        """Test wildcard doesn't match different prefix."""
        permissions = {"admin:*"}
        assert has_permission(permissions, "read:queries") is False

    def test_check_permissions_all_present(self):
        """Test checking multiple permissions (all required)."""
        permissions = {"read:queries", "write:sessions", "admin:users"}
        required = ["read:queries", "write:sessions"]
        assert check_permissions(permissions, required, require_all=True) is True

    def test_check_permissions_missing_one(self):
        """Test check fails when one permission missing."""
        permissions = {"read:queries", "write:sessions"}
        required = ["read:queries", "admin:users"]
        assert check_permissions(permissions, required, require_all=True) is False

    def test_check_permissions_any_present(self):
        """Test checking permissions (any required)."""
        permissions = {"read:queries"}
        required = ["read:queries", "admin:users"]
        assert check_permissions(permissions, required, require_all=False) is True

    def test_check_permissions_none_present(self):
        """Test check fails when no permissions present."""
        permissions = {"read:queries"}
        required = ["admin:users", "admin:roles"]
        assert check_permissions(permissions, required, require_all=False) is False

    def test_check_permissions_empty_required(self):
        """Test check with no required permissions."""
        permissions = {"read:queries"}
        assert check_permissions(permissions, [], require_all=True) is True


# ============================================================================
# Permission Validation Tests
# ============================================================================

class TestPermissionValidation:
    """Tests for permission format validation."""

    def test_validate_permission_format_valid(self):
        """Test valid permission format."""
        assert validate_permission_format("read:queries") is True
        assert validate_permission_format("admin:*") is True
        assert validate_permission_format("write:sessions") is True

    def test_validate_permission_format_no_colon(self):
        """Test rejects permission without colon."""
        assert validate_permission_format("readqueries") is False

    def test_validate_permission_format_empty_parts(self):
        """Test rejects permission with empty parts."""
        assert validate_permission_format(":queries") is False
        assert validate_permission_format("read:") is False

    def test_validate_permission_format_invalid_chars(self):
        """Test rejects permission with invalid characters."""
        assert validate_permission_format("read@queries") is False
        assert validate_permission_format("read:quer$es") is False

    def test_validate_permission_format_empty_string(self):
        """Test rejects empty permission."""
        assert validate_permission_format("") is False

    def test_validate_permission_format_none(self):
        """Test rejects None."""
        assert validate_permission_format(None) is False

    def test_parse_permission_valid(self):
        """Test parsing valid permission."""
        resource, action = parse_permission("read:queries")
        assert resource == "queries"
        assert action == "read"

    def test_parse_permission_wildcard(self):
        """Test parsing wildcard permission."""
        resource, action = parse_permission("admin:*")
        assert resource == "*"
        assert action == "admin"

    def test_parse_permission_invalid(self):
        """Test parsing invalid permission."""
        resource, action = parse_permission("invalid")
        assert resource is None
        assert action is None


# ============================================================================
# Role Name Validation Tests
# ============================================================================

class TestRoleNameValidation:
    """Tests for role name validation."""

    def test_validate_role_name_valid(self):
        """Test valid role names."""
        assert validate_role_name("user") is True
        assert validate_role_name("admin") is True
        assert validate_role_name("custom_role") is True
        assert validate_role_name("viewer123") is True

    def test_validate_role_name_uppercase(self):
        """Test rejects uppercase in role names."""
        assert validate_role_name("User") is False
        assert validate_role_name("ADMIN") is False

    def test_validate_role_name_special_chars(self):
        """Test rejects special characters."""
        assert validate_role_name("role@name") is False
        assert validate_role_name("role-name") is False

    def test_validate_role_name_too_long(self):
        """Test rejects names over max length."""
        long_name = "a" * 51
        assert validate_role_name(long_name) is False

    def test_validate_role_name_empty(self):
        """Test rejects empty name."""
        assert validate_role_name("") is False

    def test_validate_role_name_spaces(self):
        """Test rejects spaces in role names."""
        assert validate_role_name("role name") is False


# ============================================================================
# Permission Caching Tests
# ============================================================================

class TestPermissionCaching:
    """Tests for permission caching."""

    def test_cache_user_permissions(self):
        """Test caching user permissions."""
        permissions = {"read:queries", "write:sessions"}
        cache_user_permissions("user123", permissions)
        cached = get_cached_permissions("user123")
        assert cached == permissions

    def test_cache_user_permissions_custom_ttl(self):
        """Test caching with custom TTL."""
        permissions = {"admin:*"}
        cache_user_permissions("user456", permissions, ttl_seconds=60)
        cached = get_cached_permissions("user456")
        assert cached == permissions

    def test_get_cached_permissions_not_cached(self):
        """Test getting non-existent cached permissions."""
        result = get_cached_permissions("nonexistent_user")
        assert result is None

    def test_clear_user_cache(self):
        """Test clearing specific user cache."""
        permissions = {"read:queries"}
        cache_user_permissions("user789", permissions)
        assert get_cached_permissions("user789") is not None
        clear_user_cache("user789")
        assert get_cached_permissions("user789") is None

    def test_clear_all_cache(self):
        """Test clearing entire cache."""
        cache_user_permissions("user1", {"read:queries"})
        cache_user_permissions("user2", {"admin:*"})
        clear_all_cache()
        assert get_cached_permissions("user1") is None
        assert get_cached_permissions("user2") is None


# ============================================================================
# Admin Permission Tests
# ============================================================================

class TestAdminPermissions:
    """Tests for admin permission checks."""

    def test_check_admin_permission_has_admin(self):
        """Test admin permission check with admin user."""
        permissions = {"admin:*", "read:queries"}
        assert check_admin_permission(permissions) is True

    def test_check_admin_permission_no_admin(self):
        """Test admin permission check without admin permission."""
        permissions = {"read:queries", "write:sessions"}
        assert check_admin_permission(permissions) is False

    def test_check_admin_permission_empty(self):
        """Test admin permission check with empty permissions."""
        permissions = set()
        assert check_admin_permission(permissions) is False


# ============================================================================
# Default RBAC Tests
# ============================================================================

class TestDefaultRBAC:
    """Tests for default permissions and roles."""

    def test_get_default_permissions_list(self):
        """Test getting default permissions."""
        perms = get_default_permissions_list()
        assert perms is not None
        assert isinstance(perms, list)
        assert len(perms) > 0
        # Each permission should be a tuple
        for perm in perms:
            assert isinstance(perm, tuple)
            assert len(perm) == 4  # name, resource, action, description

    def test_default_permissions_have_required_names(self):
        """Test default permissions include expected names."""
        perms = get_default_permissions_list()
        perm_names = [p[0] for p in perms]
        assert "read:queries" in perm_names
        assert "write:queries" in perm_names
        assert "admin:users" in perm_names

    def test_get_default_roles_dict(self):
        """Test getting default roles."""
        roles = get_default_roles_dict()
        assert roles is not None
        assert isinstance(roles, dict)
        assert len(roles) > 0

    def test_default_roles_have_required_roles(self):
        """Test default roles include expected roles."""
        roles = get_default_roles_dict()
        assert "user" in roles
        assert "admin" in roles
        assert "viewer" in roles

    def test_default_user_role_is_default(self):
        """Test that 'user' role is marked as default."""
        roles = get_default_roles_dict()
        assert roles["user"]["is_default"] is True

    def test_default_user_role_has_permissions(self):
        """Test that default user role has permissions."""
        roles = get_default_roles_dict()
        assert "permissions" in roles["user"]
        assert len(roles["user"]["permissions"]) > 0


# ============================================================================
# Permission Building Tests
# ============================================================================

class TestPermissionBuilding:
    """Tests for building permissions from parts."""

    def test_build_permission_from_parts(self):
        """Test building permission from resource and action."""
        perm = build_permission_from_parts("queries", "read")
        assert perm == "read:queries"

    def test_build_permission_wildcard(self):
        """Test building wildcard permission."""
        perm = build_permission_from_parts("admin", "*")
        assert perm == "*:admin"


# ============================================================================
# RBAC Endpoints (Mocked)
# ============================================================================

class TestRBACEndpoints:
    """Tests for RBAC endpoints."""

    def test_list_permissions_requires_auth(self, client):
        """Test permissions endpoint requires authentication."""
        response = client.get("/admin/permissions")
        assert response.status_code in [401, 403]

    def test_create_role_requires_auth(self, client):
        """Test create role endpoint requires authentication."""
        response = client.post("/admin/roles", json={"name": "test", "permission_ids": []})
        assert response.status_code in [401, 403]

    def test_update_role_requires_auth(self, client):
        """Test update role endpoint requires authentication."""
        response = client.patch("/admin/roles/role123", json={"description": "test"})
        assert response.status_code in [401, 403]

    def test_delete_role_requires_auth(self, client):
        """Test delete role endpoint requires authentication."""
        response = client.delete("/admin/roles/role123")
        assert response.status_code in [401, 403]

    def test_assign_role_requires_auth(self, client):
        """Test assign role endpoint requires authentication."""
        response = client.post("/admin/users/user123/roles", json={"role_id": "role123"})
        assert response.status_code in [401, 403]


# ============================================================================
# Edge Cases
# ============================================================================

class TestRBACEdgeCases:
    """Tests for edge cases and error handling."""

    def test_permission_format_multiple_colons(self):
        """Test permission format validation with multiple colons."""
        assert validate_permission_format("read:queries:extra") is False

    def test_permission_format_numbers_allowed(self):
        """Test permission format allows numbers."""
        assert validate_permission_format("read:queries123") is True

    def test_permission_format_underscores_allowed(self):
        """Test permission format allows underscores."""
        assert validate_permission_format("read:my_queries") is True

    def test_role_name_numbers_allowed(self):
        """Test role name allows numbers."""
        assert validate_role_name("role123") is True

    def test_role_name_underscores_allowed(self):
        """Test role name allows underscores."""
        assert validate_role_name("custom_role_name") is True

    def test_cache_same_user_multiple_times(self):
        """Test caching overwrites previous cache."""
        cache_user_permissions("user", {"read:queries"})
        cached1 = get_cached_permissions("user")

        cache_user_permissions("user", {"admin:*"})
        cached2 = get_cached_permissions("user")

        assert cached1 != cached2
        assert "admin:*" in cached2

    def test_parse_permission_with_numbers(self):
        """Test parsing permission with numbers."""
        resource, action = parse_permission("read123:queries456")
        assert resource == "queries456"
        assert action == "read123"
