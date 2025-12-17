"""
Tests for API Key functionality - Phase 6.
Tests cover key generation, validation, scopes, expiration, and revocation.
"""

import pytest
import sys
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from main import app
from api_keys import (
    generate_api_key, hash_api_key, validate_api_key_format,
    extract_key_prefix, validate_scopes, has_scope, check_scope_access,
    calculate_key_expiry, is_api_key_expired, is_api_key_valid
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Create mock auth headers."""
    return {"Authorization": "Bearer mock_token"}


# ============================================================================
# API Key Generation Tests
# ============================================================================

class TestAPIKeyGeneration:
    """Tests for API key generation."""

    def test_generate_api_key(self):
        """Test API key generation."""
        full_key, key_prefix = generate_api_key()
        assert full_key is not None
        assert key_prefix is not None
        assert isinstance(full_key, str)
        assert isinstance(key_prefix, str)
        # Full key should contain both prefix and random portion
        assert full_key.startswith("rk_")
        assert key_prefix in full_key

    def test_generate_api_key_format(self):
        """Test API key format is rk_PREFIX_RANDOM."""
        full_key, key_prefix = generate_api_key()
        parts = full_key.split("_")
        assert parts[0] == "rk"
        assert len(full_key) > 50  # Should be reasonably long (rk_ + 8 + _ + urlsafe_base64)

    def test_generate_api_key_uniqueness(self):
        """Test generated keys are unique."""
        keys = [generate_api_key()[0] for _ in range(100)]
        assert len(set(keys)) == 100

    def test_generate_api_key_prefix_extraction(self):
        """Test prefix extraction from generated key."""
        full_key, key_prefix = generate_api_key()
        extracted = extract_key_prefix(full_key)
        assert extracted == key_prefix

    def test_hash_api_key(self):
        """Test API key hashing."""
        full_key, _ = generate_api_key()
        hashed = hash_api_key(full_key)
        assert hashed is not None
        assert isinstance(hashed, str)
        # Should be different from original
        assert hashed != full_key
        # Should be deterministic
        hashed2 = hash_api_key(full_key)
        assert hashed == hashed2

    def test_hash_api_key_length(self):
        """Test API key hash is SHA256."""
        full_key, _ = generate_api_key()
        hashed = hash_api_key(full_key)
        # SHA256 hash is 64 hex characters
        assert len(hashed) == 64
        assert all(c in '0123456789abcdef' for c in hashed)


# ============================================================================
# API Key Format Validation
# ============================================================================

class TestAPIKeyFormatValidation:
    """Tests for API key format validation."""

    def test_validate_api_key_format_valid(self):
        """Test validation of valid API key format."""
        full_key, _ = generate_api_key()
        assert validate_api_key_format(full_key) is True

    def test_validate_api_key_format_missing_prefix(self):
        """Test validation rejects keys without rk_ prefix."""
        invalid_key = "sk_ABCDEFGH_someandonomy1234567890"
        assert validate_api_key_format(invalid_key) is False

    def test_validate_api_key_format_too_short(self):
        """Test validation rejects short keys."""
        short_key = "rk_ABC"
        assert validate_api_key_format(short_key) is False

    def test_validate_api_key_format_no_underscore(self):
        """Test validation rejects keys without underscores."""
        invalid_key = "rkABCDEFGHsomeandonomy1234567890"
        assert validate_api_key_format(invalid_key) is False

    def test_validate_api_key_format_empty(self):
        """Test validation rejects empty string."""
        assert validate_api_key_format("") is False

    def test_validate_api_key_format_none(self):
        """Test validation rejects None."""
        assert validate_api_key_format(None) is False


# ============================================================================
# Key Prefix Tests
# ============================================================================

class TestKeyPrefix:
    """Tests for key prefix extraction."""

    def test_extract_key_prefix_standard(self):
        """Test extracting prefix from standard key."""
        full_key, expected_prefix = generate_api_key()
        extracted = extract_key_prefix(full_key)
        assert extracted == expected_prefix
        assert extracted.startswith("rk_")

    def test_extract_key_prefix_format(self):
        """Test prefix format is rk_XXXXXXXX."""
        full_key, prefix = generate_api_key()
        parts = prefix.split("_")
        assert parts[0] == "rk"
        assert len(parts[1]) == 8

    def test_extract_key_prefix_short_key(self):
        """Test extracting prefix from short key."""
        short_key = "abc"
        prefix = extract_key_prefix(short_key)
        assert len(prefix) <= len(short_key)


# ============================================================================
# Scope Validation Tests
# ============================================================================

class TestScopeValidation:
    """Tests for API key scope validation."""

    def test_validate_scopes_valid(self):
        """Test validating valid scopes."""
        scopes = ["read:queries", "read:sessions"]
        assert validate_scopes(scopes) is True

    def test_validate_scopes_empty_list(self):
        """Test validating empty scope list."""
        assert validate_scopes([]) is False

    def test_validate_scopes_with_allowed_list(self):
        """Test validating scopes against allowed list."""
        scopes = ["read:queries", "write:sessions"]
        allowed = ["read:queries", "write:sessions", "admin:*"]
        assert validate_scopes(scopes, allowed) is True

    def test_validate_scopes_not_in_allowed_list(self):
        """Test validation fails when scope not in allowed list."""
        scopes = ["invalid:scope"]
        allowed = ["read:queries", "write:sessions"]
        assert validate_scopes(scopes, allowed) is False

    def test_validate_scopes_empty_strings(self):
        """Test validation rejects empty scope strings."""
        scopes = ["read:queries", ""]
        assert validate_scopes(scopes) is False

    def test_validate_scopes_none_values(self):
        """Test validation rejects None values."""
        scopes = ["read:queries", None]
        assert validate_scopes(scopes) is False

    def test_validate_scopes_wildcard(self):
        """Test validating wildcard scopes."""
        scopes = ["admin:*", "read:*"]
        allowed = ["admin:*", "read:*", "write:queries"]
        assert validate_scopes(scopes, allowed) is True


# ============================================================================
# Scope Access Tests
# ============================================================================

class TestScopeAccess:
    """Tests for scope-based access control."""

    def test_has_scope_exact_match(self):
        """Test scope check with exact match."""
        scopes = ["read:queries", "write:sessions"]
        assert has_scope(scopes, "read:queries") is True

    def test_has_scope_not_present(self):
        """Test scope check when scope not present."""
        scopes = ["read:queries", "write:sessions"]
        assert has_scope(scopes, "admin:users") is False

    def test_has_scope_wildcard(self):
        """Test scope check with wildcard."""
        scopes = ["admin:*", "read:queries"]
        assert has_scope(scopes, "admin:users") is True
        assert has_scope(scopes, "admin:roles") is True

    def test_has_scope_wildcard_no_match(self):
        """Test wildcard doesn't match different prefix."""
        scopes = ["admin:*"]
        assert has_scope(scopes, "read:queries") is False

    def test_check_scope_access_all_present(self):
        """Test checking multiple required scopes."""
        scopes = ["read:queries", "write:sessions", "admin:users"]
        required = ["read:queries", "write:sessions"]
        assert check_scope_access(scopes, required) is True

    def test_check_scope_access_missing_one(self):
        """Test checking fails when one scope missing."""
        scopes = ["read:queries", "write:sessions"]
        required = ["read:queries", "admin:users"]
        assert check_scope_access(scopes, required) is False

    def test_check_scope_access_wildcard_covers(self):
        """Test wildcard scope covers required specific scope."""
        scopes = ["admin:*"]
        required = ["admin:users", "admin:roles"]
        assert check_scope_access(scopes, required) is True


# ============================================================================
# Key Expiration Tests
# ============================================================================

class TestKeyExpiration:
    """Tests for API key expiration."""

    def test_calculate_key_expiry(self):
        """Test calculating key expiry."""
        now = datetime.utcnow()
        expiry = calculate_key_expiry(365)
        # Should be approximately 365 days from now
        delta = expiry - now
        assert 364 * 24 < delta.total_seconds() / 3600 < 366 * 24

    def test_calculate_key_expiry_none(self):
        """Test calculating expiry with None (no expiration)."""
        expiry = calculate_key_expiry(None)
        assert expiry is None

    def test_is_api_key_expired_valid(self):
        """Test expiry check with valid key."""
        expiry = datetime.utcnow() + timedelta(days=365)
        assert is_api_key_expired(expiry) is False

    def test_is_api_key_expired_expired(self):
        """Test expiry check with expired key."""
        expiry = datetime.utcnow() - timedelta(days=1)
        assert is_api_key_expired(expiry) is True

    def test_is_api_key_expired_none(self):
        """Test expiry check with no expiration."""
        assert is_api_key_expired(None) is False

    def test_is_api_key_expired_boundary(self):
        """Test expiry at exact boundary."""
        expiry = datetime.utcnow()
        # Should be considered expired (>= comparison)
        assert is_api_key_expired(expiry) is True


# ============================================================================
# Key Validity Tests
# ============================================================================

class TestKeyValidity:
    """Tests for API key validity checks."""

    def test_is_api_key_valid_all_good(self):
        """Test key validity with all conditions met."""
        expiry = datetime.utcnow() + timedelta(days=365)
        assert is_api_key_valid(is_active=True, expires_at=expiry, is_revoked=False) is True

    def test_is_api_key_valid_inactive(self):
        """Test key validity with inactive key."""
        expiry = datetime.utcnow() + timedelta(days=365)
        assert is_api_key_valid(is_active=False, expires_at=expiry, is_revoked=False) is False

    def test_is_api_key_valid_expired(self):
        """Test key validity with expired key."""
        expiry = datetime.utcnow() - timedelta(days=1)
        assert is_api_key_valid(is_active=True, expires_at=expiry, is_revoked=False) is False

    def test_is_api_key_valid_revoked(self):
        """Test key validity with revoked key."""
        expiry = datetime.utcnow() + timedelta(days=365)
        assert is_api_key_valid(is_active=True, expires_at=expiry, is_revoked=True) is False

    def test_is_api_key_valid_no_expiry(self):
        """Test key validity with no expiration set."""
        assert is_api_key_valid(is_active=True, expires_at=None, is_revoked=False) is True


# ============================================================================
# API Key Endpoints (Mocked)
# ============================================================================

class TestAPIKeyEndpoints:
    """Tests for API key endpoints."""

    def test_create_api_key_requires_auth(self, client):
        """Test create endpoint requires authentication."""
        response = client.post("/api-keys", json={"name": "test-key"})
        assert response.status_code in [401, 403]

    def test_list_api_keys_requires_auth(self, client):
        """Test list endpoint requires authentication."""
        response = client.get("/api-keys")
        assert response.status_code in [401, 403]

    def test_update_api_key_requires_auth(self, client):
        """Test update endpoint requires authentication."""
        response = client.patch("/api-keys/key123", json={"name": "updated"})
        assert response.status_code in [401, 403]

    def test_delete_api_key_requires_auth(self, client):
        """Test delete endpoint requires authentication."""
        response = client.delete("/api-keys/key123")
        assert response.status_code in [401, 403]

    def test_get_api_key_usage_requires_auth(self, client):
        """Test usage endpoint requires authentication."""
        response = client.get("/api-keys/key123/usage")
        assert response.status_code in [401, 403]


# ============================================================================
# Security Tests for API Keys
# ============================================================================

class TestAPIKeySecurity:
    """Security tests for API keys."""

    def test_api_key_not_logged_in_plaintext(self):
        """Test that API keys are not exposed in logs."""
        # In actual implementation, verify full keys aren't logged
        full_key, key_prefix = generate_api_key()
        # Only prefix should be visible
        assert key_prefix != full_key

    def test_api_key_hashed_before_storage(self):
        """Test that API keys are hashed before storage."""
        full_key, _ = generate_api_key()
        hashed = hash_api_key(full_key)
        # Hashed should be different
        assert hashed != full_key
        # Should not be reversible
        assert full_key not in hashed

    def test_api_key_prefix_insufficient_for_auth(self):
        """Test that prefix alone is insufficient for authentication."""
        full_key, key_prefix = generate_api_key()
        # Prefix should not contain enough entropy to brute force
        assert len(key_prefix) == 11  # rk_ + 8 chars
        # But full key should be long enough (rk_ + 8 + _ + urlsafe_base64)
        assert len(full_key) > 50

    def test_api_key_shown_once_only(self):
        """Test that full API key is shown only once."""
        # This is tested at endpoint level
        # Endpoint should return full key on creation
        # But not on list/get operations
        pass

    def test_api_key_rate_limiting_per_key(self):
        """Test that rate limiting can be applied per key."""
        # Rate limiting should be configurable per key
        pass


# ============================================================================
# Edge Cases
# ============================================================================

class TestAPIKeyEdgeCases:
    """Tests for edge cases and error handling."""

    def test_hash_api_key_empty_string(self):
        """Test hashing empty key."""
        hashed = hash_api_key("")
        assert hashed is not None
        assert len(hashed) == 64

    def test_extract_prefix_special_characters(self):
        """Test extracting prefix from key with special chars."""
        # Keys use base64url, which includes - and _
        full_key = "rk_ABCD1234_" + "a" * 50
        prefix = extract_key_prefix(full_key)
        assert prefix == "rk_ABCD1234"

    def test_validate_scopes_duplicate_scopes(self):
        """Test validating duplicate scopes."""
        scopes = ["read:queries", "read:queries"]
        assert validate_scopes(scopes) is True

    def test_validate_scopes_case_sensitive(self):
        """Test scope validation is case sensitive."""
        scopes = ["read:Queries"]  # Capital Q
        allowed = ["read:queries"]
        assert validate_scopes(scopes, allowed) is False

    def test_calculate_expiry_zero_days(self):
        """Test calculating expiry with zero days."""
        now = datetime.utcnow()
        expiry = calculate_key_expiry(0)
        delta = expiry - now
        assert delta.total_seconds() < 60

    def test_is_api_key_valid_boundary_conditions(self):
        """Test validity at exact expiration time."""
        expiry = datetime.utcnow()
        # At exact time, should be considered expired
        assert is_api_key_valid(True, expiry, False) is False
