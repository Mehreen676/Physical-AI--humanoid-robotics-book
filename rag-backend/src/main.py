"""
RAG Chatbot Backend - FastAPI Application
Integrated Retrieval-Augmented Generation chatbot for interactive learning.
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr
import logging
from datetime import datetime, timedelta
import os
import sys
import jwt
import json
from typing import Optional

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from config import get_settings
from ingest_service import get_ingest_service
from retrieval_service import get_retriever
from generation_service import get_generation_agent
from database import (
    add_session, add_message, get_session, get_session_history, DatabaseSession,
    add_user, get_user_by_email, get_user_by_id, verify_password,
    get_user_analytics, add_query_metric, QueryMetrics
)
from validation import validate_response_in_context
from embeddings import get_embedding_generator
import time
import uuid

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
    """Create a JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(hours=JWT_EXPIRATION_HOURS)

    expire = datetime.utcnow() + expires_delta
    to_encode = {"sub": str(user_id), "exp": expire}

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"user_id": user_id}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Dependency to get current authenticated user from Bearer token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = parts[1]
    return verify_token(token)


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
    Logout endpoint (placeholder for stateless JWT).

    In a stateless JWT system, logout is handled client-side by discarding the token.
    This endpoint serves as a confirmation endpoint.

    Args:
        current_user: Current user from JWT token (dependency)

    Returns:
        dict: Confirmation message
    """
    try:
        user_id = current_user.get("user_id")
        logger.info(f"👋 User logged out: {user_id[:8]}...")
        return {"detail": "Logged out successfully"}

    except Exception as e:
        logger.error(f"❌ Logout error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Logout failed",
        )


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
