"""Content and chapter schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ChapterResponse(BaseModel):
    """Chapter content response."""

    id: int
    title: str
    module: str
    order_num: Optional[int]
    published: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "Introduction to ROS 2",
                "module": "ROS 2",
                "order_num": 1,
                "published": True,
            }
        }


class ProgressResponse(BaseModel):
    """User progress response."""

    id: int
    chapter_id: int
    status: str  # 'not_started', 'in_progress', 'completed'
    quiz_score: Optional[float]
    time_spent_seconds: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    last_accessed: datetime

    class Config:
        from_attributes = True


class ProgressUpdate(BaseModel):
    """Progress update request."""

    chapter_id: int = Field(..., description="Chapter ID")
    status: Optional[str] = Field(None, description="Progress status")
    quiz_score: Optional[float] = Field(None, description="Quiz score 0-100")
    time_spent_seconds: Optional[int] = Field(None, description="Time spent on chapter")

    class Config:
        json_schema_extra = {
            "example": {
                "chapter_id": 1,
                "status": "completed",
                "quiz_score": 85.0,
                "time_spent_seconds": 1800,
            }
        }
