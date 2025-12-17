"""
Phase 7 WAVE 2: Security Hardening Module

Implements production security controls:
- API key validation
- CORS configuration
- Rate limiting
- Input validation & sanitization
- Error message sanitization
"""

import hashlib
import re
import logging
from typing import Optional, Dict, List
from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict
import html

logger = logging.getLogger(__name__)

# Security configuration
MAX_QUERY_LENGTH = 500  # characters
MAX_SELECTED_TEXT_LENGTH = 10000  # characters
MAX_QUERY_TOKENS = 2000

RATE_LIMIT_QUERIES_PER_MINUTE = 10
RATE_LIMIT_QUERIES_PER_DAY_PER_IP = 1000

# Sanitization patterns
DANGEROUS_PATTERNS = [
    r"<script[^>]*>.*?</script>",  # Script tags
    r"javascript:",  # javascript: protocol
    r"on\w+\s*=",  # Event handlers (onclick, etc)
    r"<iframe[^>]*>",  # Iframe tags
]


class APIKeyValidator:
    """Validates API keys for admin endpoints."""

    def __init__(self):
        """Initialize with valid API keys (in production, these come from DB or secrets manager)."""
        # Format: prefix_hash
        self.valid_keys = set()
        self.key_metadata = {}  # key_hash -> metadata

    def add_key(self, key: str, name: str = "default", scopes: List[str] = None) -> str:
        """
        Add an API key to the validation list.

        Args:
            key: The full API key (e.g., "rk_prod_abc123xyz789")
            name: Human-readable name for the key
            scopes: List of permissions (e.g., ["ingest", "query"])

        Returns:
            The key hash (what gets stored in DB)
        """
        key_hash = self._hash_key(key)
        self.valid_keys.add(key_hash)
        self.key_metadata[key_hash] = {
            "name": name,
            "scopes": scopes or ["query"],
            "created_at": datetime.utcnow().isoformat(),
            "active": True,
        }
        logger.info(f"Added API key: {name} (hash: {key_hash[:16]}...)")
        return key_hash

    def validate_key(self, key: str) -> tuple[bool, Optional[Dict]]:
        """
        Validate an API key.

        Args:
            key: The full API key from X-API-Key header

        Returns:
            Tuple of (is_valid, metadata) where metadata contains scope info
        """
        if not key:
            return False, None

        key_hash = self._hash_key(key)
        if key_hash not in self.valid_keys:
            logger.warning(f"Invalid API key attempt: {key_hash[:16]}...")
            return False, None

        metadata = self.key_metadata.get(key_hash, {})
        if not metadata.get("active"):
            logger.warning(f"Inactive API key: {metadata.get('name')}")
            return False, None

        return True, metadata

    def check_scope(self, key: str, required_scope: str) -> bool:
        """
        Check if API key has required scope.

        Args:
            key: The full API key
            required_scope: Scope to check (e.g., "ingest", "admin:users")

        Returns:
            True if key has the required scope
        """
        is_valid, metadata = self.validate_key(key)
        if not is_valid:
            return False

        scopes = metadata.get("scopes", [])

        # Check exact match
        if required_scope in scopes:
            return True

        # Check wildcard support (e.g., "admin:*" matches "admin:users")
        for scope in scopes:
            if scope.endswith("*"):
                pattern = scope.replace("*", ".*")
                if re.match(f"^{pattern}$", required_scope):
                    return True

        return False

    @staticmethod
    def _hash_key(key: str) -> str:
        """Hash API key before storage."""
        return hashlib.sha256(key.encode()).hexdigest()


class InputValidator:
    """Validates and sanitizes user inputs."""

    @staticmethod
    def validate_query(query: str) -> tuple[bool, Optional[str]]:
        """
        Validate query input.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not query:
            return False, "Query cannot be empty"

        if len(query) > MAX_QUERY_LENGTH:
            return False, f"Query exceeds maximum length of {MAX_QUERY_LENGTH} characters"

        if query.strip() != query:
            # Allow leading/trailing whitespace for now, but log it
            logger.debug("Query has unexpected whitespace")

        return True, None

    @staticmethod
    def validate_selected_text(text: str) -> tuple[bool, Optional[str]]:
        """
        Validate selected text input.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not text:
            return False, "Selected text cannot be empty"

        if len(text) > MAX_SELECTED_TEXT_LENGTH:
            return False, f"Selected text exceeds maximum length of {MAX_SELECTED_TEXT_LENGTH} characters"

        return True, None

    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        Remove potentially dangerous content from user input.

        Args:
            text: User-provided text

        Returns:
            Sanitized text
        """
        # Remove HTML/script tags
        sanitized = text
        for pattern in DANGEROUS_PATTERNS:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE | re.DOTALL)

        # HTML-escape the remaining text
        sanitized = html.escape(sanitized)

        return sanitized

    @staticmethod
    def validate_api_key_format(key: str) -> tuple[bool, Optional[str]]:
        """
        Validate API key format.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Format: rk_<prefix>_<random>
        if not re.match(r"^rk_[a-z0-9_]+$", key, re.IGNORECASE):
            return False, "Invalid API key format"

        if len(key) < 20:
            return False, "API key too short"

        if len(key) > 64:
            return False, "API key too long"

        return True, None


class RateLimiter:
    """Implements rate limiting using in-memory store."""

    def __init__(self):
        """Initialize rate limiter."""
        self.requests_per_minute = defaultdict(list)  # session_id -> [timestamps]
        self.requests_per_day = defaultdict(list)  # ip_address -> [timestamps]

    def check_rate_limit(
        self,
        session_id: str,
        client_ip: str,
        verbose: bool = False,
    ) -> tuple[bool, Optional[str]]:
        """
        Check if request exceeds rate limits.

        Args:
            session_id: User session ID
            client_ip: Client IP address
            verbose: Whether to log detailed info

        Returns:
            Tuple of (is_allowed, error_message)
        """
        now = datetime.utcnow()

        # Check queries per minute (per session)
        minute_ago = now - timedelta(minutes=1)
        self.requests_per_minute[session_id] = [
            ts for ts in self.requests_per_minute[session_id]
            if ts > minute_ago
        ]

        if len(self.requests_per_minute[session_id]) >= RATE_LIMIT_QUERIES_PER_MINUTE:
            if verbose:
                logger.warning(
                    f"Rate limit exceeded for session {session_id}: "
                    f"{len(self.requests_per_minute[session_id])}/{RATE_LIMIT_QUERIES_PER_MINUTE} per minute"
                )
            return False, "Rate limit exceeded: 10 queries per minute"

        # Check queries per day (per IP)
        day_ago = now - timedelta(days=1)
        self.requests_per_day[client_ip] = [
            ts for ts in self.requests_per_day[client_ip]
            if ts > day_ago
        ]

        if len(self.requests_per_day[client_ip]) >= RATE_LIMIT_QUERIES_PER_DAY_PER_IP:
            if verbose:
                logger.warning(
                    f"Daily rate limit exceeded for IP {client_ip}: "
                    f"{len(self.requests_per_day[client_ip])}/{RATE_LIMIT_QUERIES_PER_DAY_PER_IP} per day"
                )
            return False, "Rate limit exceeded: 1000 queries per day"

        # Add current request
        self.requests_per_minute[session_id].append(now)
        self.requests_per_day[client_ip].append(now)

        return True, None

    def get_remaining_requests(self, session_id: str) -> int:
        """Get remaining requests for session in current minute."""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        self.requests_per_minute[session_id] = [
            ts for ts in self.requests_per_minute[session_id]
            if ts > minute_ago
        ]
        return max(0, RATE_LIMIT_QUERIES_PER_MINUTE - len(self.requests_per_minute[session_id]))


class CORSManager:
    """Manages CORS (Cross-Origin Resource Sharing) configuration."""

    def __init__(self, allowed_origins: List[str]):
        """
        Initialize CORS manager.

        Args:
            allowed_origins: List of allowed origin domains
        """
        self.allowed_origins = set(allowed_origins)
        logger.info(f"CORS configured for origins: {', '.join(allowed_origins)}")

    def is_origin_allowed(self, origin: str) -> bool:
        """
        Check if origin is allowed.

        Args:
            origin: The request origin header value

        Returns:
            True if origin is in allowed list
        """
        return origin in self.allowed_origins

    def add_cors_headers(self, origin: str) -> Dict[str, str]:
        """
        Generate CORS headers for response.

        Args:
            origin: The request origin

        Returns:
            Dict of CORS headers
        """
        if not self.is_origin_allowed(origin):
            return {}

        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, X-API-Key, Authorization",
            "Access-Control-Max-Age": "3600",
            "Access-Control-Allow-Credentials": "true",
        }


class ErrorSanitizer:
    """Sanitizes error messages to prevent information leakage."""

    # Mapping of error types to safe messages
    SAFE_MESSAGES = {
        "ValueError": "Invalid input provided",
        "KeyError": "Resource not found",
        "TimeoutError": "Request timed out, please try again",
        "ConnectionError": "Service temporarily unavailable",
        "PermissionError": "Access denied",
        "RuntimeError": "An error occurred processing your request",
    }

    @staticmethod
    def sanitize_error(exception: Exception, expose_details: bool = False) -> str:
        """
        Generate safe error message from exception.

        Args:
            exception: The exception that occurred
            expose_details: Whether to expose internal details (dev mode only)

        Returns:
            Safe error message
        """
        exception_type = type(exception).__name__

        if expose_details:
            # Development: expose full details
            return f"{exception_type}: {str(exception)}"

        # Production: return generic safe message
        return ErrorSanitizer.SAFE_MESSAGES.get(
            exception_type,
            "An error occurred processing your request",
        )

    @staticmethod
    def sanitize_response(response_data: dict, remove_fields: List[str] = None) -> dict:
        """
        Remove sensitive fields from response.

        Args:
            response_data: Response to sanitize
            remove_fields: Fields to remove (e.g., ["api_key", "secret"])

        Returns:
            Sanitized response
        """
        if remove_fields is None:
            remove_fields = ["api_key", "secret", "password", "token", "internal_id"]

        sanitized = response_data.copy()
        for field in remove_fields:
            sanitized.pop(field, None)

        return sanitized


if __name__ == "__main__":
    # Example usage
    print("Security Module Loaded")

    # Test API key validation
    validator = APIKeyValidator()
    key = validator.add_key("rk_prod_test123456789", name="test_key", scopes=["ingest", "admin:*"])
    print(f"Added key with hash: {key[:16]}...")

    # Test input validation
    is_valid, error = InputValidator.validate_query("test query")
    print(f"Query validation: {is_valid}, {error}")

    # Test rate limiting
    limiter = RateLimiter()
    is_allowed, msg = limiter.check_rate_limit("session1", "192.168.1.1")
    print(f"Rate limit check: {is_allowed}, {msg}")

    # Test input sanitization
    dangerous_input = "<script>alert('xss')</script> normal text"
    sanitized = InputValidator.sanitize_input(dangerous_input)
    print(f"Original: {dangerous_input}")
    print(f"Sanitized: {sanitized}")
