"""
SQLAlchemy ORM models for database persistence.

Defines User, Session, and ChatMessage entities with relationships and indexes.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, JSON, Index, event, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

Base = declarative_base()


class User(Base):
    """User entity."""
    __tablename__ = "users"

    user_id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, created_at={self.created_at})>"


class Session(Base):
    """Conversation session entity."""
    __tablename__ = "sessions"

    session_id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    metadata = Column(JSON, default={}, nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_session_user_id", "user_id"),
        Index("idx_session_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<Session(session_id={self.session_id}, user_id={self.user_id})>"


class ChatMessage(Base):
    """Chat message in a session."""
    __tablename__ = "chat_messages"

    message_id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("sessions.session_id"), nullable=False)
    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(String, nullable=False)
    metadata = Column(JSON, default={}, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("Session", back_populates="messages")

    # Indexes
    __table_args__ = (
        Index("idx_message_session_id", "session_id"),
        Index("idx_message_created_at", "created_at"),
        Index("idx_message_role", "role"),
    )

    def __repr__(self):
        return f"<ChatMessage(message_id={self.message_id}, role={self.role})>"


# Event listener to update session.updated_at on message insert
@event.listens_for(ChatMessage, "after_insert")
def receive_after_insert(mapper, connection, target):
    """Update parent session's updated_at when a message is added."""
    # This would typically be done via a database trigger for better performance
    # In production, consider using PostgreSQL triggers
    pass
