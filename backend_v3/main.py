"""FastAPI application entry point for Agentic RAG."""

import os
import sys
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend_v3.config import get_config
from backend_v3.agent import GeminiAgent
from backend_v3.api import router, set_agent, set_retriever
from retrieval import RetrievalConfig, SemanticRetriever

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Agentic RAG Chatbot",
    description="Grounded Q&A chatbot using Google Gemini (FREE) with strict grounding",
    version="3.0.0"
)

# Configure CORS - Allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Must be False when allow_origins is "*"
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")


# Add OPTIONS handler for CORS preflight
@app.options("/api/v1/{full_path:path}")
async def options_handler():
    """Handle CORS preflight requests."""
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    """Initialize agent and retriever on startup."""
    print("=" * 60)
    print("Starting Agentic RAG Backend v3.0.0")
    print("=" * 60)

    # Get configuration
    config = get_config()

    # Initialize retrieval configuration
    retrieval_config = RetrievalConfig(
        qdrant_url=config.qdrant_url,
        qdrant_api_key=config.qdrant_api_key,
        collection_name=config.collection_name,
        gemini_api_key=config.gemini_api_key,
        use_mock_embeddings=config.use_mock_embeddings
    )

    # Initialize retriever
    retriever = SemanticRetriever(retrieval_config)
    set_retriever(retriever)
    print("[OK] Retrieval layer initialized")

    # Initialize Gemini agent
    agent = GeminiAgent(
        api_key=config.gemini_api_key,
        model=config.gemini_model
    )
    set_agent(agent)
    print(f"[OK] Gemini agent initialized (model: {config.gemini_model})")

    # Test database connection
    from backend_v3.storage import get_database
    db = get_database()
    if config.database_url and config.database_url.startswith("postgres"):
        print("[OK] Neon Postgres connected")
    else:
        print(f"[OK] SQLite database: {config.sqlite_db_path}")

    print("=" * 60)
    print("[OK] Agentic RAG Backend ready")
    print("=" * 60)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Agentic RAG Chatbot API",
        "version": "3.0.0",
        "agent": "Google Gemini (FREE)",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    config = get_config()
    uvicorn.run(
        "backend_v3.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=True
    )
