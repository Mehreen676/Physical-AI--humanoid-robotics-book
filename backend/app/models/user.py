"""User and authentication models."""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.core.database import Base


class User(Base):
    """User model for authentication and profile."""

    __tablename__ = "users"

    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Authentication
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    # User Profile
    background_software = Column(String, nullable=True)  # Beginner, Intermediate, Advanced
    background_hardware = Column(String, nullable=True)  # None, Some, Extensive
    learning_goal = Column(String, nullable=True)  # Career, Hobby, Academic, Research

    # Preferences
    preferred_language = Column(String, default="en")  # 'en' or 'ur'
    difficulty_level = Column(String, default="Intermediate")  # Beginner, Intermediate, Advanced

    # Status
    email_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("UserProgress", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"


class UserPreferences(Base):
    """User preferences and settings."""

    __tablename__ = "user_preferences"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)

    # Preferences
    difficulty_level = Column(String, default="Intermediate")
    language = Column(String, default="en")
    theme = Column(String, default="light")  # 'light' or 'dark'
    notifications_enabled = Column(Boolean, default=True)

    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="preferences")

    def __repr__(self) -> str:
        return f"<UserPreferences user_id={self.user_id} language={self.language}>"
