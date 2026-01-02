"""
API routes for BookRAGAgent.

Main FastAPI router with endpoints for chat, sessions, and health checks.
"""

from fastapi import APIRouter, HTTPException, status, Request
from typing import Optional
import logging
from uuid import UUID
from datetime import datetime

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

def get_gemini_client(request):
    """Get Gemini client from app state."""
    return getattr(request.app.state, 'gemini_client', None)

def set_dependencies(app, rag_agent, session_manager, qdrant_retriever, gemini_client):
    """Set up dependencies in app.state."""
    app.state.rag_agent = rag_agent
    app.state.session_manager = session_manager
    app.state.qdrant_retriever = qdrant_retriever
    app.state.gemini_client = gemini_client


@router.post("/chat", response_model=ChatResponse, status_code=200)
async def chat(chat_request: ChatRequest, request: Request) -> ChatResponse:
    """
    Submit a question to the RAG chatbot.

    Retrieves relevant book content and returns a grounded answer with citations.
    Always returns valid JSON response, even on errors.
    """
    session_id = str(chat_request.session_id)

    try:
        logger.info(f"=== CHAT REQUEST START ===")
        logger.info(f"Session: {session_id}, Question: {chat_request.question[:100]}...")

        # Get dependencies
        rag_agent = get_rag_agent(request)
        session_manager = get_session_manager(request)

        if not rag_agent:
            logger.error("RAG agent is not initialized in app.state")
            raise RuntimeError("RAG agent not initialized - backend startup incomplete")

        logger.info(f"Dependencies retrieved. RAG agent ready.")

        # Execute RAG pipeline with error recovery
        try:
            logger.info(f"Executing RAG pipeline...")
            response = await rag_agent.execute(chat_request)
            logger.info(f"RAG pipeline completed. Answer length: {len(response.answer)}")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"RAG agent execution failed: {error_msg}", exc_info=True)

            # Provide more specific error messages based on the error type
            if "Qdrant" in error_msg or "vector" in error_msg.lower():
                user_message = "Unable to search the knowledge base. Please try again in a moment."
            elif "embed" in error_msg.lower() or "cohere" in error_msg.lower():
                user_message = "Unable to process your question at the moment. Please try again."
            elif "Gemini" in error_msg or "API" in error_msg:
                user_message = "Unable to generate an answer at the moment. Please try again."
            else:
                user_message = "I encountered an error while processing your question. Please try again."

            logger.warning(f"Returning fallback response: {user_message}")
            response = ChatResponse(
                answer=user_message,
                citations=[],
                retrieved_chunks=[]
            )
            return response

        # Store messages in session (non-blocking failure)
        if session_manager:
            try:
                logger.debug(f"Storing messages in session {session_id}...")
                # Store user question
                session_manager.add_message(
                    session_id=session_id,
                    role="user",
                    content=chat_request.question,
                    metadata={"question_type": "book_qa"}
                )

                # Store assistant response
                import json
                session_manager.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=json.dumps({
                        "answer": response.answer,
                        "citations": [{"section": c.section, "url": c.url} for c in response.citations],
                    }),
                    metadata={"response_type": "grounded_answer"}
                )
                logger.debug(f"Session messages stored successfully")
            except Exception as e:
                logger.warning(f"Non-critical: Failed to store messages in session: {e}")
        else:
            logger.debug("Session manager not available - skipping session storage")

        logger.info(f"=== CHAT REQUEST COMPLETE ===")
        return response

    except RAGError as exc:
        logger.error(f"RAG error: {exc.message}")
        raise HTTPException(
            status_code=exc.http_status,
            detail=build_error_response(exc)
        )
    except Exception as exc:
        # Comprehensive error logging for debugging
        logger.error(f"=== CRITICAL ERROR IN /CHAT ENDPOINT ===")
        logger.error(f"Session ID: {session_id}")
        logger.error(f"Exception type: {type(exc).__name__}")
        logger.error(f"Exception message: {str(exc)[:500]}")
        logger.error(f"Exception args: {exc.args}")

        import traceback
        tb_str = traceback.format_exc()
        logger.error(f"Full traceback:\n{tb_str[:1000]}")  # Limit traceback length
        logger.error(f"=== END CRITICAL ERROR ===")

        # IMPORTANT: Always return valid JSON response (not HTTPException)
        # This ensures frontend gets a proper ChatResponse even on backend errors
        return ChatResponse(
            answer="I encountered an unexpected error while processing your request. Please try again later.",
            citations=[],
            retrieved_chunks=[]
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
            session_id=UUID(session_id)
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
        gemini_client = get_gemini_client(request)
        session_manager = get_session_manager(request)

        # Check Qdrant - just verify it's initialized, skip API calls
        if qdrant_retriever:
            services["qdrant"] = "ok"  # Assume ok if initialized
        else:
            services["qdrant"] = "not_initialized"

        # Check Gemini - just verify it's initialized, skip API calls
        if gemini_client:
            services["gemini"] = "ok"  # Assume ok if initialized
        else:
            services["gemini"] = "not_initialized"

        # Check database
        if session_manager:
            services["database"] = "ok"
        else:
            services["database"] = "not_initialized"

        # Determine overall status
        all_ok = all(v == "ok" for v in services.values())
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
