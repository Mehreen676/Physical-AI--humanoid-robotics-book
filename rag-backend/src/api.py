"""
RAG Chatbot API - FastAPI Application
Complete backend with models, endpoints, and middleware for RAG-based query handling.
"""

import logging
import time
import sys
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path

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

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr

# Configure logging (before any other logger calls)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import src modules IMMEDIATELY after path setup and logging (before lifespan)
try:
    from src.config import get_settings
    logger.info("✅ Successfully imported src.config")
except ImportError as e:
    logger.error(f"❌ Failed to import src.config: {e}")
    # Provide fallback
    def get_settings():
        class Settings:
            debug = False
        return Settings()


# ============================================================================
# Content Ingestion Models
# ============================================================================

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


class ChunkInfo(BaseModel):
    """Information about a processed chunk."""

    chunk_id: str = Field(..., description="Unique chunk identifier")
    content_hash: str = Field(..., description="SHA256 hash of content")
    tokens: int = Field(..., description="Token count")
    chapter: str = Field(..., description="Source chapter")
    section: str = Field(..., description="Source section")


class IngestResponse(BaseModel):
    """Response model for ingestion status."""

    ingested: int = Field(..., description="Number of new chunks ingested")
    skipped: int = Field(..., description="Number of duplicate chunks skipped")
    vectors_stored: int = Field(..., description="Number of vectors stored in Qdrant")
    total_chunks: int = Field(..., description="Total chunks generated")
    chunks: List[ChunkInfo] = Field(default_factory=list, description="Details of ingested chunks")
    error: Optional[str] = Field(default=None, description="Error message if ingestion failed")


# ============================================================================
# Query/RAG Models
# ============================================================================

class RetrievedChunkInfo(BaseModel):
    """Retrieved chunk information in response."""

    doc_id: str = Field(..., description="Document ID")
    chapter: str = Field(..., description="Chapter name")
    section: str = Field(..., description="Section name")
    subsection: Optional[str] = Field(default=None, description="Subsection name")
    content: str = Field(..., description="Chunk content")
    similarity_score: float = Field(..., description="Semantic similarity score (0-1)")
    chunk_index: int = Field(default=0, description="Chunk index in document")
    book_version: str = Field(default="v1.0", description="Book version")


class TokenMetrics(BaseModel):
    """Token usage metrics."""

    input: int = Field(..., description="Input tokens")
    output: int = Field(..., description="Output tokens")
    total: int = Field(..., description="Total tokens")
    estimated_cost: Optional[float] = Field(default=None, description="Estimated USD cost")


class LatencyMetrics(BaseModel):
    """Latency metrics for pipeline stages."""

    retrieval_ms: float = Field(..., description="Retrieval latency in milliseconds")
    generation_ms: float = Field(..., description="Generation latency in milliseconds")
    total_ms: float = Field(..., description="Total pipeline latency in milliseconds")


class QueryRequest(BaseModel):
    """Request model for content query (full-book or selected-text mode)."""

    query: str = Field(..., min_length=1, description="User question or query")
    mode: str = Field(default="full_book", description="Query mode: 'full_book' or 'selected_text'")
    selected_text: Optional[str] = Field(default=None, description="Text highlighted by user (for selected_text mode)")
    session_id: Optional[str] = Field(default=None, description="Chat session ID for continuity")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "How do I set up ROS 2 on Ubuntu?",
                "mode": "full_book",
                "session_id": "sess_123abc",
            }
        }


class QueryResponse(BaseModel):
    """Response model for RAG query."""

    query: str = Field(..., description="Original user query")
    answer: str = Field(..., description="Generated answer")
    retrieved_chunks: List[RetrievedChunkInfo] = Field(..., description="Retrieved context chunks")
    model: str = Field(..., description="Model used for generation")
    tokens: TokenMetrics = Field(..., description="Token usage")
    latency: LatencyMetrics = Field(..., description="Latency metrics")
    session_id: Optional[str] = Field(default=None, description="Session ID")
    mode: str = Field(default="full_book", description="Query mode used")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


# ============================================================================
# Authentication Models (Phase 4+)
# ============================================================================

class LoginRequest(BaseModel):
    """Login request."""

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password")


class LoginResponse(BaseModel):
    """Login response with access token."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user_id: str = Field(..., description="User ID")
    expires_in: int = Field(..., description="Token expiration in seconds")


class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password")
    full_name: str = Field(..., description="User full name")


class RegisterResponse(BaseModel):
    """Registration response."""

    user_id: str = Field(..., description="New user ID")
    email: str = Field(..., description="User email")
    message: str = Field(default="User registered successfully", description="Status message")


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str = Field(..., description="Refresh token")


class RefreshTokenResponse(BaseModel):
    """Refresh token response."""

    access_token: str = Field(..., description="New access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


# ============================================================================
# Analytics Models (Phase 4)
# ============================================================================

class QueryMetricData(BaseModel):
    """Query metrics snapshot."""

    user_id: str = Field(..., description="User ID")
    query: str = Field(..., description="Query string")
    response_time_ms: float = Field(..., description="Response time in milliseconds")
    tokens_used: int = Field(..., description="Tokens used")
    model: str = Field(..., description="Model used")
    timestamp: datetime = Field(..., description="Query timestamp")


class UserAnalyticsResponse(BaseModel):
    """User analytics summary."""

    user_id: str = Field(..., description="User ID")
    total_queries: int = Field(..., description="Total queries")
    total_tokens_used: int = Field(..., description="Total tokens used")
    avg_response_time_ms: float = Field(..., description="Average response time")
    most_common_topics: List[str] = Field(..., description="Most queried topics")
    last_query_timestamp: Optional[datetime] = Field(default=None, description="Last query timestamp")


# ============================================================================
# Health & Status Models
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="System status (healthy, degraded, down)")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="API version")
    services: Dict[str, str] = Field(..., description="Status of each service")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error detail message")
    timestamp: datetime = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(default=None, description="Request ID for debugging")


# ============================================================================
# Rate Limiting & Quota Models
# ============================================================================

class RateLimitInfo(BaseModel):
    """Rate limit information."""

    remaining: int = Field(..., description="Remaining requests in window")
    limit: int = Field(..., description="Request limit per window")
    reset_at: datetime = Field(..., description="When limit resets")


class QuotaInfo(BaseModel):
    """User quota information."""

    queries_remaining: int = Field(..., description="Remaining queries")
    tokens_remaining: int = Field(..., description="Remaining tokens")
    next_reset: datetime = Field(..., description="Next quota reset")


# ============================================================================
# FastAPI Application Initialization
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    # Startup
    logger.info("🚀 RAG Chatbot Backend starting...")
    try:
        # Import services - get_settings already imported at module level
        from src.vector_store import get_vector_store

        settings = get_settings()
        vector_store = get_vector_store()
        logger.info("✅ Services initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise

    yield

    # Shutdown
    logger.info("🛑 RAG Chatbot Backend shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="RAG Chatbot Backend",
    description="Production-ready RAG system with semantic search and LLM generation",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
try:
    from src.config import get_settings
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"✅ CORS configured for origins: {settings.allowed_origins}")
except Exception as e:
    logger.warning(f"⚠️ CORS configuration warning: {e}")
    # Fallback: allow localhost
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns:
        HealthResponse with status and service information
    """
    try:
        from src.vector_store import get_vector_store
        from src.config import get_settings

        vector_store = get_vector_store()
        settings = get_settings()

        services = {
            "vector_store": "healthy" if vector_store else "unhealthy",
            "config": "healthy" if settings else "unhealthy",
            "database": "healthy",  # Would check actual DB in production
        }

        status = "healthy" if all(s == "healthy" for s in services.values()) else "degraded"

        return HealthResponse(
            status=status,
            timestamp=datetime.utcnow(),
            version="2.0.0",
            services=services,
        )
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return HealthResponse(
            status="down",
            timestamp=datetime.utcnow(),
            version="2.0.0",
            services={"error": str(e)},
        )


# ============================================================================
# Content Ingestion Endpoint
# ============================================================================

@app.post("/ingest", response_model=IngestResponse)
async def ingest_content(request: IngestRequest):
    """
    Ingest content chunks into the RAG system.

    Args:
        request: IngestRequest with chapter content

    Returns:
        IngestResponse with ingestion statistics
    """
    start_time = time.time()

    try:
        from src.ingest_service import ContentIngestionService

        logger.info(f"📥 Ingesting content: {request.chapter}")

        ingest_service = ContentIngestionService()
        result = ingest_service.ingest_chapter(
            chapter=request.chapter,
            section=request.section,
            content=request.content,
            book_version=request.book_version,
        )

        latency_ms = (time.time() - start_time) * 1000
        logger.info(f"✅ Ingestion completed in {latency_ms:.1f}ms")

        return IngestResponse(
            ingested=result.get("ingested", 0),
            skipped=result.get("skipped", 0),
            vectors_stored=result.get("vectors_stored", 0),
            total_chunks=result.get("total_chunks", 0),
            chunks=result.get("chunks", []),
        )

    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}", exc_info=True)
        return IngestResponse(
            ingested=0,
            skipped=0,
            vectors_stored=0,
            total_chunks=0,
            chunks=[],
            error=str(e),
        )


# ============================================================================
# Query Endpoint (Main RAG Pipeline)
# ============================================================================

@app.post("/query", response_model=QueryResponse)
async def query_content(request: QueryRequest):
    """
    Main RAG query endpoint.

    Orchestrates:
    1. Semantic search via Qdrant
    2. Context assembly from retrieved chunks
    3. LLM generation with context
    4. Response formatting and metrics

    Args:
        request: QueryRequest with query and optional parameters

    Returns:
        QueryResponse with answer, retrieved chunks, and metrics
    """
    start_time = time.time()
    retrieval_start = start_time

    try:
        logger.info(f"❓ Processing query: '{request.query}' (mode={request.mode})")

        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        # Import services
        from src.retrieval_service import RetrieverAgent
        from src.generation_service import GeneratorAgent

        # Step 1: Retrieve relevant chunks
        logger.info("🔍 Retrieving relevant content...")
        retriever = RetrieverAgent(top_k=5, min_similarity=0.5)

        retrieved_chunks, retrieval_metadata = retriever.retrieve(
            query=request.query,
            mode=request.mode,
        )

        retrieval_time = (time.time() - retrieval_start) * 1000
        logger.info(f"✅ Retrieved {len(retrieved_chunks)} chunks in {retrieval_time:.1f}ms")

        # Convert retrieved chunks to response format
        response_chunks = [
            RetrievedChunkInfo(
                doc_id=chunk.doc_id,
                chapter=chunk.chapter,
                section=chunk.section,
                subsection=chunk.subsection,
                content=chunk.content,
                similarity_score=chunk.similarity_score,
                chunk_index=chunk.chunk_index,
                book_version=chunk.book_version,
            )
            for chunk in retrieved_chunks
        ]

        # Step 2: Generate response
        logger.info("🤖 Generating response...")
        generation_start = time.time()

        generator = GeneratorAgent()
        context = "\n\n".join([chunk.content for chunk in retrieved_chunks[:3]])

        generated = generator.generate(
            query=request.query,
            context=context,
            mode=request.mode,
        )

        generation_time = (time.time() - generation_start) * 1000
        logger.info(f"✅ Generated response in {generation_time:.1f}ms")

        # Step 3: Assemble response
        total_time = (time.time() - start_time) * 1000

        return QueryResponse(
            query=request.query,
            answer=generated.content,
            retrieved_chunks=response_chunks,
            model=generated.model,
            tokens=TokenMetrics(
                input=generated.input_tokens,
                output=generated.output_tokens,
                total=generated.total_tokens,
                estimated_cost=generated.total_tokens * 0.0001,  # Estimate
            ),
            latency=LatencyMetrics(
                retrieval_ms=retrieval_time,
                generation_ms=generation_time,
                total_ms=total_time,
            ),
            session_id=request.session_id,
            mode=request.mode,
            timestamp=datetime.utcnow(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


# ============================================================================
# OpenAI Agent Endpoint (Tool-Use Based RAG)
# ============================================================================

@app.post("/agent/query", response_model=QueryResponse)
async def query_with_openai_agent(request: QueryRequest):
    """
    OpenAI Agent-based query endpoint.

    Uses OpenAI Agent SDK with tool use to orchestrate:
    1. Semantic search via retrieve_relevant_chunks tool
    2. Context assembly from retrieved chunks
    3. Response generation via generate_response tool

    Args:
        request: QueryRequest with query and optional parameters

    Returns:
        QueryResponse with answer, retrieved chunks, and metrics
    """
    start_time = time.time()

    try:
        logger.info(f"🤖 OpenAI Agent query: '{request.query}' (mode={request.mode})")

        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        # Import agent with lazy loading to avoid startup issues
        try:
            from src.agent import get_openai_rag_agent
        except ImportError as e:
            raise HTTPException(
                status_code=503,
                detail=f"OpenAI Agent not available: {str(e)}"
            )

        # Initialize agent
        try:
            agent = get_openai_rag_agent()
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI Agent: {e}")
            raise HTTPException(
                status_code=503,
                detail="OpenAI Agent initialization failed"
            )

        # Process query with agent (tool-use based)
        try:
            rag_response = await agent.process_query_with_agent(
                query=request.query,
                user_id="anonymous",
                session_id=request.session_id,
                mode=request.mode,
            )

            total_time = (time.time() - start_time) * 1000

            # Convert RAGResponse to QueryResponse
            return QueryResponse(
                query=request.query,
                answer=rag_response.answer,
                retrieved_chunks=[
                    RetrievedChunkInfo(
                        doc_id=chunk.doc_id,
                        chapter=chunk.chapter,
                        section=chunk.section,
                        subsection=chunk.subsection,
                        content=chunk.content,
                        similarity_score=chunk.similarity_score,
                        chunk_index=chunk.chunk_index,
                        book_version=chunk.book_version,
                    )
                    for chunk in rag_response.retrieved_chunks
                ],
                model=rag_response.model,
                tokens=TokenMetrics(
                    input=rag_response.input_tokens,
                    output=rag_response.output_tokens,
                    total=rag_response.total_tokens,
                    estimated_cost=rag_response.total_tokens * 0.0001,
                ),
                latency=LatencyMetrics(
                    retrieval_ms=rag_response.retrieval_latency_ms,
                    generation_ms=rag_response.generation_latency_ms,
                    total_ms=total_time,
                ),
                session_id=request.session_id,
                mode=request.mode,
                timestamp=datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"OpenAI Agent query failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Agent query processing failed: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Agent endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with standard error format."""
    return ErrorResponse(
        error=f"HTTP {exc.status_code}",
        detail=exc.detail,
        timestamp=datetime.utcnow(),
        request_id=str(id(request)),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions gracefully."""
    logger.error(f"❌ Unhandled exception: {exc}", exc_info=True)
    return ErrorResponse(
        error="InternalServerError",
        detail="An unexpected error occurred. Please try again later.",
        timestamp=datetime.utcnow(),
        request_id=str(id(request)),
    )
