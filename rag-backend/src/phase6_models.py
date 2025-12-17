"""
Pydantic request/response models for Phase 6 endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ============================================================================
# TOTP (MFA) Models
# ============================================================================

class MFASetupResponse(BaseModel):
    """Response for MFA setup initiation."""
    qr_code_url: str = Field(..., description="Data URL for QR code image")
    secret: str = Field(..., description="Base32-encoded TOTP secret (for manual entry)")
    backup_codes: List[str] = Field(..., description="10 one-time backup codes (show to user once)")


class MFAVerifyRequest(BaseModel):
    """Request to verify TOTP code during setup."""
    code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP code")


class MFAVerifyResponse(BaseModel):
    """Response after MFA verification."""
    success: bool
    message: str
    backup_codes: Optional[List[str]] = None  # Returned if this was setup verification


class MFADisableRequest(BaseModel):
    """Request to disable MFA."""
    password: str = Field(..., description="User's password for confirmation")


class MFADisableResponse(BaseModel):
    """Response after MFA disabling."""
    success: bool
    message: str


class MFALoginRequest(BaseModel):
    """Request for second step of MFA login."""
    code: Optional[str] = Field(None, min_length=6, max_length=6, description="6-digit TOTP code")
    backup_code: Optional[str] = Field(None, description="One-time backup code")


class MFALoginResponse(BaseModel):
    """Response for successful MFA login."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


# ============================================================================
# Refresh Token Models
# ============================================================================

class RefreshTokenRequest(BaseModel):
    """Request to refresh access token."""
    refresh_token: str = Field(..., description="Valid refresh token")


class RefreshTokenResponse(BaseModel):
    """Response with new access token."""
    access_token: str
    refresh_token: str  # New rotated refresh token
    token_type: str = "bearer"
    expires_in: int


class DeviceInfo(BaseModel):
    """Information about a device/session."""
    device_id: str
    device_name: str
    ip_address: Optional[str] = None
    created_at: datetime
    last_used_at: Optional[datetime] = None
    is_current: bool = False  # True if this is the current device


class DeviceListResponse(BaseModel):
    """Response with list of active devices."""
    devices: List[DeviceInfo]
    total: int


class RevokeDeviceResponse(BaseModel):
    """Response after revoking a device."""
    success: bool
    message: str
    revoked_device_id: str


class LogoutAllResponse(BaseModel):
    """Response after logging out all devices."""
    success: bool
    message: str
    revoked_count: int


# ============================================================================
# API Key Models
# ============================================================================

class CreateAPIKeyRequest(BaseModel):
    """Request to create a new API key."""
    name: str = Field(..., max_length=255, description="Display name for the key")
    description: Optional[str] = Field(None, description="Optional description")
    scopes: List[str] = Field(default_factory=lambda: ["read:queries", "read:sessions"])
    expires_in_days: Optional[int] = Field(None, description="Days until expiry (None = no expiry)")


class CreateAPIKeyResponse(BaseModel):
    """Response with new API key (shown once!)."""
    key: str = Field(..., description="Full API key (ONLY shown at creation)")
    key_prefix: str = Field(..., description="Key prefix for display")
    name: str
    created_at: datetime
    message: str = "Save this key immediately - it will not be shown again"


class APIKeyItem(BaseModel):
    """Item in API keys list."""
    id: str
    key_prefix: str
    name: str
    description: Optional[str] = None
    scopes: List[str]
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class APIKeyListResponse(BaseModel):
    """Response with list of user's API keys."""
    keys: List[APIKeyItem]
    total: int


class UpdateAPIKeyRequest(BaseModel):
    """Request to update API key metadata."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    scopes: Optional[List[str]] = None


class RevokeAPIKeyResponse(BaseModel):
    """Response after revoking an API key."""
    success: bool
    message: str
    revoked_key_prefix: str


class APIKeyUsageResponse(BaseModel):
    """Response with API key usage statistics."""
    key_prefix: str
    calls_last_24h: int
    calls_last_30d: int
    last_used_at: Optional[datetime] = None


# ============================================================================
# RBAC Models
# ============================================================================

class PermissionItem(BaseModel):
    """A single permission."""
    id: str
    name: str
    resource: str
    action: str
    description: Optional[str] = None


class PermissionListResponse(BaseModel):
    """Response with list of all permissions."""
    permissions: List[PermissionItem]
    total: int


class CreateRoleRequest(BaseModel):
    """Request to create a new role."""
    name: str = Field(..., max_length=50, description="Role name (lowercase, alphanumeric + underscores)")
    description: Optional[str] = Field(None, description="Role description")
    permission_ids: List[str] = Field(..., description="Permission IDs to assign")


class RoleItem(BaseModel):
    """A role with permissions."""
    id: str
    name: str
    description: Optional[str] = None
    is_default: bool
    permissions: List[PermissionItem]
    created_at: datetime


class RoleListResponse(BaseModel):
    """Response with list of roles."""
    roles: List[RoleItem]
    total: int


class UpdateRoleRequest(BaseModel):
    """Request to update a role."""
    description: Optional[str] = None
    permission_ids: Optional[List[str]] = None


class AssignRoleRequest(BaseModel):
    """Request to assign role to user."""
    role_id: str


class AssignRoleResponse(BaseModel):
    """Response after role assignment."""
    success: bool
    message: str
    user_id: str
    role_id: str


class RemoveRoleResponse(BaseModel):
    """Response after role removal."""
    success: bool
    message: str
    user_id: str
    role_id: str
