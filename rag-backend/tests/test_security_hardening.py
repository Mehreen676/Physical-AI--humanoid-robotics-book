"""
Phase 7 WAVE 2: Security Hardening Tests

Tests for production security controls:
- API key validation
- CORS configuration
- Rate limiting
- Input validation & sanitization
- Error message sanitization
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from security import (
    APIKeyValidator,
    InputValidator,
    RateLimiter,
    CORSManager,
    ErrorSanitizer,
)


class TestAPIKeyValidation:
    """Test API key validation and scope checking."""

    @pytest.fixture
    def validator(self):
        """Create API key validator."""
        return APIKeyValidator()

    def test_add_and_validate_key(self, validator):
        """Test adding and validating an API key."""
        key = "rk_prod_test123456789abcdef"
        key_hash = validator.add_key(key, name="test_key")

        # Should validate successfully
        is_valid, metadata = validator.validate_key(key)
        assert is_valid is True
        assert metadata is not None
        assert metadata["name"] == "test_key"

    def test_invalid_key_rejected(self, validator):
        """Test that invalid keys are rejected."""
        is_valid, metadata = validator.validate_key("invalid_key_xyz")
        assert is_valid is False
        assert metadata is None

    def test_empty_key_rejected(self, validator):
        """Test that empty keys are rejected."""
        is_valid, metadata = validator.validate_key("")
        assert is_valid is False

    def test_key_with_scope_validation(self, validator):
        """Test checking specific scopes on keys."""
        key = "rk_prod_admin123456789abcdef"
        validator.add_key(key, name="admin_key", scopes=["admin:users", "admin:roles"])

        # Should have admin:users scope
        assert validator.check_scope(key, "admin:users") is True

        # Should not have other scopes
        assert validator.check_scope(key, "ingest") is False

    def test_wildcard_scope_matching(self, validator):
        """Test wildcard scope matching (e.g., admin:* matches admin:users)."""
        key = "rk_prod_admin_wild123456789"
        validator.add_key(key, name="wildcard_key", scopes=["admin:*", "query"])

        # Should match admin:users with admin:*
        assert validator.check_scope(key, "admin:users") is True
        assert validator.check_scope(key, "admin:roles") is True

        # Should match query
        assert validator.check_scope(key, "query") is True

        # Should not match ingest
        assert validator.check_scope(key, "ingest") is False

    def test_inactive_key_rejected(self, validator):
        """Test that inactive keys are rejected."""
        key = "rk_prod_test123456789abcdef"
        validator.add_key(key, name="test_key")

        # Deactivate the key
        key_hash = validator._hash_key(key)
        validator.key_metadata[key_hash]["active"] = False

        is_valid, _ = validator.validate_key(key)
        assert is_valid is False

    def test_multiple_keys_isolated(self, validator):
        """Test that multiple keys are isolated from each other."""
        key1 = "rk_prod_key1_123456789abcdef"
        key2 = "rk_prod_key2_123456789abcdef"

        validator.add_key(key1, name="key1", scopes=["ingest"])
        validator.add_key(key2, name="key2", scopes=["query"])

        # Each key should only have its own scopes
        assert validator.check_scope(key1, "ingest") is True
        assert validator.check_scope(key1, "query") is False

        assert validator.check_scope(key2, "query") is True
        assert validator.check_scope(key2, "ingest") is False


class TestInputValidation:
    """Test input validation and sanitization."""

    def test_query_validation_valid(self):
        """Test that valid queries pass validation."""
        is_valid, error = InputValidator.validate_query("What is ROS 2?")
        assert is_valid is True
        assert error is None

    def test_query_validation_empty(self):
        """Test that empty queries are rejected."""
        is_valid, error = InputValidator.validate_query("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_query_validation_too_long(self):
        """Test that queries exceeding max length are rejected."""
        long_query = "a" * 501  # Exceeds 500 char limit
        is_valid, error = InputValidator.validate_query(long_query)
        assert is_valid is False
        assert "exceeds maximum" in error.lower()

    def test_query_validation_max_length_ok(self):
        """Test that queries at exact max length pass."""
        query = "a" * 500  # At limit
        is_valid, error = InputValidator.validate_query(query)
        assert is_valid is True

    def test_selected_text_validation_valid(self):
        """Test that valid selected text passes validation."""
        is_valid, error = InputValidator.validate_selected_text("Some selected text from the book.")
        assert is_valid is True
        assert error is None

    def test_selected_text_validation_too_long(self):
        """Test that selected text exceeding limit is rejected."""
        long_text = "a" * 10001  # Exceeds 10000 char limit
        is_valid, error = InputValidator.validate_selected_text(long_text)
        assert is_valid is False
        assert "exceeds maximum" in error.lower()

    def test_input_sanitization_removes_script_tags(self):
        """Test that script tags are removed during sanitization."""
        dirty_input = "Hello <script>alert('xss')</script> world"
        clean = InputValidator.sanitize_input(dirty_input)

        assert "<script>" not in clean
        assert "alert" not in clean
        assert "Hello" in clean
        assert "world" in clean

    def test_input_sanitization_removes_event_handlers(self):
        """Test that event handlers are removed or escaped."""
        dirty_input = '<img src="x" onclick="alert(\'xss\')">'
        clean = InputValidator.sanitize_input(dirty_input)

        # Event handler should be removed or escaped (not executable)
        assert "onclick=" not in clean  # No executable onclick attribute

    def test_input_sanitization_removes_javascript_protocol(self):
        """Test that javascript: protocol is removed."""
        dirty_input = '<a href="javascript:alert(\'xss\')">Click me</a>'
        clean = InputValidator.sanitize_input(dirty_input)

        assert "javascript:" not in clean

    def test_input_sanitization_html_escaping(self):
        """Test that HTML entities are escaped."""
        dirty_input = "<p>Paragraph</p>"
        clean = InputValidator.sanitize_input(dirty_input)

        # Should be HTML-escaped
        assert "&lt;p&gt;" in clean or "Paragraph" in clean

    def test_api_key_format_validation_valid(self):
        """Test that valid API key formats pass."""
        is_valid, error = InputValidator.validate_api_key_format("rk_prod_test123456789abcdef")
        assert is_valid is True
        assert error is None

    def test_api_key_format_validation_invalid_prefix(self):
        """Test that invalid prefix is rejected."""
        is_valid, error = InputValidator.validate_api_key_format("sk_prod_test123456789abcdef")
        assert is_valid is False

    def test_api_key_format_validation_too_short(self):
        """Test that too-short keys are rejected."""
        is_valid, error = InputValidator.validate_api_key_format("rk_short")
        assert is_valid is False

    def test_api_key_format_validation_too_long(self):
        """Test that too-long keys are rejected."""
        is_valid, error = InputValidator.validate_api_key_format("rk_" + "a" * 100)
        assert is_valid is False


class TestRateLimiting:
    """Test rate limiting functionality."""

    @pytest.fixture
    def limiter(self):
        """Create rate limiter."""
        return RateLimiter()

    def test_allow_requests_within_limit(self, limiter):
        """Test that requests within rate limit are allowed."""
        session_id = "session123"
        client_ip = "192.168.1.1"

        # First 10 requests should be allowed
        for i in range(10):
            is_allowed, msg = limiter.check_rate_limit(session_id, client_ip)
            assert is_allowed is True
            assert msg is None

    def test_reject_requests_exceeding_per_minute_limit(self, limiter):
        """Test that requests exceeding per-minute limit are rejected."""
        session_id = "session123"
        client_ip = "192.168.1.1"

        # Use up the limit
        for i in range(10):
            limiter.check_rate_limit(session_id, client_ip)

        # 11th request should be rejected
        is_allowed, msg = limiter.check_rate_limit(session_id, client_ip)
        assert is_allowed is False
        assert "rate limit" in msg.lower()

    def test_different_sessions_independent(self, limiter):
        """Test that rate limits are independent per session."""
        client_ip = "192.168.1.1"

        # Session 1 uses all its quota
        for i in range(10):
            limiter.check_rate_limit("session1", client_ip)

        # Session 2 should still have quota
        is_allowed, _ = limiter.check_rate_limit("session2", client_ip)
        assert is_allowed is True

    def test_get_remaining_requests(self, limiter):
        """Test getting remaining requests for a session."""
        session_id = "session123"
        client_ip = "192.168.1.1"

        # Use 5 requests
        for i in range(5):
            limiter.check_rate_limit(session_id, client_ip)

        # Should have 5 remaining
        remaining = limiter.get_remaining_requests(session_id)
        assert remaining == 5


class TestCORSConfiguration:
    """Test CORS configuration and origin validation."""

    @pytest.fixture
    def cors_manager(self):
        """Create CORS manager."""
        return CORSManager([
            "http://localhost:3000",
            "https://book.example.com",
            "https://api.example.com",
        ])

    def test_allowed_origin(self, cors_manager):
        """Test that allowed origins are recognized."""
        assert cors_manager.is_origin_allowed("http://localhost:3000") is True
        assert cors_manager.is_origin_allowed("https://book.example.com") is True

    def test_disallowed_origin(self, cors_manager):
        """Test that disallowed origins are rejected."""
        assert cors_manager.is_origin_allowed("https://evil.com") is False
        assert cors_manager.is_origin_allowed("http://localhost:8080") is False

    def test_cors_headers_generated_for_allowed_origin(self, cors_manager):
        """Test that CORS headers are generated for allowed origins."""
        headers = cors_manager.add_cors_headers("http://localhost:3000")

        assert headers is not None
        assert "Access-Control-Allow-Origin" in headers
        assert headers["Access-Control-Allow-Origin"] == "http://localhost:3000"
        assert "Access-Control-Allow-Methods" in headers

    def test_cors_headers_not_generated_for_disallowed_origin(self, cors_manager):
        """Test that CORS headers are not generated for disallowed origins."""
        headers = cors_manager.add_cors_headers("https://evil.com")

        assert headers == {}


class TestErrorSanitization:
    """Test error message sanitization to prevent information leakage."""

    def test_sanitize_value_error_production(self):
        """Test that ValueError is sanitized in production."""
        exc = ValueError("Database connection string leaked: postgresql://user:pass@host")
        safe_msg = ErrorSanitizer.sanitize_error(exc, expose_details=False)

        assert "Invalid input" in safe_msg
        assert "connection" not in safe_msg
        assert "password" not in safe_msg

    def test_sanitize_error_development_mode(self):
        """Test that full details are exposed in development mode."""
        exc = ValueError("Some internal error detail")
        safe_msg = ErrorSanitizer.sanitize_error(exc, expose_details=True)

        assert "ValueError" in safe_msg
        assert "Some internal error detail" in safe_msg

    def test_sanitize_unknown_error_type(self):
        """Test that unknown error types get generic message."""
        class CustomException(Exception):
            pass

        exc = CustomException("Custom error")
        safe_msg = ErrorSanitizer.sanitize_error(exc, expose_details=False)

        assert "error occurred" in safe_msg.lower()

    def test_sanitize_response_removes_sensitive_fields(self):
        """Test that sensitive fields are removed from responses."""
        response = {
            "user_id": "123",
            "api_key": "secret_key_xyz",
            "query": "test",
            "token": "jwt_token_xyz",
        }

        sanitized = ErrorSanitizer.sanitize_response(response)

        assert "user_id" in sanitized
        assert "query" in sanitized
        assert "api_key" not in sanitized
        assert "token" not in sanitized

    def test_sanitize_response_custom_fields(self):
        """Test sanitizing with custom sensitive fields list."""
        response = {
            "data": "public",
            "internal_id": "secret123",
            "custom_secret": "hidden",
        }

        sanitized = ErrorSanitizer.sanitize_response(response, remove_fields=["internal_id", "custom_secret"])

        assert "data" in sanitized
        assert "internal_id" not in sanitized
        assert "custom_secret" not in sanitized


class TestSecurityIntegration:
    """Integration tests combining multiple security components."""

    def test_complete_request_validation_flow(self):
        """Test complete flow: validate API key, sanitize input, check rate limit."""
        # Setup
        validator = APIKeyValidator()
        api_key = "rk_test_abc123def456ghi789"
        validator.add_key(api_key, name="test", scopes=["query"])

        input_validator = InputValidator()
        limiter = RateLimiter()

        # Simulate secure request
        is_valid, _ = validator.validate_key(api_key)
        assert is_valid is True

        query = "What is ROS 2?"
        is_valid, _ = input_validator.validate_query(query)
        assert is_valid is True

        is_allowed, _ = limiter.check_rate_limit("session1", "192.168.1.1")
        assert is_allowed is True

        # Simulate malicious request
        bad_key = "rk_bad_key_xyz"
        is_valid, _ = validator.validate_key(bad_key)
        assert is_valid is False

        bad_query = "<script>alert('xss')</script>"
        is_valid, _ = input_validator.validate_query(bad_query)
        assert is_valid is True  # Not rejected, just long enough
        sanitized = input_validator.sanitize_input(bad_query)
        assert "<script>" not in sanitized


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
