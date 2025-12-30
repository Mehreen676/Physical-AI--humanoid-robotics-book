"""
API routes for BookRAGAgent.

Main FastAPI router with endpoints for chat, sessions, and health checks.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Optional
import logging
from uuid import UUID

from backend.models.schemas import (
    ChatRequest, ChatResponse, SessionCreateResponse,
    SessionGetResponse, HealthResponse, ErrorResponse
)
from backend.utils.errors import (
    RAGError, InvalidInputException, SessionNotFoundException,
    get_http_status_code, build_error_response
)

logger = logging.getLogger(__name__)
router = APIRouter()

# These will be injected by the application
_rag_agent = None
_session_manager = None
_qdrant_retriever = None
_openrouter_client = None


def set_dependencies(rag_agent, session_manager, qdrant_retriever, openrouter_client):
    """Set up dependencies for routes."""
    global _rag_agent, _session_manager, _qdrant_retriever, _openrouter_client
    _rag_agent = rag_agent
    _session_manager = session_manager
    _qdrant_retriever = qdrant_retriever
    _openrouter_client = openrouter_client


@router.post("/chat", response_model=ChatResponse, status_code=200)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Submit a question to the RAG chatbot.

    Retrieves relevant book content and returns a grounded answer with citations.
    """
    try:
        if not _rag_agent:
            raise RuntimeError("RAG agent not initialized")

        logger.info(f"Chat request from session {request.session_id}")

        # Execute RAG pipeline
        response = await _rag_agent.execute(request)

        # Store messages in session
        if _session_manager:
            try:
                # Store user question
                _session_manager.add_message(
                    session_id=request.session_id,
                    role="user",
                    content=request.question,
                    metadata={"question_type": "book_qa"}
                )

                # Store assistant response
                import json
                _session_manager.add_message(
                    session_id=request.session_id,
                    role="assistant",
                    content=json.dumps({
                        "answer": response.answer,
                        "citations": [{"section": c.section, "url": c.url} for c in response.citations],
                    }),
                    metadata={"response_type": "grounded_answer"}
                )
            except Exception as e:
                logger.warning(f"Failed to store messages in session: {e}")

        return response

    except RAGError as exc:
        logger.error(f"RAG error: {exc.message}")
        raise HTTPException(
            status_code=exc.http_status,
            detail=build_error_response(exc)
        )
    except Exception as exc:
        logger.error(f"Unexpected error in /chat: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred processing your request."
            }
        )


@router.post("/sessions", response_model=SessionCreateResponse, status_code=201)
async def create_session() -> SessionCreateResponse:
    """
    Create a new conversation session.

    Returns a session_id that should be used in subsequent /chat requests.
    """
    try:
        if not _session_manager:
            raise RuntimeError("Session manager not initialized")

        logger.info("Creating new session")
        session_id = _session_manager.create_session()

        return SessionCreateResponse(
            session_id=UUID(session_id),
            created_at=None  # Will be set by pydantic
        )

    except Exception as exc:
        logger.error(f"Failed to create session: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Session Creation Failed",
                "message": "Could not create a new conversation session."
            }
        )


@router.get("/sessions/{session_id}", response_model=SessionGetResponse, status_code=200)
async def get_session(session_id: UUID) -> SessionGetResponse:
    """
    Retrieve conversation history for a session.

    Returns all messages in the session ordered by creation time.
    """
    try:
        if not _session_manager:
            raise RuntimeError("Session manager not initialized")

        logger.info(f"Retrieving session {session_id}")

        session = _session_manager.get_session(session_id)
        if not session:
            raise SessionNotFoundException(str(session_id))

        messages = _session_manager.get_all_messages(session_id)

        # Convert to response format
        from backend.models.schemas import ChatMessage
        chat_messages = [
            ChatMessage(
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at
            )
            for msg in messages
        ]

        return SessionGetResponse(
            session_id=session_id,
            messages=chat_messages
        )

    except SessionNotFoundException as exc:
        logger.warning(f"Session not found: {session_id}")
        raise HTTPException(
            status_code=404,
            detail=build_error_response(exc)
        )
    except Exception as exc:
        logger.error(f"Failed to retrieve session: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Session Retrieval Failed",
                "message": "Could not retrieve the session."
            }
        )


@router.get("/health", response_model=HealthResponse, status_code=200)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns status of critical services.
    """
    try:
        services = {}

        # Check Qdrant
        if _qdrant_retriever:
            qdrant_health = await _qdrant_retriever.health_check()
            services["qdrant"] = qdrant_health.get("status", "unknown")
        else:
            services["qdrant"] = "not_initialized"

        # Check OpenRouter
        if _openrouter_client:
            router_health = await _openrouter_client.health_check()
            services["openrouter"] = router_health.get("status", "unknown")
        else:
            services["openrouter"] = "not_initialized"

        # Check database (basic check)
        if _session_manager:
            try:
                services["database"] = "ok"
            except:
                services["database"] = "error"
        else:
            services["database"] = "not_initialized"

        # Determine overall status
        all_ok = all(v in ["ok", "unknown"] for v in services.values())
        overall_status = "healthy" if all_ok else "degraded"

        return HealthResponse(
            status=overall_status,
            services=services
        )

    except Exception as exc:
        logger.error(f"Health check failed: {exc}", exc_info=True)
        return HealthResponse(
            status="unhealthy",
            services={"error": str(exc)}
        )
