"""Chat and conversation schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChatQuery(BaseModel):
    """User chat query request."""

    query: str = Field(..., description="User question")
    session_id: Optional[int] = Field(None, description="Chat session ID (optional, creates new if not provided)")
    chapter_context: Optional[str] = Field(None, description="Current chapter context")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "How do I set up ROS 2 on Ubuntu?",
                "chapter_context": "Chapter 1.2",
            }
        }


class ChatMessageResponse(BaseModel):
    """Chat message response."""

    id: int
    role: str
    content: str
    sources: Optional[List[dict]] = None
    confidence: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "role": "assistant",
                "content": "Based on Chapter 1.2, you can install ROS 2 by...",
                "sources": [{"chapter": "1.2", "section": "Installation"}],
                "confidence": 0.95,
            }
        }


class ChatResponse(BaseModel):
    """RAG chatbot response."""

    answer: str = Field(..., description="Generated answer")
    sources: List[str] = Field(default=[], description="Source references")
    confidence: float = Field(..., description="Confidence score 0.0-1.0")
    session_id: int = Field(..., description="Chat session ID")

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Based on Chapter 1.2, ROS 2 is installed using apt-get...",
                "sources": ["Chapter 1.2: Installation", "Chapter 1.3: Configuration"],
                "confidence": 0.92,
                "session_id": 123,
            }
        }


class ChatSessionResponse(BaseModel):
    """Chat session response."""

    id: int
    title: Optional[str]
    topic: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True
