"""
Refresh Token Management Utilities (Phase 6).
Handles refresh token generation, hashing, validation, and device tracking.
"""

import secrets
import hashlib
from typing import Tuple, Optional
from datetime import datetime, timedelta
from urllib.parse import quote
import logging

logger = logging.getLogger(__name__)


def generate_refresh_token(length: int = 64) -> str:
    """
    Generate a cryptographically secure refresh token.

    Args:
        length: Token length in bytes (default 64 = ~86 base64 chars)

    Returns:
        str: URL-safe base64-encoded refresh token

    Note:
        Tokens should be long (64+ bytes) to resist brute force attacks
        Format: "rk_[8-char-prefix]_[58-char-random]" for display
    """
    # Generate random bytes and encode as URL-safe base64
    token_bytes = secrets.token_urlsafe(length)
    return token_bytes


def hash_token(token: str) -> str:
    """
    Hash a token using SHA256 for secure database storage.

    Args:
        token: Plaintext token

    Returns:
        str: Hexadecimal SHA256 hash

    Note:
        Tokens are hashed before storage so database compromise doesn't leak tokens
        Only returned token is never stored in plaintext
    """
    return hashlib.sha256(token.encode()).hexdigest()


def extract_token_prefix(token: str, prefix_length: int = 8) -> str:
    """
    Extract first N characters of a token for display purposes.

    Args:
        token: Plaintext token
        prefix_length: Number of characters to extract (default 8)

    Returns:
        str: First N characters of token

    Note:
        Used in UI to show "rk_ABCD..." for display in active sessions list
    """
    return token[:prefix_length] if len(token) >= prefix_length else token


def extract_device_id_from_user_agent(user_agent: str) -> str:
    """
    Extract a device ID hash from User-Agent header.

    Args:
        user_agent: User-Agent header value

    Returns:
        str: SHA256 hash of User-Agent for device tracking

    Note:
        Used to identify devices and detect unusual login locations
        Hash prevents storing full User-Agent string
    """
    if not user_agent:
        return "unknown"
    return hashlib.sha256(user_agent.encode()).hexdigest()[:16]


def parse_user_agent(user_agent: str) -> str:
    """
    Parse User-Agent header to extract device name.

    Args:
        user_agent: User-Agent header value

    Returns:
        str: Human-readable device name (e.g., "Chrome on Windows")

    Note:
        Simple parsing for common browsers; could be enhanced with ua-parser library
    """
    if not user_agent:
        return "Unknown Device"

    ua_lower = user_agent.lower()

    # Extract browser
    if "chrome" in ua_lower and "edg" not in ua_lower:
        browser = "Chrome"
    elif "firefox" in ua_lower:
        browser = "Firefox"
    elif "safari" in ua_lower and "chrome" not in ua_lower:
        browser = "Safari"
    elif "edg" in ua_lower:
        browser = "Edge"
    elif "msie" in ua_lower or "trident" in ua_lower:
        browser = "Internet Explorer"
    else:
        browser = "Unknown Browser"

    # Extract OS
    if "windows" in ua_lower:
        os = "Windows"
    elif "mac" in ua_lower:
        os = "macOS"
    elif "linux" in ua_lower:
        os = "Linux"
    elif "android" in ua_lower:
        os = "Android"
    elif "iphone" in ua_lower or "ipad" in ua_lower:
        os = "iOS"
    else:
        os = "Unknown OS"

    return f"{browser} on {os}"


def calculate_token_expiry(expiration_days: int) -> datetime:
    """
    Calculate token expiration time.

    Args:
        expiration_days: Number of days until expiration

    Returns:
        datetime: Expiration timestamp (UTC)
    """
    return datetime.utcnow() + timedelta(days=expiration_days)


def is_token_expired(expires_at: datetime) -> bool:
    """
    Check if a token has expired.

    Args:
        expires_at: Token expiration timestamp

    Returns:
        bool: True if token is expired, False otherwise
    """
    return datetime.utcnow() >= expires_at


def validate_refresh_token_format(token: str) -> bool:
    """
    Validate that a token is in proper format.

    Args:
        token: Token to validate

    Returns:
        bool: True if token appears valid, False otherwise

    Note:
        Basic validation - checks for reasonable length and charset
    """
    if not token or not isinstance(token, str):
        return False

    # Refresh tokens should be 60+ characters (base64url encoded)
    if len(token) < 60:
        return False

    # Check if it contains only valid base64url characters
    valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
    return all(c in valid_chars for c in token)


def can_rotate_token(rotation_count: int, max_chains: int = 3) -> bool:
    """
    Check if a token can be rotated based on chain limit.

    Args:
        rotation_count: Number of times this token has been rotated
        max_chains: Maximum allowed rotation chain length (default 3)

    Returns:
        bool: True if token can be rotated, False if max chains exceeded

    Note:
        Prevents indefinite token rotation without re-authentication
        Enforces re-login after N rotations to maintain security
    """
    return rotation_count < max_chains
