"""Pydantic schemas for API requests/responses."""

from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""

    session_id: Optional[str] = Field(None, description="Session ID for conversation history")
    question: str = Field(..., min_length=1, max_length=1000, description="User question")
    retrieval_mode: Literal["normal", "selected_text"] = Field(
        default="normal",
        description="Retrieval mode: normal or selected_text"
    )
    selected_text: Optional[str] = Field(
        None,
        max_length=2000,
        description="Selected text (required for selected_text mode)"
    )


class Citation(BaseModel):
    """Source citation."""

    chapter: str
    section: str
    text_snippet: str
    score: float


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""

    session_id: str = Field(..., description="Session ID")
    answer: str = Field(..., description="Generated answer")
    citations: list[Citation] = Field(default_factory=list, description="Source citations")
    retrieval_mode: str = Field(..., description="Retrieval mode used")
    grounded: bool = Field(..., description="Whether answer is fully grounded")
    metadata: dict = Field(default_factory=dict, description="Response metadata")


class SessionCreate(BaseModel):
    """Request schema for creating a session."""

    user_id: Optional[str] = Field(None, description="Optional user ID")


class SessionResponse(BaseModel):
    """Response schema for session creation."""

    session_id: str
    created_at: datetime


class ConversationTurn(BaseModel):
    """Single conversation turn."""

    question: str
    answer: str
    citations: list[Citation]
    timestamp: datetime
    retrieval_mode: str


class SessionHistory(BaseModel):
    """Complete session history."""

    session_id: str
    created_at: datetime
    turns: list[ConversationTurn]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    components: dict[str, bool]
    version: str
