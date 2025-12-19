"""
Simple RAG Chatbot Backend - FastAPI Application
SPEC-COMPLIANT implementation with minimal, focused functionality.

GOAL: Provide a clean, stable, production-ready backend with a single /query endpoint
that follows the exact spec: POST /query with {"question": "string"} -> {"answer": "string"}

STACK: FastAPI, Qdrant Cloud, TF-IDF Embeddings (FREE), PostgreSQL
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import time
from src.config import get_settings
from src.embeddings import embed_text
from src.vector_store import get_vector_store
from src.simple_generation_service import generate_response_with_context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize services
try:
    settings = get_settings()
    vector_store = get_vector_store()
except Exception as e:
    logger.error(f"❌ Failed to initialize services: {e}")
    raise

# Initialize FastAPI app
app = FastAPI(
    title="RAG Chatbot Backend - Spec Compliant",
    description="Simple RAG system with Cohere embeddings and Qdrant vector store",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Request/Response Models
class QueryRequest(BaseModel):
    """Request model for content query."""
    question: str

class QueryResponse(BaseModel):
    """Response model for query result."""
    answer: str

# Main query endpoint - SPEC-COMPLIANT
@app.post("/query", response_model=QueryResponse)
async def query_content(request: QueryRequest):
    """
    SPEC-COMPLIANT query endpoint.

    Input: {"question": "string"}
    Output: {"answer": "string"}

    RAG Pipeline (STRICT ORDER):
    1. Accept POST request at /query
    2. Generate embeddings using Cohere
    3. Search Qdrant collection "aibook_chunk"
    4. Retrieve payload["text"] from results
    5. If results are empty, return a graceful fallback response
    6. Build prompt using retrieved context ONLY
    7. Generate final answer
    8. Return JSON
    """
    start_time = time.time()

    try:
        logger.info(f"❓ Processing query: '{request.question}'")

        # Validate input
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        # 1. Generate embeddings using Cohere
        logger.info("📝 Generating embeddings...")
        query_embedding = embed_text(request.question)

        # 2. Search Qdrant collection "aibook_chunk_tfidf" for TF-IDF vectors (cosine similarity, limit 3-5)
        logger.info(f"🔍 Searching Qdrant collection 'aibook_chunk_tfidf'...")

        # Use vector store to query vectors directly with TF-IDF collection
        search_results = vector_store.query_vectors(
            query_embedding=query_embedding,
            k=5,  # 3-5 results as specified
            collection_name="aibook_chunk_tfidf"
        )

        # 3. Retrieve payload["text"] from results
        logger.info("📄 Extracting content from results...")
        retrieved_texts = []
        for result in search_results:
            text_content = result.get("content", "")
            if text_content:
                retrieved_texts.append(text_content)

        # 4. If results are empty, return a graceful fallback response
        if not retrieved_texts:
            logger.warning("⚠️ No relevant results found in Qdrant")
            answer = "I couldn't find relevant information in the knowledge base to answer your question. Please try rephrasing or ask a different question."
            return QueryResponse(answer=answer)

        # 5. Build prompt using retrieved context ONLY
        context = "\n\n".join(retrieved_texts[:3])  # Limit to first 3 results for context

        # 6. Generate final answer
        logger.info("🤖 Generating response...")
        answer = generate_response_with_context(request.question, context)

        logger.info(f"✅ Query completed in {time.time() - start_time:.2f}s")
        return QueryResponse(answer=answer)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Query failed: {e}", exc_info=True)
        # 8. Never crash server (no 500) - return graceful error
        error_response = "Sorry, there was an issue processing your question. Please try again later."
        return QueryResponse(answer=error_response)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "RAG backend is running",
        "timestamp": time.time(),
    }


# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler to prevent 500 errors."""
    logger.error(f"❌ Unhandled exception: {exc}", exc_info=True)
    return QueryResponse(answer="An unexpected error occurred. Please try again later.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )