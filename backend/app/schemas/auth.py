"""Authentication request/response schemas."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class SignupRequest(BaseModel):
    """User signup request."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    background_software: Optional[str] = Field(None, description="Software experience level")
    background_hardware: Optional[str] = Field(None, description="Hardware experience level")
    learning_goal: Optional[str] = Field(None, description="Learning goal")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "background_software": "Intermediate",
                "learning_goal": "Career",
            }
        }


class SigninRequest(BaseModel):
    """User signin request."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
            }
        }


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")


class UserProfile(BaseModel):
    """User profile response."""

    id: str
    email: str
    background_software: Optional[str]
    background_hardware: Optional[str]
    learning_goal: Optional[str]
    preferred_language: str
    difficulty_level: str
    email_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """User profile update request."""

    background_software: Optional[str] = None
    background_hardware: Optional[str] = None
    learning_goal: Optional[str] = None
    preferred_language: Optional[str] = None
    difficulty_level: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "difficulty_level": "Advanced",
                "preferred_language": "ur",
            }
        }
