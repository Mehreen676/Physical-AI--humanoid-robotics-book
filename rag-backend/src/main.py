"""
RAG Chatbot Backend - FastAPI Application
Integrated Retrieval-Augmented Generation chatbot for interactive learning.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging
from datetime import datetime
import os
import sys

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from config import get_settings
from ingest_service import get_ingest_service
from retrieval_service import get_retriever
from generation_service import get_generation_agent
from database import add_session, add_message, get_session, DatabaseSession
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
