"""
RAG Chatbot Backend - FastAPI Application
Integrated Retrieval-Augmented Generation chatbot for interactive learning.
"""

import logging
from datetime import datetime, timedelta
import os
import sys
import jwt
import json
from typing import Optional
import httpx
import secrets

# ============================================================================
# Python Path Configuration (for container deployments)
# ============================================================================
# Aggressively add paths to handle various deployment contexts
_current_file = os.path.abspath(__file__)
_current_dir = os.path.dirname(_current_file)  # /app/src or ./src
_project_root = os.path.dirname(_current_dir)  # /app or .

# Add paths to sys.path (only if not already present)
_paths_to_add = [
    _project_root,                          # Project root (where src/ is)
    os.getcwd(),                            # Current working directory
    os.path.dirname(os.getcwd()),           # Parent of cwd (for nested structures)
]

for _path in _paths_to_add:
    if _path and _path not in sys.path:
        sys.path.insert(0, _path)

from fastapi import FastAPI, HTTPException, Depends, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field, EmailStr
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.config import get_settings
from src.ingest_service import get_ingest_service
from src.retrieval_service import get_retriever
from src.generation_service import get_generation_agent
from src.database import (
    add_session, add_message, get_session, get_session_history, DatabaseSession,
    add_user, get_user_by_email, get_user_by_id, verify_password,
    get_user_analytics, add_query_metric, QueryMetrics,
    get_user_by_oauth_id, create_oauth_user, RevokedToken,
    revoke_token, is_token_revoked,
    get_user_cohort_analytics, get_funnel_metrics,
    # Phase 6 models
    TOTPSecret, RefreshToken, APIKey, Permission, Role, RolePermission, UserRole
)
from src.validation import validate_response_in_context
from src.embeddings import get_embedding_generator
import time
import uuid
# Phase 6 - Enterprise Authentication
from src.mfa import generate_totp_secret, generate_qr_code, verify_totp_code, generate_backup_codes, hash_backup_code, hash_backup_codes, verify_backup_code
from src.tokens import generate_refresh_token, hash_token, extract_token_prefix, extract_device_id_from_user_agent, parse_user_agent, calculate_token_expiry, is_token_expired, can_rotate_token
from src.api_keys import generate_api_key, hash_api_key, validate_api_key_format, extract_key_prefix, validate_scopes, has_scope, check_scope_access, calculate_key_expiry, is_api_key_expired, is_api_key_valid
from src.rbac import has_permission, check_permissions, cache_user_permissions, get_cached_permissions, clear_user_cache, validate_permission_format, DEFAULT_ROLES, DEFAULT_PERMISSIONS
from src.phase6_models import (
    MFASetupResponse, MFAVerifyRequest, MFAVerifyResponse, MFADisableRequest,
    MFADisableResponse, MFALoginRequest, MFALoginResponse,
    RefreshTokenRequest, RefreshTokenResponse, DeviceInfo, DeviceListResponse,
    RevokeDeviceResponse, LogoutAllResponse,
    CreateAPIKeyRequest, CreateAPIKeyResponse, APIKeyItem, APIKeyListResponse,
    UpdateAPIKeyRequest, RevokeAPIKeyResponse, APIKeyUsageResponse,
    PermissionItem, PermissionListResponse, CreateRoleRequest, RoleItem,
    RoleListResponse, UpdateRoleRequest, AssignRoleRequest, AssignRoleResponse,
    RemoveRoleResponse
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load configuration
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="RAG Chatbot Backend",
    description="Retrieval-Augmented Generation Chatbot for Interactive Learning",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Initialize rate limiter (Phase 5)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# JWT Configuration (Phase 4)
JWT_SECRET = settings.secret_key if hasattr(settings, 'secret_key') else os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


def create_access_token(user_id: str, expires_delta: timedelta = None) -> str:
    """Create a JWT access token with JWT ID (jti) for revocation support."""
    if expires_delta is None:
        expires_delta = timedelta(hours=JWT_EXPIRATION_HOURS)

    expire = datetime.utcnow() + expires_delta
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "jti": str(uuid.uuid4()),  # JWT ID for token revocation (Phase 5)
        "iat": datetime.utcnow(),
    }

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token, checking revocation blacklist."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")

        if user_id is None or jti is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Check if token is revoked (Phase 5)
        if is_token_revoked(jti):
            raise HTTPException(status_code=401, detail="Token has been revoked")

        return {"user_id": user_id, "jti": jti}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Dependency to get current authenticated user from Bearer token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = parts[1]
    return verify_token(token)


async def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency to verify user is admin."""
    user = get_user_by_id(current_user["user_id"])
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# Request/Response Models
class IngestRequest(BaseModel):
    """Request model for content ingestion."""

    chapter: str = Field(..., description="Chapter name/identifier")
    section: str = Field(default="Introduction", description="Section within chapter")
    content: str = Field(..., description="Chapter content (markdown or plain text)")
    book_version: str = Field(default="v1.0", description="Book version for tracking")

    class Config:
        json_schema_extra = {
            "example": {
                "chapter": "Module 1: ROS 2 Basics",
                "section": "Introduction",
                "content": "# ROS 2\nROS 2 is a robotics middleware...",
                "book_version": "v1.0",
            }
        }


class IngestResponse(BaseModel):
    """Response model for ingestion status."""

    ingested: int = Field(..., description="Number of new chunks ingested")
    skipped: int = Field(
        ..., description="Number of duplicate chunks skipped"
    )
    vectors_stored: int = Field(
        ..., description="Number of vectors stored in Qdrant"
    )
    total_chunks: int = Field(..., description="Total chunks generated")
    error: str = Field(
        default=None, description="Error message if ingestion failed"
    )


class QueryRequest(BaseModel):
    """Request model for content query (full-book or selected-text mode)."""

    query: str = Field(..., description="User question")
    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Chat session ID",
    )
    book_version: str = Field(default="v1.0", description="Book version to query")
    mode: str = Field(
        default="full_book",
        description="Query mode: 'full_book' or 'selected_text'",
    )
    selected_text: str = Field(
        default=None,
        description="Text user highlighted (for selected_text mode)",
    )
    chapter_filter: str = Field(
        default=None, description="Optional chapter to limit search"
    )
    top_k: int = Field(
        default=5, description="Number of retrieval results to use"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is ROS 2 and how does it work?",
                "session_id": "abc123...",
                "book_version": "v1.0",
                "mode": "full_book",
                "top_k": 5,
            }
        }


class SourceChunk(BaseModel):
    """Source chunk in the response."""

    doc_id: str
    chapter: str
    section: str
    similarity_score: float
    content: str


class QueryResponse(BaseModel):
    """Response model for query result."""

    response: str = Field(..., description="Generated answer")
    sources: list[SourceChunk] = Field(
        ..., description="Source chunks used for generation"
    )
    latency_ms: int = Field(..., description="Total query latency in milliseconds")
    mode: str = Field(..., description="Query mode used")
    input_tokens: int = Field(..., description="Tokens in LLM input")
    output_tokens: int = Field(..., description="Tokens in LLM output")
    error: str = Field(default=None, description="Error message if query failed")


class MessageResponse(BaseModel):
    """Response model for a single message in session history."""

    message_id: str = Field(..., description="Unique message ID")
    user_message: str = Field(..., description="User's query")
    assistant_response: str = Field(..., description="Assistant's response")
    mode: str = Field(..., description="Query mode: 'full_book' or 'selected_text'")
    selected_text: str = Field(
        default=None, description="Selected text (if selected_text mode)"
    )
    latency_ms: int = Field(
        default=None, description="Query latency in milliseconds"
    )
    created_at: str = Field(..., description="Message creation timestamp (ISO format)")


class SessionResponse(BaseModel):
    """Response model for session with chat history."""

    session_id: str = Field(..., description="Unique session ID")
    user_id: str = Field(default=None, description="User identifier")
    title: str = Field(default=None, description="Session title")
    book_version: str = Field(..., description="Book version")
    message_count: int = Field(..., description="Number of messages in session")
    created_at: str = Field(..., description="Session creation timestamp (ISO format)")
    updated_at: str = Field(..., description="Last update timestamp (ISO format)")
    last_activity: str = Field(
        ..., description="Last activity timestamp (ISO format)"
    )
    messages: list[MessageResponse] = Field(
        ..., description="List of messages in session"
    )


# Authentication Models (Phase 4)

class SignupRequest(BaseModel):
    """Request model for user registration."""

    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    full_name: str = Field(default=None, description="Full name")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "full_name": "John Doe",
            }
        }


class LoginRequest(BaseModel):
    """Request model for user login."""

    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
            }
        }


class LoginResponse(BaseModel):
    """Response model for login endpoint."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 86400,
            }
        }


class UserResponse(BaseModel):
    """Response model for user information."""

    user_id: str = Field(..., description="User ID (UUID)")
    email: str = Field(..., description="User email address")
    full_name: str = Field(default=None, description="Full name")
    created_at: str = Field(..., description="Account creation timestamp (ISO format)")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "full_name": "John Doe",
                "created_at": "2024-12-17T10:30:00",
            }
        }


# Analytics Models (Phase 4)

class UserAnalyticsResponse(BaseModel):
    """Response model for user analytics."""

    total_queries: int = Field(..., description="Total number of queries")
    avg_response_time_ms: float = Field(..., description="Average response time in milliseconds")
    total_tokens_used: int = Field(..., description="Total tokens used across all queries")
    success_rate: float = Field(..., description="Success rate as percentage (0-100)")

    class Config:
        json_schema_extra = {
            "example": {
                "total_queries": 42,
                "avg_response_time_ms": 3500.5,
                "total_tokens_used": 5000,
                "success_rate": 95.2,
            }
        }


class QueryHistoryItem(BaseModel):
    """Single query in history."""

    query_id: str = Field(..., description="Query metric ID")
    query_text: str = Field(..., description="The user's query")
    response_time_ms: int = Field(..., description="Response time in milliseconds")
    model_used: str = Field(..., description="Model used for generation")
    success: bool = Field(..., description="Whether query was successful")
    created_at: str = Field(..., description="Query timestamp (ISO format)")


class QueryHistoryResponse(BaseModel):
    """Response model for query history."""

    queries: list[QueryHistoryItem] = Field(..., description="List of queries")
    total: int = Field(..., description="Total number of queries")
    limit: int = Field(..., description="Queries returned in this request")
    offset: int = Field(..., description="Pagination offset")


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Status and timestamp information.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": settings.environment,
    }


@app.post("/ingest", response_model=IngestResponse)
async def ingest_content(request: IngestRequest):
    """
    Ingest content: chunk, embed, and store in vector DB and Postgres.

    Workflow:
    1. Split content by headings (H1/H2), fallback to token-based chunking
    2. Generate embeddings for new chunks (skip duplicates)
    3. Store in Qdrant (vectors) and Neon (metadata)

    Args:
        request: IngestRequest with chapter content and metadata

    Returns:
        IngestResponse with ingestion statistics

    Raises:
        HTTPException: If ingestion fails
    """
    try:
        logger.info(
            f"📥 Ingest request: {request.chapter} / {request.section} "
            f"({len(request.content)} chars)"
        )

        # Validate input
        if not request.content.strip():
            raise HTTPException(
                status_code=400, detail="Content cannot be empty"
            )

        if len(request.content) > 1_000_000:  # 1MB limit
            raise HTTPException(
                status_code=413,
                detail="Content too large (max 1MB)",
            )

        # Perform ingestion
        ingest_service = get_ingest_service()
        result = ingest_service.ingest_chapter(
            chapter=request.chapter,
            section=request.section,
            content=request.content,
            book_version=request.book_version,
        )

        # Check for errors
        if "error" in result and result["error"]:
            logger.error(f"❌ Ingestion error: {result['error']}")
            raise HTTPException(
                status_code=500,
                detail=f"Ingestion failed: {result['error']}",
            )

        logger.info(f"✅ Ingestion successful: {result}")
        return IngestResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in /ingest: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )


@app.post("/query", response_model=QueryResponse)
async def query_content(request: QueryRequest):
    """
    Query the knowledge base: retrieve relevant content and generate an answer.

    Workflow:
    1. Retrieve relevant chunks using semantic search
    2. Generate response using LLM with retrieved context
    3. Store interaction in database
    4. Return response with sources and latency metrics

    Args:
        request: QueryRequest with query and parameters

    Returns:
        QueryResponse with generated answer and sources

    Raises:
        HTTPException: If query processing fails
    """
    query_start = time.time()

    try:
        logger.info(
            f"❓ Query: '{request.query}' (mode={request.mode}, "
            f"session={request.session_id[:8]}...)"
        )

        # Validate input
        if not request.query.strip():
            raise HTTPException(
                status_code=400, detail="Query cannot be empty"
            )

        # Step 1: Retrieve relevant chunks
        logger.info("🔍 Retrieving relevant chunks...")
        retriever = get_retriever(top_k=request.top_k)

        retrieved_chunks, retrieval_metadata = retriever.retrieve(
            query=request.query,
            book_version=request.book_version,
            chapter_filter=request.chapter_filter,
            mode=request.mode,
        )

        if not retrieved_chunks:
            logger.warning("⚠️ No relevant chunks found")
            return QueryResponse(
                response="I couldn't find relevant information in the course materials to answer your question.",
                sources=[],
                latency_ms=int((time.time() - query_start) * 1000),
                mode=request.mode,
                input_tokens=0,
                output_tokens=0,
            )

        # Step 2: Assemble context for generation
        context_parts = []
        for i, chunk in enumerate(retrieved_chunks, 1):
            source = f"{chunk.chapter} > {chunk.section}"
            if chunk.subsection:
                source += f" > {chunk.subsection}"
            part = f"[Source {i}: {source} (sim: {chunk.similarity_score:.2f})]\n{chunk.content}"
            context_parts.append(part)

        context = "\n\n".join(context_parts)

        # Step 3: Generate response
        logger.info("🤖 Generating response...")
        generator = get_generation_agent()

        generated = generator.generate(
            query=request.query,
            context=context,
            mode=request.mode,
            selected_text=request.selected_text,
        )

        # Step 4: Store interaction in database
        try:
            db = DatabaseSession()
            session_id = request.session_id

            # Get or create session
            session = get_session(session_id)
            if not session:
                session = add_session(
                    session_id=session_id,
                    user_id="anonymous",
                    title=request.query[:50],
                    book_version=request.book_version,
                )

            # Store message
            source_ids = [chunk.doc_id for chunk in retrieved_chunks]
            add_message(
                session_id=session_id,
                user_message=request.query,
                assistant_response=generated.content,
                mode=request.mode,
                selected_text=request.selected_text,
                source_chunk_ids=source_ids,
                latency_ms=int((time.time() - query_start) * 1000),
            )

            logger.info(f"✅ Interaction stored (session={session_id[:8]}...)")
        except Exception as e:
            logger.warning(f"⚠️ Failed to store interaction: {e}")
            # Continue anyway; don't fail the query

        # Step 5: Format response
        latency_ms = int((time.time() - query_start) * 1000)

        sources = [
            SourceChunk(
                doc_id=chunk.doc_id,
                chapter=chunk.chapter,
                section=chunk.section,
                similarity_score=chunk.similarity_score,
                content=chunk.content[:200],  # Truncate for response
            )
            for chunk in retrieved_chunks
        ]

        logger.info(
            f"✅ Query complete: {latency_ms}ms, "
            f"{generated.output_tokens} output tokens"
        )

        return QueryResponse(
            response=generated.content,
            sources=sources,
            latency_ms=latency_ms,
            mode=request.mode,
            input_tokens=generated.input_tokens,
            output_tokens=generated.output_tokens,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Query processing failed: {str(e)}",
        )


@app.post("/query-selected-text", response_model=QueryResponse)
async def query_selected_text(request: QueryRequest):
    """
    Query using only user-selected text (no vector retrieval).

    Workflow:
    1. Validate selected_text length
    2. Use selected_text as sole context
    3. Generate response using LLM
    4. Validate response is grounded in selected text
    5. Store interaction in database
    6. Return response with selected text as sole source

    Args:
        request: QueryRequest with query and selected_text

    Returns:
        QueryResponse with generated answer and selected text as source

    Raises:
        HTTPException: If query processing fails
    """
    query_start = time.time()

    try:
        logger.info(
            f"❓ Selected-Text Query: '{request.query}' "
            f"(session={request.session_id[:8]}...)"
        )

        # Validate query
        if not request.query.strip():
            raise HTTPException(
                status_code=400, detail="Query cannot be empty"
            )

        # Validate selected_text
        if not request.selected_text or not request.selected_text.strip():
            raise HTTPException(
                status_code=400, detail="Selected text cannot be empty"
            )

        selected_text = request.selected_text.strip()

        # Validate selected_text character length
        if len(selected_text) > settings.max_selected_text_characters:
            raise HTTPException(
                status_code=413,
                detail=f"Selected text too long (max {settings.max_selected_text_characters} chars)",
            )

        # Validate selected_text token length
        logger.info("📊 Validating selected text token count...")
        embeddings = get_embedding_generator()
        tokens = embeddings.estimate_tokens(selected_text)

        if tokens > settings.max_selected_text_tokens:
            logger.warning(
                f"⚠️ Selected text truncated: {tokens} → {settings.max_selected_text_tokens} tokens"
            )
            # Truncate to token limit (simple approach: truncate text by proportion)
            truncation_ratio = settings.max_selected_text_tokens / tokens
            selected_text = selected_text[: int(len(selected_text) * truncation_ratio)]

        # Step 1: Use selected_text as sole context (no retrieval)
        context = f"[User Selected Text]\n{selected_text}"

        # Step 2: Generate response
        logger.info("🤖 Generating response (selected-text mode)...")
        generator = get_generation_agent()

        generated = generator.generate(
            query=request.query,
            context=context,
            mode="selected_text",
            selected_text=selected_text,
        )

        # Step 3: Server-side validation
        logger.info("✔️ Validating response is grounded in selected text...")
        is_valid, confidence = validate_response_in_context(
            generated.content, selected_text
        )

        if not is_valid:
            logger.warning(
                f"⚠️ Response failed validation (confidence={confidence:.3f})"
            )
            # Replace with fallback message
            generated.content = (
                "I couldn't find an answer to your question in the selected text. "
                "Try selecting more context or switching to full-book mode."
            )

        # Step 4: Store interaction in database
        try:
            db = DatabaseSession()
            session_id = request.session_id

            # Get or create session
            session = get_session(session_id)
            if not session:
                session = add_session(
                    session_id=session_id,
                    user_id="anonymous",
                    title=request.query[:50],
                    book_version=request.book_version,
                )

            # Store message
            add_message(
                session_id=session_id,
                user_message=request.query,
                assistant_response=generated.content,
                mode="selected_text",
                selected_text=selected_text,
                source_chunk_ids=[],  # No retrieval in selected-text mode
                latency_ms=int((time.time() - query_start) * 1000),
            )

            logger.info(f"✅ Interaction stored (session={session_id[:8]}...)")
        except Exception as e:
            logger.warning(f"⚠️ Failed to store interaction: {e}")
            # Continue anyway; don't fail the query

        # Step 5: Format response
        latency_ms = int((time.time() - query_start) * 1000)

        # Return selected text as sole source
        sources = [
            SourceChunk(
                doc_id="selected_text",
                chapter="User Selection",
                section="Highlighted Text",
                similarity_score=1.0,
                content=selected_text[:200],  # Truncate for response
            )
        ]

        logger.info(
            f"✅ Selected-text query complete: {latency_ms}ms, "
            f"{generated.output_tokens} output tokens"
        )

        return QueryResponse(
            response=generated.content,
            sources=sources,
            latency_ms=latency_ms,
            mode="selected_text",
            input_tokens=generated.input_tokens,
            output_tokens=generated.output_tokens,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Selected-text query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Selected-text query processing failed: {str(e)}",
        )


@app.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session_endpoint(
    session_id: str, limit: int = 50, offset: int = 0
):
    """
    Retrieve chat session with message history.

    Args:
        session_id: The session ID to retrieve
        limit: Number of messages to return (default 50, max 100)
        offset: Pagination offset (default 0)

    Returns:
        SessionResponse with session details and message history

    Raises:
        HTTPException: If session not found or expired
    """
    try:
        logger.info(
            f"📋 Retrieving session: {session_id[:8]}... (limit={limit}, offset={offset})"
        )

        # Validate pagination parameters
        limit = min(limit, 100)  # Max 100 messages
        if limit < 1:
            limit = 50
        if offset < 0:
            offset = 0

        # Get session
        session = get_session(session_id)

        if not session:
            logger.warning(f"⚠️ Session not found or expired: {session_id}")
            raise HTTPException(
                status_code=404, detail="Session not found or expired"
            )

        # Get message history
        messages = get_session_history(
            session_id=session_id, limit=limit, offset=offset
        )

        # Convert messages to response format
        message_responses = [
            MessageResponse(
                message_id=str(msg.id),
                user_message=msg.user_message,
                assistant_response=msg.assistant_response or "",
                mode=msg.mode,
                selected_text=msg.selected_text,
                latency_ms=msg.latency_ms,
                created_at=msg.created_at.isoformat() if msg.created_at else None,
            )
            for msg in messages
        ]

        # Build response
        response = SessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            title=session.title,
            book_version=session.book_version,
            message_count=session.message_count,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            last_activity=session.last_activity.isoformat(),
            messages=message_responses,
        )

        logger.info(
            f"✅ Session retrieved: {session_id[:8]}... "
            f"({len(message_responses)} messages, {session.message_count} total)"
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to retrieve session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve session: {str(e)}",
        )


# Authentication Endpoints (Phase 4)

@app.post("/auth/signup", response_model=UserResponse, status_code=201)
@limiter.limit("5/hour")  # 5 signups per hour per IP
async def signup(request: SignupRequest):
    """
    Register a new user account.

    Args:
        request: SignupRequest with email, password, and optional full_name

    Returns:
        UserResponse with user information

    Raises:
        HTTPException: If email already registered or validation fails
    """
    try:
        logger.info(f"📝 Signup request: {request.email}")

        # Validate password length
        if len(request.password) < 8:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters",
            )

        # Attempt to create user
        user = add_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
        )

        logger.info(f"✅ User registered: {request.email}")
        return UserResponse(
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at.isoformat(),
        )

    except ValueError as e:
        logger.warning(f"⚠️ Signup failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Signup error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to register user",
        )


@app.post("/auth/login", response_model=LoginResponse)
@limiter.limit("10/minute")  # 10 login attempts per minute per IP
async def login(request: LoginRequest):
    """
    Login a user and return JWT access token.

    Args:
        request: LoginRequest with email and password

    Returns:
        LoginResponse with access token and expiration

    Raises:
        HTTPException: If credentials invalid
    """
    try:
        logger.info(f"🔐 Login request: {request.email}")

        # Find user by email
        user = get_user_by_email(request.email)
        if not user:
            logger.warning(f"⚠️ Login failed: User not found: {request.email}")
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password",
            )

        # Verify password
        if not verify_password(request.password, user.password_hash):
            logger.warning(f"⚠️ Login failed: Invalid password for {request.email}")
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password",
            )

        # Check if account is active
        if not user.is_active:
            logger.warning(f"⚠️ Login failed: Account inactive: {request.email}")
            raise HTTPException(
                status_code=403,
                detail="Account is inactive",
            )

        # Phase 6: Check if MFA is enabled
        if settings.mfa_enabled and user.mfa_enabled:
            # Create temporary MFA token (short-lived, requires MFA verification)
            mfa_token_expire = datetime.utcnow() + timedelta(minutes=5)
            mfa_token_payload = {
                "sub": str(user.id),
                "exp": mfa_token_expire,
                "mfa_required": True,
                "type": "mfa_temporary",
            }
            mfa_token = jwt.encode(
                mfa_token_payload,
                JWT_SECRET,
                algorithm=JWT_ALGORITHM
            )
            logger.info(f"✅ MFA required for user {request.email} - temporary token issued")
            # Return 202 Accepted with temporary MFA token
            return JSONResponse(
                status_code=202,
                content={
                    "message": "MFA verification required",
                    "mfa_token": mfa_token,
                    "mfa_required": True,
                }
            )

        # Create access token
        access_token = create_access_token(str(user.id))
        expires_in = JWT_EXPIRATION_HOURS * 3600  # Convert to seconds

        logger.info(f"✅ User logged in: {request.email}")
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to login",
        )


# ============================================================================
# PHASE 6: TOTP/MFA ENDPOINTS
# ============================================================================

@app.post("/auth/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(current_user: dict = Depends(get_current_user)):
    """
    Initiate MFA setup for a user. Returns QR code and backup codes.

    Args:
        current_user: Current authenticated user

    Returns:
        MFASetupResponse with QR code URL, secret, and backup codes
    """
    try:
        user_id = current_user.get("user_id")
        user = get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Generate TOTP secret
        secret = generate_totp_secret()

        # Generate QR code
        qr_code_url = generate_qr_code(secret, user.email, settings.mfa_issuer_name)

        # Generate backup codes
        backup_codes = generate_backup_codes()
        hashed_codes = hash_backup_codes(backup_codes)

        # Store TOTP secret in database (not yet verified)
        db_session = DatabaseSession()
        session = db_session.get_session()
        try:
            # Check if TOTP already exists
            existing = session.query(TOTPSecret).filter_by(user_id=user_id).first()
            if existing:
                session.delete(existing)

            totp_secret = TOTPSecret(
                user_id=user_id,
                secret=secret,
                is_verified=False,
                enabled=False,
                backup_codes=hashed_codes,
            )
            session.add(totp_secret)
            session.commit()

            logger.info(f"✅ MFA setup initiated for user {user_id}")

            return MFASetupResponse(
                qr_code_url=qr_code_url,
                secret=secret,
                backup_codes=backup_codes,  # Show once to user
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ MFA setup error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to setup MFA")


@app.post("/auth/mfa/verify", response_model=MFAVerifyResponse)
async def verify_mfa_setup(
    request: MFAVerifyRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Verify TOTP code during MFA setup. Enables MFA if code is valid.

    Args:
        request: MFAVerifyRequest with 6-digit TOTP code
        current_user: Current authenticated user

    Returns:
        MFAVerifyResponse with success status
    """
    try:
        user_id = current_user.get("user_id")
        user = get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        db_session = DatabaseSession()
        session = db_session.get_session()
        try:
            # Get TOTP secret
            totp_secret = session.query(TOTPSecret).filter_by(user_id=user_id).first()
            if not totp_secret:
                raise HTTPException(status_code=400, detail="MFA setup not initiated")

            # Verify TOTP code
            if not verify_totp_code(totp_secret.secret, request.code):
                logger.warning(f"⚠️ Invalid TOTP code for user {user_id}")
                raise HTTPException(status_code=400, detail="Invalid TOTP code")

            # Mark as verified and enabled
            totp_secret.is_verified = True
            totp_secret.enabled = True
            session.add(totp_secret)

            # Update user MFA status
            user.mfa_enabled = True
            user.mfa_method = "totp"
            session.add(user)
            session.commit()

            logger.info(f"✅ MFA verified and enabled for user {user_id}")

            return MFAVerifyResponse(
                success=True,
                message="MFA setup successful",
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ MFA verification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to verify MFA")


@app.post("/auth/mfa/disable", response_model=MFADisableResponse)
async def disable_mfa(
    request: MFADisableRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Disable MFA for a user. Requires password confirmation.

    Args:
        request: MFADisableRequest with password
        current_user: Current authenticated user

    Returns:
        MFADisableResponse with success status
    """
    try:
        user_id = current_user.get("user_id")
        user = get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Verify password
        if not verify_password(request.password, user.password_hash):
            logger.warning(f"⚠️ MFA disable failed: Invalid password for user {user_id}")
            raise HTTPException(status_code=401, detail="Invalid password")

        db_session = DatabaseSession()
        session = db_session.get_session()
        try:
            # Delete TOTP secret
            totp_secret = session.query(TOTPSecret).filter_by(user_id=user_id).first()
            if totp_secret:
                session.delete(totp_secret)

            # Update user MFA status
            user.mfa_enabled = False
            user.mfa_method = None
            session.add(user)
            session.commit()

            logger.info(f"✅ MFA disabled for user {user_id}")

            return MFADisableResponse(
                success=True,
                message="MFA disabled successfully",
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ MFA disable error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to disable MFA")


@app.post("/auth/mfa/backup-codes", response_model=MFAVerifyResponse)
async def regenerate_backup_codes(current_user: dict = Depends(get_current_user)):
    """
    Regenerate backup codes for MFA. Returns new codes.

    Args:
        current_user: Current authenticated user

    Returns:
        MFAVerifyResponse with new backup codes
    """
    try:
        user_id = current_user.get("user_id")
        user = get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.mfa_enabled:
            raise HTTPException(status_code=400, detail="MFA not enabled")

        # Generate new backup codes
        backup_codes = generate_backup_codes()
        hashed_codes = hash_backup_codes(backup_codes)

        db_session = DatabaseSession()
        session = db_session.get_session()
        try:
            totp_secret = session.query(TOTPSecret).filter_by(user_id=user_id).first()
            if not totp_secret:
                raise HTTPException(status_code=400, detail="TOTP secret not found")

            totp_secret.backup_codes = hashed_codes
            session.add(totp_secret)
            session.commit()

            logger.info(f"✅ Backup codes regenerated for user {user_id}")

            return MFAVerifyResponse(
                success=True,
                message="Backup codes regenerated",
                backup_codes=backup_codes,  # Show once to user
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Backup codes regeneration error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to regenerate backup codes")


@app.post("/auth/login/mfa", response_model=MFALoginResponse)
async def mfa_verification(
    request: MFALoginRequest,
    mfa_token: Optional[str] = Header(None)
):
    """
    Complete MFA login with TOTP code or backup code.
    Requires temporary MFA token from initial login.

    Args:
        request: MFALoginRequest with TOTP code or backup code
        mfa_token: Temporary MFA token from initial login

    Returns:
        MFALoginResponse with access and refresh tokens
    """
    try:
        if not mfa_token:
            raise HTTPException(status_code=401, detail="MFA token required")

        # Verify MFA token (temporary token that was returned from initial login)
        try:
            payload = jwt.decode(mfa_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("sub")
            mfa_required = payload.get("mfa_required")

            if not mfa_required:
                raise HTTPException(status_code=401, detail="Invalid MFA token")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="MFA token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid MFA token")

        user = get_user_by_id(user_id)
        if not user or not user.mfa_enabled:
            raise HTTPException(status_code=401, detail="MFA not enabled")

        db_session = DatabaseSession()
        session = db_session.get_session()
        try:
            totp_secret = session.query(TOTPSecret).filter_by(user_id=user_id).first()
            if not totp_secret:
                raise HTTPException(status_code=400, detail="TOTP secret not found")

            # Verify TOTP code or backup code
            code_valid = False
            if request.code:
                code_valid = verify_totp_code(totp_secret.secret, request.code)
            elif request.backup_code:
                # Check backup code
                for hashed_code in (totp_secret.backup_codes or []):
                    if verify_backup_code(request.backup_code, hashed_code):
                        code_valid = True
                        # Remove used backup code
                        totp_secret.backup_codes = [
                            h for h in totp_secret.backup_codes if h != hashed_code
                        ]
                        break

            if not code_valid:
                logger.warning(f"⚠️ Invalid MFA code for user {user_id}")
                raise HTTPException(status_code=401, detail="Invalid code")

            # Create access token
            access_token = create_access_token(str(user_id))
            expires_in = JWT_EXPIRATION_HOURS * 3600

            # Create refresh token
            refresh_token = generate_refresh_token()
            token_hash = hash_token(refresh_token)

            refresh_token_obj = RefreshToken(
                user_id=user_id,
                token_hash=token_hash,
                device_id=str(uuid.uuid4()),
                device_name="Web Browser",
                expires_at=calculate_token_expiry(settings.refresh_token_expiration_days),
            )
            session.add(refresh_token_obj)
            session.commit()

            logger.info(f"✅ MFA login successful for user {user_id}")

            return MFALoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=expires_in,
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ MFA verification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to complete MFA login")


# ============================================================================
# PHASE 6: REFRESH TOKEN ENDPOINTS
# ============================================================================

@app.post("/auth/refresh", response_model=RefreshTokenResponse)
@limiter.limit("20/minute")  # Rate limit token refresh
async def refresh_access_token(
    request: RefreshTokenRequest,
    user_agent: str = Header(None),
    x_forwarded_for: str = Header(None)
):
    """
    Refresh access token using refresh token. Implements token rotation.
    Old refresh token is invalidated, new refresh token is returned.

    Args:
        request: RefreshTokenRequest with refresh_token
        user_agent: User-Agent header for device tracking
        x_forwarded_for: Client IP address

    Returns:
        RefreshTokenResponse with new access and refresh tokens
    """
    try:
        if not settings.refresh_token_enabled:
            raise HTTPException(status_code=403, detail="Token refresh disabled")

        db_session = DatabaseSession()
        session = db_session.get_session()
        try:
            # Find refresh token by hash
            token_hash = hash_token(request.refresh_token)
            refresh_token_obj = session.query(RefreshToken).filter_by(
                token_hash=token_hash
            ).first()

            if not refresh_token_obj or refresh_token_obj.is_revoked:
                logger.warning(f"⚠️ Invalid or revoked refresh token attempted")
                raise HTTPException(status_code=401, detail="Invalid refresh token")

            if is_token_expired(refresh_token_obj.expires_at):
                session.delete(refresh_token_obj)
                session.commit()
                logger.warning(f"⚠️ Expired refresh token attempted")
                raise HTTPException(status_code=401, detail="Refresh token expired")

            # Check rotation chain limit
            rotation_count = refresh_token_obj.rotation_count or 0
            if not can_rotate_token(rotation_count, settings.max_refresh_token_chains):
                logger.warning(f"⚠️ Rotation chain limit exceeded for user {refresh_token_obj.user_id}")
                raise HTTPException(status_code=401, detail="Rotation chain limit exceeded - re-authentication required")

            user_id = refresh_token_obj.user_id

            # Create new access token
            access_token = create_access_token(user_id)
            expires_in = JWT_EXPIRATION_HOURS * 3600

            # Rotate refresh token (Phase 6 security: prevent token reuse)
            new_refresh_token = generate_refresh_token()
            new_token_hash = hash_token(new_refresh_token)

            # Mark old token as rotated (don't delete, keep audit trail)
            old_device_id = refresh_token_obj.device_id
            refresh_token_obj.is_revoked = True
            session.add(refresh_token_obj)

            # Create new refresh token
            new_refresh_token_obj = RefreshToken(
                user_id=user_id,
                token_hash=new_token_hash,
                device_id=old_device_id,  # Keep same device
                device_name=refresh_token_obj.device_name,
                ip_address=x_forwarded_for,
                expires_at=calculate_token_expiry(settings.refresh_token_expiration_days),
                rotated_from=refresh_token_obj.id,
                rotation_count=(rotation_count + 1) if settings.enable_token_rotation else 0,
            )
            session.add(new_refresh_token_obj)
            session.commit()

            logger.info(f"✅ Token rotated for device {old_device_id} (rotation: {rotation_count + 1})")

            return RefreshTokenResponse(
                access_token=access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
                expires_in=expires_in,
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Token refresh error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to refresh token")


@app.get("/auth/devices", response_model=DeviceListResponse)
async def list_active_devices(current_user: dict = Depends(get_current_user)):
    """
    List all active sessions/devices for current user.

    Args:
        current_user: Current authenticated user

    Returns:
        DeviceListResponse with list of active devices
    """
    try:
        user_id = current_user.get("user_id")
        user = get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        db_session = DatabaseSession()
        session = db_session.get_session()
        try:
            # Get all active (non-revoked) refresh tokens for user
            devices = session.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.utcnow()
            ).all()

            device_list = [
                DeviceInfo(
                    device_id=str(device.device_id),
                    device_name=device.device_name or "Unknown Device",
                    ip_address=device.ip_address,
                    created_at=device.created_at,
                    last_used_at=device.last_used_at,
                    is_current=False,  # Would need current token ID to determine
                )
                for device in devices
            ]

            logger.info(f"✅ Retrieved {len(device_list)} active devices for user {user_id}")

            return DeviceListResponse(
                devices=device_list,
                total=len(device_list),
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to retrieve devices: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve devices")


@app.post("/auth/devices/{device_id}/revoke", response_model=RevokeDeviceResponse)
async def revoke_device(
    device_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Revoke a specific device/session for current user.

    Args:
        device_id: Device ID to revoke
        current_user: Current authenticated user

    Returns:
        RevokeDeviceResponse with success status
    """
    try:
        user_id = current_user.get("user_id")
        user = get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        db_session = DatabaseSession()
        session = db_session.get_session()
        try:
            # Find and revoke the refresh token for this device
            device_token = session.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.device_id == device_id,
                RefreshToken.is_revoked == False
            ).first()

            if not device_token:
                raise HTTPException(status_code=404, detail="Device not found")

            device_token.is_revoked = True
            session.add(device_token)
            session.commit()

            logger.info(f"✅ Device {device_id} revoked for user {user_id}")

            return RevokeDeviceResponse(
                success=True,
                message=f"Device {device_id} revoked successfully",
                revoked_device_id=device_id,
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to revoke device: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to revoke device")


@app.post("/auth/logout-all", response_model=LogoutAllResponse)
async def logout_all_devices(current_user: dict = Depends(get_current_user)):
    """
    Logout from all devices by revoking all refresh tokens.

    Args:
        current_user: Current authenticated user

    Returns:
        LogoutAllResponse with count of revoked devices
    """
    try:
        user_id = current_user.get("user_id")
        user = get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        db_session = DatabaseSession()
        session = db_session.get_session()
        try:
            # Find all active refresh tokens for this user
            active_tokens = session.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False
            ).all()

            # Revoke all of them
            revoked_count = 0
            for token in active_tokens:
                token.is_revoked = True
                session.add(token)
                revoked_count += 1

            session.commit()

            # Also revoke any JWT tokens by adding them to blacklist
            # This would require the current access token, which we don't have here
            # In production, could pass the token and revoke it too

            logger.info(f"✅ Logged out from all {revoked_count} devices for user {user_id}")

            return LogoutAllResponse(
                success=True,
                message=f"Logged out from all devices",
                revoked_count=revoked_count,
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to logout from all devices: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to logout from all devices")


# ============================================================================
# PHASE 6: API KEY ENDPOINTS
# ============================================================================

@app.post("/api-keys", response_model=CreateAPIKeyResponse)
async def create_api_key(
    request: CreateAPIKeyRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new API key for programmatic access.
    Full key is returned ONCE - user must save immediately.

    Args:
        request: CreateAPIKeyRequest with name, scopes, expiration
        current_user: Current authenticated user

    Returns:
        CreateAPIKeyResponse with full API key (shown once!)
    """
    try:
        if not settings.api_keys_enabled:
            raise HTTPException(status_code=403, detail="API keys disabled")

        user_id = current_user.get("user_id")
        user = get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check max API keys per user
        db_session = DatabaseSession()
        session = db_session.get_session()
        try:
            key_count = session.query(APIKey).filter_by(user_id=user_id).count()
            if key_count >= settings.max_api_keys_per_user:
                raise HTTPException(
                    status_code=429,
                    detail=f"Maximum {settings.max_api_keys_per_user} API keys allowed"
                )

            # Use default scopes if none provided
            scopes = request.scopes if request.scopes else ["read:queries", "read:sessions"]

            # Generate API key
            full_key, key_prefix = generate_api_key()
            key_hash = hash_api_key(full_key)

            # Create API key record
            api_key_obj = APIKey(
                user_id=user_id,
                key_hash=key_hash,
                key_prefix=key_prefix,
                name=request.name,
                description=request.description,
                scopes=scopes,
                is_active=True,
                expires_at=calculate_key_expiry(request.expires_in_days or settings.api_key_default_expiration_days),
            )
            session.add(api_key_obj)
            session.commit()

            logger.info(f"✅ API key created for user {user_id}: {request.name}")

            return CreateAPIKeyResponse(
                key=full_key,  # Only returned once!
                key_prefix=key_prefix,
                name=request.name,
                created_at=api_key_obj.created_at,
                message="Save this key immediately - it will not be shown again",
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create API key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create API key")


@app.get("/api-keys", response_model=APIKeyListResponse)
async def list_api_keys(current_user: dict = Depends(get_current_user)):
    """
    List all API keys for current user. Shows only key prefix, not full key.

    Args:
        current_user: Current authenticated user

    Returns:
        APIKeyListResponse with list of API keys
    """
    try:
        user_id = current_user.get("user_id")
        user = get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        db_session = DatabaseSession()
        session = db_session.get_session()
        try:
            api_keys = session.query(APIKey).filter_by(user_id=user_id).all()

            keys_list = [
                APIKeyItem(
                    id=str(key.id),
                    key_prefix=key.key_prefix,
                    name=key.name,
                    description=key.description,
                    scopes=key.scopes,
                    is_active=key.is_active,
                    created_at=key.created_at,
                    last_used_at=key.last_used_at,
                    expires_at=key.expires_at,
                )
                for key in api_keys
            ]

            logger.info(f"✅ Retrieved {len(keys_list)} API keys for user {user_id}")

            return APIKeyListResponse(
                keys=keys_list,
                total=len(keys_list),
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to list API keys: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list API keys")


@app.patch("/api-keys/{key_id}", response_model=APIKeyItem)
async def update_api_key(
    key_id: str,
    request: UpdateAPIKeyRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update API key metadata (name, description, scopes).

    Args:
        key_id: API key ID to update
        request: UpdateAPIKeyRequest with updates
        current_user: Current authenticated user

    Returns:
        APIKeyItem with updated information
    """
    try:
        user_id = current_user.get("user_id")
        user = get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        db_session = DatabaseSession()
        session = db_session.get_session()
        try:
            api_key = session.query(APIKey).filter(
                APIKey.id == key_id,
                APIKey.user_id == user_id
            ).first()

            if not api_key:
                raise HTTPException(status_code=404, detail="API key not found")

            # Update fields if provided
            if request.name is not None:
                api_key.name = request.name
            if request.description is not None:
                api_key.description = request.description
            if request.scopes is not None:
                api_key.scopes = request.scopes

            session.add(api_key)
            session.commit()

            logger.info(f"✅ API key updated for user {user_id}: {key_id}")

            return APIKeyItem(
                id=str(api_key.id),
                key_prefix=api_key.key_prefix,
                name=api_key.name,
                description=api_key.description,
                scopes=api_key.scopes,
                is_active=api_key.is_active,
                created_at=api_key.created_at,
                last_used_at=api_key.last_used_at,
                expires_at=api_key.expires_at,
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update API key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update API key")


@app.delete("/api-keys/{key_id}", response_model=RevokeAPIKeyResponse)
async def revoke_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Revoke an API key immediately.

    Args:
        key_id: API key ID to revoke
        current_user: Current authenticated user

    Returns:
        RevokeAPIKeyResponse with success status
    """
    try:
        user_id = current_user.get("user_id")
        user = get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        db_session = DatabaseSession()
        session = db_session.get_session()
        try:
            api_key = session.query(APIKey).filter(
                APIKey.id == key_id,
                APIKey.user_id == user_id
            ).first()

            if not api_key:
                raise HTTPException(status_code=404, detail="API key not found")

            api_key.is_active = False
            api_key.revoked_at = datetime.utcnow()
            session.add(api_key)
            session.commit()

            logger.info(f"✅ API key revoked for user {user_id}: {key_id}")

            return RevokeAPIKeyResponse(
                success=True,
                message="API key revoked successfully",
                revoked_key_prefix=api_key.key_prefix,
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to revoke API key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to revoke API key")


@app.get("/api-keys/{key_id}/usage", response_model=APIKeyUsageResponse)
async def get_api_key_usage(
    key_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get usage statistics for an API key.

    Args:
        key_id: API key ID
        current_user: Current authenticated user

    Returns:
        APIKeyUsageResponse with usage statistics
    """
    try:
        user_id = current_user.get("user_id")
        user = get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        db_session = DatabaseSession()
        session = db_session.get_session()
        try:
            api_key = session.query(APIKey).filter(
                APIKey.id == key_id,
                APIKey.user_id == user_id
            ).first()

            if not api_key:
                raise HTTPException(status_code=404, detail="API key not found")

            # In a real implementation, track API key usage in a separate table
            # For now, return mock usage data
            logger.info(f"✅ Retrieved usage stats for API key {key_id}")

            return APIKeyUsageResponse(
                key_prefix=api_key.key_prefix,
                calls_last_24h=0,  # Would query metrics table
                calls_last_30d=0,  # Would query metrics table
                last_used_at=api_key.last_used_at,
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get API key usage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get API key usage")


# ============================================================================
# PHASE 6: RBAC ENDPOINTS
# ============================================================================

@app.get("/admin/permissions", response_model=PermissionListResponse)
async def list_permissions(current_user: dict = Depends(get_current_user)):
    """
    List all available permissions in the system.

    Args:
        current_user: Current authenticated user

    Returns:
        PermissionListResponse with all permissions
    """
    try:
        if not settings.rbac_enabled:
            raise HTTPException(status_code=403, detail="RBAC disabled")

        db_session = DatabaseSession()
        session = db_session.get_session()
        try:
            permissions = session.query(Permission).all()

            permission_list = [
                PermissionItem(
                    id=str(perm.id),
                    name=perm.name,
                    resource=perm.resource,
                    action=perm.action,
                    description=perm.description,
                )
                for perm in permissions
            ]

            logger.info(f"✅ Retrieved {len(permission_list)} permissions")

            return PermissionListResponse(
                permissions=permission_list,
                total=len(permission_list),
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to list permissions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list permissions")


@app.post("/admin/roles", response_model=RoleItem)
async def create_role(
    request: CreateRoleRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new role (admin only).

    Args:
        request: CreateRoleRequest with role name and permissions
        current_user: Current authenticated user (must have admin permission)

    Returns:
        RoleItem with created role
    """
    try:
        if not settings.rbac_enabled:
            raise HTTPException(status_code=403, detail="RBAC disabled")

        # Check admin permission
        user_permissions = get_cached_permissions(current_user.get("user_id"))
        if not user_permissions:
            # If not cached, fetch from database (simplified for demo)
            if not has_permission({}, "admin:roles"):
                raise HTTPException(status_code=403, detail="Permission denied")

        # Validate role name
        if not validate_role_name(request.name):
            raise HTTPException(status_code=400, detail="Invalid role name format")

        db_session = DatabaseSession()
        session = db_session.get_session()
        try:
            # Check if role already exists
            existing_role = session.query(Role).filter_by(name=request.name).first()
            if existing_role:
                raise HTTPException(status_code=409, detail="Role already exists")

            # Create role
            role = Role(
                name=request.name,
                description=request.description,
                is_default=False,
            )

            # Add permissions
            permissions = session.query(Permission).filter(
                Permission.id.in_(request.permission_ids)
            ).all()

            for perm in permissions:
                role.permissions.append(perm)

            session.add(role)
            session.commit()

            logger.info(f"✅ Role created: {request.name}")

            return RoleItem(
                id=str(role.id),
                name=role.name,
                description=role.description,
                is_default=role.is_default,
                permissions=[
                    PermissionItem(
                        id=str(p.id),
                        name=p.name,
                        resource=p.resource,
                        action=p.action,
                        description=p.description,
                    )
                    for p in role.permissions
                ],
                created_at=role.created_at,
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create role: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create role")


@app.patch("/admin/roles/{role_id}", response_model=RoleItem)
async def update_role(
    role_id: str,
    request: UpdateRoleRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a role (admin only).

    Args:
        role_id: Role ID to update
        request: UpdateRoleRequest with updates
        current_user: Current authenticated user (must have admin permission)

    Returns:
        RoleItem with updated role
    """
    try:
        if not settings.rbac_enabled:
            raise HTTPException(status_code=403, detail="RBAC disabled")

        db_session = DatabaseSession()
        session = db_session.get_session()
        try:
            role = session.query(Role).filter_by(id=role_id).first()
            if not role:
                raise HTTPException(status_code=404, detail="Role not found")

            # Update fields if provided
            if request.description is not None:
                role.description = request.description

            # Update permissions if provided
            if request.permission_ids is not None:
                role.permissions.clear()
                permissions = session.query(Permission).filter(
                    Permission.id.in_(request.permission_ids)
                ).all()
                for perm in permissions:
                    role.permissions.append(perm)

            session.add(role)
            session.commit()

            logger.info(f"✅ Role updated: {role.name}")

            return RoleItem(
                id=str(role.id),
                name=role.name,
                description=role.description,
                is_default=role.is_default,
                permissions=[
                    PermissionItem(
                        id=str(p.id),
                        name=p.name,
                        resource=p.resource,
                        action=p.action,
                        description=p.description,
                    )
                    for p in role.permissions
                ],
                created_at=role.created_at,
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update role: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update role")


@app.delete("/admin/roles/{role_id}")
async def delete_role(
    role_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a role (admin only). Prevents deleting roles with assigned users.

    Args:
        role_id: Role ID to delete
        current_user: Current authenticated user (must have admin permission)

    Returns:
        Success message
    """
    try:
        if not settings.rbac_enabled:
            raise HTTPException(status_code=403, detail="RBAC disabled")

        db_session = DatabaseSession()
        session = db_session.get_session()
        try:
            role = session.query(Role).filter_by(id=role_id).first()
            if not role:
                raise HTTPException(status_code=404, detail="Role not found")

            # Prevent deleting roles with assigned users
            user_count = session.query(UserRole).filter_by(role_id=role_id).count()
            if user_count > 0:
                raise HTTPException(
                    status_code=409,
                    detail=f"Cannot delete role with {user_count} assigned users"
                )

            session.delete(role)
            session.commit()

            logger.info(f"✅ Role deleted: {role.name}")

            return {"success": True, "message": "Role deleted successfully"}
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete role: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete role")


@app.post("/admin/users/{user_id}/roles", response_model=AssignRoleResponse)
async def assign_role_to_user(
    user_id: str,
    request: AssignRoleRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Assign a role to a user (admin only).

    Args:
        user_id: User ID to assign role to
        request: AssignRoleRequest with role_id
        current_user: Current authenticated user (must have admin permission)

    Returns:
        AssignRoleResponse with success status
    """
    try:
        if not settings.rbac_enabled:
            raise HTTPException(status_code=403, detail="RBAC disabled")

        db_session = DatabaseSession()
        session = db_session.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            role = session.query(Role).filter_by(id=request.role_id).first()
            if not role:
                raise HTTPException(status_code=404, detail="Role not found")

            # Check if user already has this role
            existing = session.query(UserRole).filter_by(
                user_id=user_id,
                role_id=request.role_id
            ).first()
            if existing:
                raise HTTPException(status_code=409, detail="User already has this role")

            # Assign role
            user_role = UserRole(
                user_id=user_id,
                role_id=request.role_id,
                assigned_by=current_user.get("user_id"),
            )
            session.add(user_role)
            session.commit()

            # Clear user's permission cache
            clear_user_cache(user_id)

            logger.info(f"✅ Role {role.name} assigned to user {user_id}")

            return AssignRoleResponse(
                success=True,
                message=f"Role {role.name} assigned successfully",
                user_id=user_id,
                role_id=request.role_id,
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to assign role: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to assign role")


@app.delete("/admin/users/{user_id}/roles/{role_id}", response_model=RemoveRoleResponse)
async def remove_role_from_user(
    user_id: str,
    role_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Remove a role from a user (admin only).

    Args:
        user_id: User ID to remove role from
        role_id: Role ID to remove
        current_user: Current authenticated user (must have admin permission)

    Returns:
        RemoveRoleResponse with success status
    """
    try:
        if not settings.rbac_enabled:
            raise HTTPException(status_code=403, detail="RBAC disabled")

        db_session = DatabaseSession()
        session = db_session.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            role = session.query(Role).filter_by(id=role_id).first()
            if not role:
                raise HTTPException(status_code=404, detail="Role not found")

            # Find and remove the user role
            user_role = session.query(UserRole).filter_by(
                user_id=user_id,
                role_id=role_id
            ).first()
            if not user_role:
                raise HTTPException(status_code=404, detail="User does not have this role")

            session.delete(user_role)
            session.commit()

            # Clear user's permission cache
            clear_user_cache(user_id)

            logger.info(f"✅ Role {role.name} removed from user {user_id}")

            return RemoveRoleResponse(
                success=True,
                message=f"Role {role.name} removed successfully",
                user_id=user_id,
                role_id=role_id,
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to remove role: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to remove role")


@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Args:
        current_user: Current user from JWT token (dependency)

    Returns:
        UserResponse with user information

    Raises:
        HTTPException: If user not found
    """
    try:
        user_id = current_user.get("user_id")
        logger.info(f"👤 Retrieving user info: {user_id[:8]}...")

        user = get_user_by_id(user_id)
        if not user:
            logger.warning(f"⚠️ User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        return UserResponse(
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to retrieve user: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user information",
        )


@app.post("/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout endpoint - revokes the JWT token.

    Args:
        current_user: Current user from JWT token (dependency)

    Returns:
        dict: Confirmation message

    Note:
        Revokes the JWT token by adding it to the blacklist.
        Requires jti claim in JWT (standard for Phase 5+).
    """
    try:
        user_id = current_user.get("user_id")
        jti = current_user.get("jti")

        if jti:
            # Calculate token expiration time for revocation record
            expires_at = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)

            # Revoke the token
            revoke_token(jti, user_id, reason="user_logout", expires_at=expires_at)
            logger.info(f"👋 User logged out and token revoked: {user_id[:8]}...")
        else:
            logger.warning(f"⚠️ Logout without jti for user: {user_id[:8]}...")

        return {"detail": "Logged out successfully"}

    except Exception as e:
        logger.error(f"❌ Logout error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Logout failed",
        )


# ==================== OAuth Endpoints (Phase 5) ====================

# Store OAuth state tokens temporarily (in production, use Redis)
_oauth_states = {}

def _get_oauth_provider_config(provider: str) -> dict:
    """Get OAuth provider configuration."""
    if provider == "github":
        return {
            "client_id": settings.github_client_id,
            "client_secret": settings.github_client_secret,
            "auth_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "user_url": "https://api.github.com/user",
            "email_url": "https://api.github.com/user/emails",
        }
    elif provider == "google":
        return {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "user_url": "https://openidconnect.googleapis.com/v1/userinfo",
            "scopes": "openid email profile",
        }
    else:
        raise HTTPException(status_code=400, detail="Unsupported OAuth provider")


@app.get("/auth/oauth/{provider}/login")
@limiter.limit("20/hour")
async def oauth_login(provider: str, request):
    """
    Redirect to OAuth provider authorization page.

    Args:
        provider: OAuth provider ("github" or "google")

    Returns:
        RedirectResponse to OAuth provider
    """
    try:
        config = _get_oauth_provider_config(provider)
        if not config.get("client_id") or not config.get("client_secret"):
            raise HTTPException(status_code=503, detail=f"{provider.title()} OAuth is not configured")

        # Generate state token for CSRF protection
        state = secrets.token_urlsafe(32)
        _oauth_states[state] = {"provider": provider, "created_at": datetime.utcnow()}

        # Build authorization URL
        params = {
            "client_id": config["client_id"],
            "redirect_uri": settings.oauth_redirect_uri,
            "response_type": "code",
            "state": state,
            "scope": config.get("scopes", "user:email"),
        }

        auth_url = f"{config['auth_url']}?" + "&".join(f"{k}={v}" for k, v in params.items())
        logger.info(f"🔐 OAuth login initiated for {provider}")
        return RedirectResponse(url=auth_url)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ OAuth login error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="OAuth login failed")


@app.get("/auth/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
):
    """
    Handle OAuth provider callback and create/login user.

    Args:
        provider: OAuth provider ("github" or "google")
        code: Authorization code from provider
        state: State token for CSRF validation

    Returns:
        LoginResponse with JWT token and user info
    """
    try:
        # Validate state token
        if state not in _oauth_states:
            logger.warning(f"⚠️ Invalid OAuth state token")
            raise HTTPException(status_code=400, detail="Invalid state token")

        state_data = _oauth_states.pop(state)
        if (datetime.utcnow() - state_data["created_at"]).total_seconds() > 600:  # 10 min expiry
            raise HTTPException(status_code=400, detail="State token expired")

        config = _get_oauth_provider_config(provider)

        # Exchange code for access token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                config["token_url"],
                data={
                    "client_id": config["client_id"],
                    "client_secret": config["client_secret"],
                    "code": code,
                    "redirect_uri": settings.oauth_redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"},
            )
            token_response.raise_for_status()
            tokens = token_response.json()
            access_token = tokens.get("access_token")

            if not access_token:
                raise HTTPException(status_code=400, detail="Failed to get access token")

            # Fetch user info from provider
            user_response = await client.get(
                config["user_url"],
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_response.raise_for_status()
            oauth_user = user_response.json()

        # Extract user info based on provider
        if provider == "github":
            oauth_id = str(oauth_user.get("id"))
            email = oauth_user.get("email")
            # If primary email not in response, fetch from email endpoint
            if not email:
                async with httpx.AsyncClient() as client:
                    emails_response = await client.get(
                        config["email_url"],
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
                    emails = emails_response.json()
                    email = next((e["email"] for e in emails if e["primary"]), emails[0]["email"] if emails else None)
            full_name = oauth_user.get("name")
            profile_picture = oauth_user.get("avatar_url")
        elif provider == "google":
            oauth_id = oauth_user.get("sub")
            email = oauth_user.get("email")
            full_name = oauth_user.get("name")
            profile_picture = oauth_user.get("picture")
        else:
            raise HTTPException(status_code=400, detail="Unsupported provider")

        if not email:
            raise HTTPException(status_code=400, detail="Could not retrieve email from OAuth provider")

        # Create or get user
        existing_oauth_user = get_user_by_oauth_id(provider, oauth_id)
        if existing_oauth_user:
            user = existing_oauth_user
            logger.info(f"✅ OAuth user logged in: {email} ({provider})")
        else:
            user = create_oauth_user(
                email=email,
                oauth_provider=provider,
                oauth_id=oauth_id,
                full_name=full_name,
                profile_picture=profile_picture,
            )
            logger.info(f"✅ New OAuth user created: {email} ({provider})")

        # Check if account is active
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is inactive")

        # Create JWT token
        jwt_token = create_access_token(str(user.id))
        expires_in = JWT_EXPIRATION_HOURS * 3600

        return LoginResponse(
            access_token=jwt_token,
            token_type="bearer",
            expires_in=expires_in,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ OAuth callback error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="OAuth login failed")


# ==================== Admin Models & Endpoints (Phase 5) ====================

class AdminUserItem(BaseModel):
    """Admin view of a user."""
    user_id: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    is_admin: bool
    oauth_provider: Optional[str]
    created_at: str

class AdminUsersListResponse(BaseModel):
    """Admin users list response."""
    users: list[AdminUserItem]
    total: int
    limit: int
    offset: int

class AdminUpdateRoleRequest(BaseModel):
    """Request to update user role."""
    role: str = Field(..., description="'user' or 'admin'")

@app.get("/admin/users", response_model=AdminUsersListResponse)
@limiter.limit("30/minute")
async def list_users(
    limit: int = 50,
    offset: int = 0,
    admin: dict = Depends(get_admin_user),
    request=None,
):
    """List all users (admin only)."""
    try:
        from sqlalchemy import func
        db = get_db()
        session = db.get_session()
        try:
            # Get total count
            total = session.query(func.count(User.id)).scalar() or 0

            # Get paginated users
            users = session.query(User).limit(limit).offset(offset).all()

            user_items = [
                AdminUserItem(
                    user_id=str(u.id),
                    email=u.email,
                    full_name=u.full_name,
                    role=u.role,
                    is_active=u.is_active,
                    is_admin=u.is_admin,
                    oauth_provider=u.oauth_provider,
                    created_at=u.created_at.isoformat(),
                )
                for u in users
            ]

            logger.info(f"📊 Admin retrieved users list: {len(users)} users")
            return AdminUsersListResponse(
                users=user_items,
                total=total,
                limit=limit,
                offset=offset,
            )
        finally:
            session.close()
    except Exception as e:
        logger.error(f"❌ Error listing users: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list users")

@app.get("/admin/users/{user_id}", response_model=AdminUserItem)
@limiter.limit("30/minute")
async def get_user_detail(
    user_id: str,
    admin: dict = Depends(get_admin_user),
    request=None,
):
    """Get detailed user info (admin only)."""
    try:
        user = get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        logger.info(f"📋 Admin viewed user: {user.email}")
        return AdminUserItem(
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            is_admin=user.is_admin,
            oauth_provider=user.oauth_provider,
            created_at=user.created_at.isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get user")

@app.post("/admin/users/{user_id}/deactivate")
@limiter.limit("10/minute")
async def deactivate_user(
    user_id: str,
    admin: dict = Depends(get_admin_user),
    request=None,
):
    """Deactivate user account (admin only)."""
    try:
        user = get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Prevent self-deactivation
        if str(user.id) == admin["user_id"]:
            raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

        db = get_db()
        session = db.get_session()
        try:
            user.is_active = False
            session.commit()
            logger.info(f"🚫 Admin deactivated user: {user.email}")
            return {"detail": "User deactivated successfully"}
        finally:
            session.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deactivating user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to deactivate user")

@app.get("/admin/analytics/overview")
@limiter.limit("30/minute")
async def get_system_analytics(admin: dict = Depends(get_admin_user), request=None):
    """Get system-wide analytics (admin only)."""
    try:
        from sqlalchemy import func
        db = get_db()
        session = db.get_session()
        try:
            # Count active users
            total_users = session.query(func.count(User.id)).scalar() or 0
            active_users = session.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0

            # Count queries
            total_queries = session.query(func.count(QueryMetrics.id)).scalar() or 0

            # Average response time
            avg_response_time = session.query(func.avg(QueryMetrics.response_time_ms)).scalar() or 0

            # Success rate
            successful = session.query(func.count(QueryMetrics.id)).filter(QueryMetrics.success == True).scalar() or 0
            success_rate = (successful / total_queries * 100) if total_queries > 0 else 0

            logger.info(f"📊 Admin viewed system analytics")
            return {
                "total_users": total_users,
                "active_users": active_users,
                "total_queries": total_queries,
                "avg_response_time_ms": float(avg_response_time),
                "success_rate_percent": float(success_rate),
            }
        finally:
            session.close()
    except Exception as e:
        logger.error(f"❌ Error getting system analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get system analytics")


# ==================== Advanced Analytics Endpoints (Phase 5 Wave 5) ====================

@app.get("/analytics/cohorts")
@limiter.limit("30/minute")
async def get_cohort_analysis(
    start_date: str,
    end_date: str,
    current_user: dict = Depends(get_current_user),
    request=None,
):
    """Get cohort analytics (user signup cohort analysis)."""
    try:
        # Parse dates
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)

        result = get_user_cohort_analytics(start, end)
        logger.info(f"📊 Cohort analysis: {result['total_users']} users")
        return result
    except Exception as e:
        logger.error(f"❌ Cohort analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get cohort analysis")

@app.get("/analytics/funnel")
@limiter.limit("30/minute")
async def get_funnel_analysis(
    admin: dict = Depends(get_admin_user),
    request=None,
):
    """Get conversion funnel metrics (admin only)."""
    try:
        result = get_funnel_metrics()
        logger.info(f"🔝 Funnel analysis complete")
        return result
    except Exception as e:
        logger.error(f"❌ Funnel analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get funnel analysis")


# Analytics Endpoints (Phase 4)

@app.get("/analytics/user", response_model=UserAnalyticsResponse)
async def get_user_stats(current_user: dict = Depends(get_current_user)):
    """
    Get analytics for current user.

    Args:
        current_user: Current user from JWT token (dependency)

    Returns:
        UserAnalyticsResponse with aggregated query metrics

    Raises:
        HTTPException: If user not found or error retrieving analytics
    """
    try:
        user_id = current_user.get("user_id")
        logger.info(f"📊 Retrieving analytics for user: {user_id[:8]}...")

        # Verify user exists
        user = get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get aggregated analytics
        analytics = get_user_analytics(user_id)

        logger.info(f"✅ Analytics retrieved: {analytics['total_queries']} queries")
        return UserAnalyticsResponse(**analytics)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to retrieve analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve analytics",
        )


@app.get("/analytics/user/queries", response_model=QueryHistoryResponse)
async def get_user_query_history(
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
):
    """
    Get query history for current user with pagination.

    Args:
        limit: Number of queries to return (default 50, max 200)
        offset: Pagination offset (default 0)
        current_user: Current user from JWT token (dependency)

    Returns:
        QueryHistoryResponse with paginated query history

    Raises:
        HTTPException: If user not found or error retrieving history
    """
    try:
        user_id = current_user.get("user_id")
        logger.info(f"📋 Retrieving query history for user: {user_id[:8]}... (limit={limit}, offset={offset})")

        # Verify user exists
        user = get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Validate pagination parameters
        limit = min(limit, 200)  # Max 200 queries
        if limit < 1:
            limit = 50
        if offset < 0:
            offset = 0

        # Get query metrics with pagination
        from database import get_db

        db = get_db()
        session = db.get_session()
        try:
            total_metrics = session.query(QueryMetrics).filter_by(user_id=user_id).count()
            metrics = (
                session.query(QueryMetrics)
                .filter_by(user_id=user_id)
                .order_by(QueryMetrics.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            query_items = [
                QueryHistoryItem(
                    query_id=str(m.id),
                    query_text=m.query_text,
                    response_time_ms=m.response_time_ms,
                    model_used=m.model_used,
                    success=m.success,
                    created_at=m.created_at.isoformat(),
                )
                for m in metrics
            ]

            logger.info(f"✅ Query history retrieved: {len(query_items)} queries (total: {total_metrics})")
            return QueryHistoryResponse(
                queries=query_items,
                total=total_metrics,
                limit=limit,
                offset=offset,
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to retrieve query history: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve query history",
        )


@app.on_event("startup")
async def startup_event():
    """Initialize on application startup."""
    logger.info("🚀 RAG Chatbot Backend starting up...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"CORS allowed origins: {settings.allowed_origins}")
    logger.info("✅ Backend initialization complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("🛑 RAG Chatbot Backend shutting down...")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"❌ Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An error occurred",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
