"""
BookRAGAgent FastAPI Application

Main entry point for the hallucination-free RAG chatbot backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
from pathlib import Path

# Add current directory to path for imports when running as script
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from api import routes

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="BookRAGAgent API",
    description="Hallucination-free RAG chatbot backend",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(routes.router)

# Root route
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "status": "ok",
        "service": "BookRAGAgent",
        "version": "1.0.0"
    }

# Debug endpoint to check app state
@app.get("/debug/state")
async def debug_state():
    """Debug endpoint to check app.state."""
    return {
        "has_rag_agent": hasattr(app.state, "rag_agent"),
        "has_session_manager": hasattr(app.state, "session_manager"),
        "has_qdrant_retriever": hasattr(app.state, "qdrant_retriever"),
        "has_openrouter_client": hasattr(app.state, "openrouter_client"),
    }

# Startup event
@app.on_event("startup")
async def startup():
    """Validate configuration and initialize services on startup."""
    logger.info("BookRAGAgent starting up...")

    try:
        # Initialize database
        from storage.init_db import init_db
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        init_db()
        logger.info("Database initialized")

        # Initialize session manager
        from storage.sessions import SessionManager
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db_session = SessionLocal()
        session_manager = SessionManager(db_session)
        logger.info("Session manager initialized")

        # Initialize Qdrant retriever
        from rag.retrieval import QdrantRetriever
        qdrant_retriever = QdrantRetriever(
            qdrant_url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            collection_name=settings.collection_name
        )
        logger.info("Qdrant retriever initialized")

        # Initialize embeddings service
        from services.embeddings import EmbeddingsService
        embeddings_service = EmbeddingsService(
            provider=settings.embeddings_provider,
            api_key=settings.embeddings_api_key
        )
        logger.info("Embeddings service initialized")

        # Initialize OpenRouter client
        from services.openrouter_service import OpenRouterClient
        openrouter_client = OpenRouterClient(
            api_key=settings.openrouter_api_key,
            model_name=settings.model_name
        )
        logger.info("OpenRouter client initialized")

        # Initialize RAG agent
        from agent.agent import BookRAGAgent
        from agent.sub_agents import (
            RetrievalSubAgent, AnswerSubAgent, GuardrailsSubAgent,
            SelectionModeSubAgent, MemorySubAgent
        )
        from rag.retrieval import VectorSearchSkill
        from rag.grounding import (
            GroundedSynthesisSkill, AntiHallucinationSkill,
            RetrievalValidationSkill, SelectedTextOverrideSkill,
            SessionPersistenceSkill
        )

        # Create vector search skill
        vector_search = VectorSearchSkill(
            retriever=qdrant_retriever,
            embeddings_service=embeddings_service
        )

        # Create sub-agents
        retrieval_agent = RetrievalSubAgent(vector_search)
        answer_agent = AnswerSubAgent(
            synthesis_skill=GroundedSynthesisSkill(openrouter_client)
        )
        guardrails_agent = GuardrailsSubAgent(
            validation_skill=RetrievalValidationSkill(),
            hallucination_skill=AntiHallucinationSkill(openrouter_client)
        )
        selection_agent = SelectionModeSubAgent()
        memory_agent = MemorySubAgent()

        # Create main RAG agent
        rag_agent = BookRAGAgent(
            retrieval_agent=retrieval_agent,
            answer_agent=answer_agent,
            guardrails_agent=guardrails_agent,
            selection_mode_agent=selection_agent,
            memory_agent=memory_agent
        )
        logger.info("RAG agent initialized")

        # Inject dependencies into app.state
        routes.set_dependencies(
            app=app,
            rag_agent=rag_agent,
            session_manager=session_manager,
            qdrant_retriever=qdrant_retriever,
            openrouter_client=openrouter_client
        )
        logger.info("Dependencies injected into app.state")

        logger.info("Configuration validated successfully")

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}", exc_info=True)
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown():
    """Clean up resources on shutdown."""
    logger.info("BookRAGAgent shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
