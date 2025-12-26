"""Content and chapter models."""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.core.database import Base


class Chapter(Base):
    """Chapter content model."""

    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Content info
    title = Column(String, nullable=False)
    module = Column(String, nullable=False, index=True)  # 'ROS 2', 'Gazebo/Unity', 'Isaac', 'VLA'
    order_num = Column(Integer)

    # File and content
    content_path = Column(String)  # Path to MDX file
    content_hash = Column(String)  # Hash for change detection

    # Status
    published = Column(Boolean, default=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    progress = relationship("UserProgress", back_populates="chapter", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Chapter id={self.id} title={self.title} module={self.module}>"


class UserProgress(Base):
    """User progress tracking for chapters."""

    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False, index=True)

    # Progress info
    status = Column(String, default="not_started")  # 'not_started', 'in_progress', 'completed'
    quiz_score = Column(Float, nullable=True)  # 0.0 to 100.0
    time_spent_seconds = Column(Integer, default=0)  # Time spent on chapter

    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    last_accessed = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="progress")
    chapter = relationship("Chapter", back_populates="progress")

    def __repr__(self) -> str:
        return f"<UserProgress user_id={self.user_id} chapter_id={self.chapter_id} status={self.status}>"
