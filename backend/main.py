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

# Parse CORS allowed origins from settings
allowed_origins_list = (
    [origin.strip() for origin in settings.allowed_origins.split(",")]
    if settings.allowed_origins != "*"
    else ["*"]
)

# Add CORS middleware with configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"CORS configured for origins: {allowed_origins_list}")

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
        "has_gemini_client": hasattr(app.state, "gemini_client"),
    }

# Startup event
@app.on_event("startup")
async def startup():
    """Validate configuration and initialize services on startup."""
    logger.info("BookRAGAgent starting up...")

    try:
        # Initialize database
        logger.info("Step 1: Initializing database...")
        from storage.init_db import init_db
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        init_db()
        logger.info("Database initialized")

        # Initialize session manager
        logger.info("Step 2: Initializing session manager...")
        from storage.sessions import SessionManager
        from storage.init_db import clean_database_url
        clean_url = clean_database_url(settings.database_url)
        engine = create_engine(clean_url)
        SessionLocal = sessionmaker(bind=engine)
        db_session = SessionLocal()
        session_manager = SessionManager(db_session)
        logger.info("Session manager initialized")

        # Initialize Qdrant retriever
        logger.info("Step 3: Initializing Qdrant retriever...")
        from rag.retrieval import QdrantRetriever
        qdrant_retriever = QdrantRetriever(
            qdrant_url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            collection_name=settings.collection_name
        )
        logger.info("Qdrant retriever initialized")

        # Initialize embeddings service
        logger.info("Step 4: Initializing embeddings service...")
        from services.embeddings import EmbeddingsService

        # Use configured provider (Cohere or TF-IDF)
        provider = settings.embeddings_provider
        api_key = settings.embeddings_api_key if provider == "cohere" else None
        model = settings.embeddings_model if provider == "cohere" else None

        embeddings_service = EmbeddingsService(
            provider=provider,
            api_key=api_key,
            model=model
        )

        # If using TF-IDF, fit vectorizer on indexed documents
        if provider == "tfidf":
            try:
                logger.info("  Retrieving indexed documents for TF-IDF vectorizer training...")
                all_documents = await qdrant_retriever.get_all_documents()
                if all_documents:
                    embeddings_service.fit_on_documents(all_documents)
                    logger.info(f"  ✓ TF-IDF vectorizer fitted on {len(all_documents)} documents")
                else:
                    logger.warning("  No documents found in Qdrant for vectorizer training")
            except Exception as e:
                logger.warning(f"  Could not pre-fit TF-IDF vectorizer: {e}")

        logger.info(f"Embeddings service initialized (provider: {provider})")

        # Initialize Gemini client
        logger.info("Step 5: Initializing Gemini client...")
        from services.gemini_service import GeminiClient
        gemini_client = GeminiClient(
            api_key=settings.gemini_api_key,
            model_name=settings.model_name
        )
        logger.info("Gemini client initialized")

        # Initialize RAG agent
        logger.info("Step 6: Initializing RAG agent...")
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
            embeddings_service=embeddings_service,
            top_k=settings.retrieval_top_k,
            similarity_threshold=settings.similarity_threshold
        )

        # Create sub-agents
        retrieval_agent = RetrievalSubAgent(vector_search)
        answer_agent = AnswerSubAgent(
            synthesis_skill=GroundedSynthesisSkill(gemini_client)
        )
        guardrails_agent = GuardrailsSubAgent(
            validation_skill=RetrievalValidationSkill(),
            hallucination_skill=AntiHallucinationSkill(gemini_client)
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
            gemini_client=gemini_client
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
