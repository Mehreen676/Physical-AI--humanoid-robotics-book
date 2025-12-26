"""Chat and conversation models."""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class ChatSession(Base):
    """Chat session for user conversations."""

    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Session info
    title = Column(String, nullable=True)
    topic = Column(String, nullable=True)  # 'ROS 2', 'Gazebo', 'Isaac', 'VLA'

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ChatSession id={self.id} user_id={self.user_id} topic={self.topic}>"


class ChatMessage(Base):
    """Individual messages in a chat session."""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)

    # Message content
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(String, nullable=False)

    # RAG metadata
    sources = Column(JSON, nullable=True)  # Array of source references
    confidence = Column(Float, nullable=True)  # 0.0 to 1.0
    metadata = Column(JSON, nullable=True)  # Additional metadata

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self) -> str:
        return f"<ChatMessage id={self.id} session_id={self.session_id} role={self.role}>"
