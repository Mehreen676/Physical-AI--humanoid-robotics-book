"""FastAPI routes for Agentic RAG."""

import time
import sys
import os
from fastapi import APIRouter, HTTPException

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from backend_v3.models import (
    ChatRequest,
    ChatResponse,
    SessionCreate,
    SessionResponse,
    SessionHistory,
    HealthResponse
)
from backend_v3.agent import (
    GeminiAgent,
    ContextFormatter,
    SelectedTextHandler,
    AnswerGenerator
)
from backend_v3.storage import get_database
from backend_v3.utils import handle_errors, StructuredLogger
from retrieval import SemanticRetriever
from datetime import datetime

router = APIRouter()

# Global instances (initialized in main.py)
_agent: GeminiAgent = None
_retriever: SemanticRetriever = None


def set_agent(agent: GeminiAgent):
    """Set global agent instance."""
    global _agent
    _agent = agent


def set_retriever(retriever: SemanticRetriever):
    """Set global retriever instance."""
    global _retriever
    _retriever = retriever


def get_agent() -> GeminiAgent:
    """Get global agent instance."""
    if _agent is None:
        raise RuntimeError("Agent not initialized")
    return _agent


def get_retriever() -> SemanticRetriever:
    """Get global retriever instance."""
    if _retriever is None:
        raise RuntimeError("Retriever not initialized")
    return _retriever


@router.post("/chat", response_model=ChatResponse)
@handle_errors
async def chat(request: ChatRequest):
    """
    Main chat endpoint using Gemini agent.

    Args:
        request: Chat request with question and optional session_id

    Returns:
        ChatResponse with answer and citations

    Raises:
        HTTPException: If validation or processing fails
    """
    start_time = time.time()

    StructuredLogger.log_event("chat_start", question=request.question)

    try:
        # Validate selected text if needed
        SelectedTextHandler.validate_selected_text(
            request.selected_text,
            request.retrieval_mode
        )

        # Retrieve chunks
        retriever = get_retriever()
        chunks = retriever.retrieve(
            query=request.question,
            retrieval_mode=request.retrieval_mode,
            selected_text=request.selected_text
        )

        StructuredLogger.log_event(
            "retrieval_complete",
            num_chunks=len(chunks)
        )

        # Format context
        if request.retrieval_mode == "selected_text":
            context = SelectedTextHandler.prepare_selected_text_context(
                request.question,
                request.selected_text,
                chunks
            )
        else:
            context = ContextFormatter.format_chunks(chunks)

        # Get conversation history
        db = get_database()
        session_id = request.session_id

        if session_id and db.session_exists(session_id):
            history = db.get_conversation_history(session_id)
        else:
            # Create new session
            session_id = db.create_session()
            history = []

        # Generate answer
        agent = get_agent()
        generator = AnswerGenerator(agent)

        result = generator.generate_answer(
            question=request.question,
            context=context,
            conversation_history=history
        )

        StructuredLogger.log_event(
            "answer_generated",
            is_refusal=result["is_refusal"]
        )

        # Extract citations
        citations = generator.extract_citations(result["answer"], chunks)

        # Store turn (handle database errors gracefully)
        try:
            chunk_ids = [str(i) for i in range(len(chunks))]
            db.add_turn(
                session_id=session_id,
                question=request.question,
                retrieval_mode=request.retrieval_mode,
                context_chunk_ids=chunk_ids,
                answer=result["answer"],
                grounded=result["grounded"]
            )
        except Exception as e:
            StructuredLogger.log_event(
                "database_error",
                level="WARNING",
                error=str(e)
            )
            # Continue anyway - answer still returned

        # Log latency
        latency_ms = (time.time() - start_time) * 1000
        StructuredLogger.log_latency("chat_request", latency_ms)

        return ChatResponse(
            session_id=session_id,
            answer=result["answer"],
            citations=citations,
            retrieval_mode=request.retrieval_mode,
            grounded=result["grounded"],
            metadata={
                "latency_ms": round(latency_ms, 2),
                "num_chunks": len(chunks),
                "is_refusal": result["is_refusal"]
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        StructuredLogger.log_event(
            "chat_error",
            level="ERROR",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/sessions", response_model=SessionResponse)
async def create_session(request: SessionCreate):
    """
    Create a new conversation session.

    Args:
        request: Session creation request

    Returns:
        SessionResponse with session_id
    """
    try:
        db = get_database()
        session_id = db.create_session(user_id=request.user_id)

        return SessionResponse(
            session_id=session_id,
            created_at=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("/sessions/{session_id}", response_model=SessionHistory)
async def get_session(session_id: str):
    """
    Get conversation history for a session.

    Args:
        session_id: Session identifier

    Returns:
        SessionHistory with all turns

    Raises:
        HTTPException: If session not found
    """
    try:
        db = get_database()

        if not db.session_exists(session_id):
            raise HTTPException(status_code=404, detail="Session not found")

        history = db.get_conversation_history(session_id)

        # Get session creation time (approximate from first turn or now)
        created_at = history[0]["created_at"] if history else datetime.utcnow()

        return SessionHistory(
            session_id=session_id,
            created_at=created_at,
            turns=history
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns:
        HealthResponse with component status
    """
    try:
        retriever = get_retriever()
        health = retriever.health_check()

        return HealthResponse(
            status="healthy",
            components={
                "qdrant": health["qdrant"],
                "embeddings": health["embedding_service"],
                "agent": True,
                "database": True
            },
            version="3.0.0"
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            components={
                "qdrant": False,
                "embeddings": False,
                "agent": False,
                "database": False
            },
            version="3.0.0"
        )
