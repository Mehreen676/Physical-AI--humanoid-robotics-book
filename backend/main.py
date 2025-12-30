"""
BookRAGAgent FastAPI Application

Main entry point for the hallucination-free RAG chatbot backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from backend.config import settings
from backend.api import routes

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

# Startup event
@app.on_event("startup")
async def startup():
    """Validate configuration and initialize services on startup."""
    logger.info("BookRAGAgent starting up...")
    # Configuration validation happens in settings module
    logger.info("Configuration validated successfully")

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
