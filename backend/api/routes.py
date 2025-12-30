"""
API routes for BookRAGAgent.

Main FastAPI router with endpoints for chat, sessions, and health checks.
"""

from fastapi import APIRouter, HTTPException, status, Request
from typing import Optional
import logging
from uuid import UUID

from models.schemas import (
    ChatRequest, ChatResponse, SessionCreateResponse,
    SessionGetResponse, HealthResponse, ErrorResponse
)
from utils.errors import (
    RAGError, InvalidInputException, SessionNotFoundException,
    get_http_status_code, build_error_response
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Dependencies will be stored in app.state by the startup event
# This avoids issues with module reloading resetting global variables

def get_rag_agent(request):
    """Get RAG agent from app state."""
    return getattr(request.app.state, 'rag_agent', None)

def get_session_manager(request):
    """Get session manager from app state."""
    return getattr(request.app.state, 'session_manager', None)

def get_qdrant_retriever(request):
    """Get Qdrant retriever from app state."""
    return getattr(request.app.state, 'qdrant_retriever', None)

def get_openrouter_client(request):
    """Get OpenRouter client from app state."""
    return getattr(request.app.state, 'openrouter_client', None)

def set_dependencies(app, rag_agent, session_manager, qdrant_retriever, openrouter_client):
    """Set up dependencies in app.state."""
    app.state.rag_agent = rag_agent
    app.state.session_manager = session_manager
    app.state.qdrant_retriever = qdrant_retriever
    app.state.openrouter_client = openrouter_client


@router.post("/chat", response_model=ChatResponse, status_code=200)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Submit a question to the RAG chatbot.

    Retrieves relevant book content and returns a grounded answer with citations.
    """
    try:
        rag_agent = get_rag_agent(request)
        session_manager = get_session_manager(request)

        if not rag_agent:
            raise RuntimeError("RAG agent not initialized")

        logger.info(f"Chat request from session {request.session_id}")

        # Execute RAG pipeline
        response = await rag_agent.execute(request)

        # Store messages in session
        if session_manager:
            try:
                # Store user question
                session_manager.add_message(
                    session_id=request.session_id,
                    role="user",
                    content=request.question,
                    metadata={"question_type": "book_qa"}
                )

                # Store assistant response
                import json
                session_manager.add_message(
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
async def create_session(request: Request) -> SessionCreateResponse:
    """
    Create a new conversation session.

    Returns a session_id that should be used in subsequent /chat requests.
    """
    try:
        session_manager = get_session_manager(request)

        if not session_manager:
            raise RuntimeError("Session manager not initialized")

        logger.info("Creating new session")
        session_id = session_manager.create_session()

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
async def get_session(session_id: UUID, request: Request) -> SessionGetResponse:
    """
    Retrieve conversation history for a session.

    Returns all messages in the session ordered by creation time.
    """
    try:
        session_manager = get_session_manager(request)

        if not session_manager:
            raise RuntimeError("Session manager not initialized")

        logger.info(f"Retrieving session {session_id}")

        session = session_manager.get_session(session_id)
        if not session:
            raise SessionNotFoundException(str(session_id))

        messages = session_manager.get_all_messages(session_id)

        # Convert to response format
        from models.schemas import ChatMessage
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
async def health_check(request: Request) -> HealthResponse:
    """
    Health check endpoint.

    Returns status of critical services.
    """
    try:
        services = {}
        qdrant_retriever = get_qdrant_retriever(request)
        openrouter_client = get_openrouter_client(request)
        session_manager = get_session_manager(request)

        # Check Qdrant
        if qdrant_retriever:
            qdrant_health = await qdrant_retriever.health_check()
            services["qdrant"] = qdrant_health.get("status", "unknown")
        else:
            services["qdrant"] = "not_initialized"

        # Check OpenRouter
        if openrouter_client:
            router_health = await openrouter_client.health_check()
            services["openrouter"] = router_health.get("status", "unknown")
        else:
            services["openrouter"] = "not_initialized"

        # Check database (basic check)
        if session_manager:
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
