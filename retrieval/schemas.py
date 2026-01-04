"""
Data schemas for retrieval layer.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field, validator


class ChunkMetadata(BaseModel):
    """Metadata for a retrieved chunk."""

    chapter: str = Field(..., description="Chapter name")
    section: str = Field(..., description="Section name")
    source_file: str = Field(..., description="Source file path")
    chunk_index: int = Field(..., ge=0, description="Index of this chunk")
    total_chunks: int = Field(..., ge=1, description="Total chunks in source")
    token_count: Optional[int] = Field(None, ge=0, description="Token count")

    @validator("chunk_index")
    def validate_chunk_index(cls, v, values):
        """Ensure chunk_index < total_chunks."""
        if "total_chunks" in values and v >= values["total_chunks"]:
            raise ValueError("chunk_index must be less than total_chunks")
        return v


class RetrievedChunk(BaseModel):
    """A single retrieved chunk with metadata and score."""

    text: str = Field(..., min_length=1, description="Chunk text content")
    metadata: ChunkMetadata = Field(..., description="Chunk metadata")
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")


class RetrievalRequest(BaseModel):
    """Request schema for retrieval."""

    query: str = Field(..., min_length=1, max_length=1000, description="User query")
    retrieval_mode: Literal["normal", "selected_text"] = Field(
        default="normal",
        description="Retrieval mode"
    )
    selected_text: Optional[str] = Field(
        None,
        max_length=2000,
        description="Selected text (required for selected_text mode)"
    )
    top_k: Optional[int] = Field(
        None,
        ge=1,
        le=20,
        description="Override default top_k"
    )
    score_threshold: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Override default score threshold"
    )

    @validator("selected_text")
    def validate_selected_text(cls, v, values):
        """Validate selected_text is provided when mode is selected_text."""
        if values.get("retrieval_mode") == "selected_text" and not v:
            raise ValueError("selected_text is required when retrieval_mode is 'selected_text'")
        return v


class RetrievalResponse(BaseModel):
    """Response schema for retrieval."""

    chunks: list[RetrievedChunk] = Field(..., description="Retrieved chunks")
    metadata: dict = Field(..., description="Response metadata")
