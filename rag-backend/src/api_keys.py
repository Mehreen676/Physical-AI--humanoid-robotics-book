"""
API Key Management Utilities (Phase 6).
Handles API key generation, hashing, validation, and scope checking.
"""

import secrets
import hashlib
import string
import logging
from typing import List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def generate_api_key(prefix_length: int = 8, key_length: int = 32) -> Tuple[str, str]:
    """
    Generate a new API key.

    Args:
        prefix_length: Length of prefix for display (default 8)
        key_length: Length of random portion (default 32)

    Returns:
        Tuple[str, str]: (full_key, key_prefix)

    Note:
        Format: "rk_[8-char-prefix]_[random]"
        Only the full key is returned to user; prefix is shown in UI later
        Full key should be stored securely by the user immediately
    """
    # Generate prefix (first 8 chars for display)
    prefix_chars = string.ascii_uppercase + string.digits
    prefix = "".join(secrets.choice(prefix_chars) for _ in range(prefix_length))

    # Generate full random key
    random_portion = secrets.token_urlsafe(key_length)

    # Format: rk_PREFIX_RANDOM
    full_key = f"rk_{prefix}_{random_portion}"
    key_prefix = f"rk_{prefix}"

    return full_key, key_prefix


def hash_api_key(key: str) -> str:
    """
    Hash an API key using SHA256 for secure database storage.

    Args:
        key: Plaintext API key

    Returns:
        str: Hexadecimal SHA256 hash

    Note:
        API keys are hashed before storage so database compromise doesn't leak keys
    """
    return hashlib.sha256(key.encode()).hexdigest()


def validate_api_key_format(key: str) -> bool:
    """
    Validate that a key is in proper API key format.

    Args:
        key: Key to validate

    Returns:
        bool: True if key appears valid, False otherwise
    """
    if not key or not isinstance(key, str):
        return False

    # Must start with "rk_"
    if not key.startswith("rk_"):
        return False

    # Must contain at least 2 underscores (rk_PREFIX_RANDOM)
    if key.count("_") < 2:
        return False

    # Minimum reasonable length (should be 60+ chars)
    if len(key) < 60:
        return False

    return True


def extract_key_prefix(key: str) -> str:
    """
    Extract the display prefix from an API key.

    Args:
        key: Full API key

    Returns:
        str: Key prefix (e.g., "rk_ABCD1234")
    """
    parts = key.split("_")
    if len(parts) >= 2:
        return f"{parts[0]}_{parts[1]}"
    return key[:16]


def validate_scopes(scopes: List[str], allowed_scopes: Optional[List[str]] = None) -> bool:
    """
    Validate that requested scopes are allowed.

    Args:
        scopes: List of requested scopes
        allowed_scopes: List of valid scopes (None = allow any)

    Returns:
        bool: True if all scopes are valid, False otherwise

    Note:
        If allowed_scopes is None, any scope format is accepted
        Otherwise, scopes must be in allowed_scopes list
    """
    if not scopes or not isinstance(scopes, list):
        return False

    if allowed_scopes is None:
        # Accept any scope as long as it's a non-empty string
        return all(isinstance(s, str) and len(s) > 0 for s in scopes)

    # Check all scopes are in allowed list
    return all(scope in allowed_scopes for scope in scopes)


def get_default_scopes() -> List[str]:
    """
    Get default scopes for new API keys.

    Returns:
        List[str]: Default scope list

    Note:
        Default is read-only access to queries and sessions
        Users can request additional scopes during key creation
    """
    return ["read:queries", "read:sessions"]


def has_scope(scopes: List[str], required_scope: str) -> bool:
    """
    Check if a scope list includes a required scope.

    Args:
        scopes: List of scopes from API key
        required_scope: Required scope to check

    Returns:
        bool: True if required scope is in list, False otherwise

    Note:
        Supports wildcard scopes:
        - "admin:*" includes all "admin:*" scopes
        - "read:*" includes all "read:*" scopes
    """
    # Exact match
    if required_scope in scopes:
        return True

    # Wildcard match
    for scope in scopes:
        if scope.endswith("*"):
            # "admin:*" matches "admin:users", "admin:roles", etc.
            prefix = scope[:-1]  # Remove the *
            if required_scope.startswith(prefix):
                return True

    return False


def check_scope_access(scopes: List[str], required_scopes: List[str]) -> bool:
    """
    Check if a scope list includes all required scopes.

    Args:
        scopes: List of scopes from API key
        required_scopes: List of scopes required for operation

    Returns:
        bool: True if all required scopes are present, False otherwise
    """
    return all(has_scope(scopes, scope) for scope in required_scopes)


def calculate_key_expiry(expiration_days: Optional[int]) -> Optional[datetime]:
    """
    Calculate API key expiration time.

    Args:
        expiration_days: Number of days until expiration (None = no expiry)

    Returns:
        Optional[datetime]: Expiration timestamp or None if no expiry

    Note:
        Keys can optionally have no expiration for long-lived service accounts
    """
    if expiration_days is None:
        return None
    return datetime.utcnow() + timedelta(days=expiration_days)


def is_api_key_expired(expires_at: Optional[datetime]) -> bool:
    """
    Check if an API key has expired.

    Args:
        expires_at: Key expiration timestamp (None = no expiry)

    Returns:
        bool: True if key is expired, False otherwise
    """
    if expires_at is None:
        return False  # No expiration
    return datetime.utcnow() >= expires_at


def is_api_key_valid(
    is_active: bool, expires_at: Optional[datetime], is_revoked: bool = False
) -> bool:
    """
    Check if an API key is valid for use.

    Args:
        is_active: Key activation status
        expires_at: Key expiration timestamp
        is_revoked: Whether key has been revoked

    Returns:
        bool: True if key is valid for use, False otherwise
    """
    # Must be active
    if not is_active:
        return False

    # Must not be revoked
    if is_revoked:
        return False

    # Must not be expired
    if is_api_key_expired(expires_at):
        return False

    return True
