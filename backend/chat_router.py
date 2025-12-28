"""
FastAPI Router for Chat Endpoint
Handles RAG query processing and response generation
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/chat", tags=["chat"])


class Source(BaseModel):
    """Source document reference"""
    url: str
    snippet: str
    chunk_position: Optional[str] = None
    similarity_score: Optional[float] = None


class QueryRequest(BaseModel):
    """Request body for chat endpoint"""
    query: str = Field(..., min_length=3, max_length=5000, description="User query")
    selected_text: Optional[str] = Field(None, description="Highlighted text from textbook")
    k: int = Field(5, ge=1, le=20, description="Number of chunks to retrieve")


class QueryResponse(BaseModel):
    """Response body from chat endpoint"""
    query: str
    response: str
    sources: List[Source]
    confidence: float = Field(..., ge=0, le=1)
    execution_time_ms: int
    status: str = Field(..., description="success, error, or no_results")
    error: Optional[str] = None


@router.post("/", response_model=QueryResponse)
async def chat_query(request: QueryRequest) -> QueryResponse:
    """
    Main chat endpoint

    Processes user query through RAG agent:
    1. Validates input query
    2. Retrieves context chunks from Qdrant
    3. Synthesizes response via OpenAI Agent (if enabled)
    4. Returns response with sources and confidence

    Args:
        request: QueryRequest with query text and optional selected_text

    Returns:
        QueryResponse with synthesized answer, sources, confidence, and metadata

    Raises:
        HTTPException: On validation, retrieval, or synthesis errors
    """
    try:
        logger.info(f"Received query: {request.query[:100]}...")

        # TODO: Phase 2 - Integrate with agent.py
        # This will be implemented to call agent.run_query()
        # For now, return skeleton response

        response = QueryResponse(
            query=request.query,
            response="Chat endpoint skeleton. Phase 2 implementation required.",
            sources=[],
            confidence=0.0,
            execution_time_ms=0,
            status="error",
            error="Chat endpoint not yet implemented. Complete Phase 2 integration."
        )

        return response

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    Verifies backend is running and accessible
    """
    return {
        "status": "healthy",
        "message": "Chat endpoint is running",
    }
