"""
Pydantic schemas for request/response validation.

Defines data models for API contracts and internal data structures.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID

# Request schemas

class ChatRequest(BaseModel):
    """Request schema for /chat endpoint."""
    question: str = Field(..., min_length=1, max_length=500, description="User's question about the book")
    session_id: UUID = Field(..., description="UUID of the conversation session")
    selected_text: Optional[str] = Field(default=None, description="Optional: restrict answer to this passage")

    @field_validator("question")
    @classmethod
    def validate_question(cls, v):
        """Validate question is not just whitespace."""
        if not v or not v.strip():
            raise ValueError("Question cannot be empty or whitespace")
        return v.strip()


# Response schemas

class Citation(BaseModel):
    """Citation for a retrieved chunk."""
    section: str = Field(..., description="Book section name")
    url: str = Field(..., description="URL to the source")


class ChunkMetadata(BaseModel):
    """Metadata for a retrieved chunk."""
    url: str
    section: str
    chunk_id: str
    position: int
    embedding_score: float = Field(..., ge=0, le=1)


class RetrievedChunkResponse(BaseModel):
    """A single retrieved chunk from the RAG pipeline."""
    text: str = Field(..., description="The chunk text")
    metadata: ChunkMetadata


class ChatResponse(BaseModel):
    """Response schema for /chat endpoint."""
    answer: str = Field(..., description="Grounded answer synthesized from book content")
    citations: List[Citation] = Field(default_factory=list, description="Sources for the answer")
    retrieved_chunks: List[RetrievedChunkResponse] = Field(default_factory=list, description="All chunks used")


class SessionCreateResponse(BaseModel):
    """Response schema for POST /sessions endpoint."""
    session_id: UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatMessage(BaseModel):
    """A message in a conversation session."""
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    created_at: datetime


class SessionGetResponse(BaseModel):
    """Response schema for GET /sessions/{session_id} endpoint."""
    session_id: UUID
    messages: List[ChatMessage] = Field(default_factory=list, description="Messages in order")


class HealthResponse(BaseModel):
    """Response schema for GET /health endpoint."""
    status: str = Field(..., description="'healthy', 'degraded', or 'unhealthy'")
    services: dict = Field(default_factory=dict, description="Status of each service")


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
