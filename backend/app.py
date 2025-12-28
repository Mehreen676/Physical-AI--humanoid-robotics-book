"""
FastAPI Application for RAG Chat Service
Integrates chat endpoint with RAG Agent backend
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RAG Chat Service",
    description="Retrieval-Augmented Generation chat API for humanoid robotics textbook",
    version="1.0.0"
)

# Configure CORS (Cross-Origin Resource Sharing)
# Allow requests from Docusaurus frontend (both development and production)
cors_origins = [
    "http://localhost:3000",      # Docusaurus dev
    "http://localhost:8000",      # Alternative local dev
    "http://127.0.0.1:3000",      # Local IP variant
    "https://mehreen676.github.io",  # GitHub Pages production
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Length"],
)

logger.info(f"CORS configured for origins: {', '.join(cors_origins)}")


# Import and register routers
from chat_router import router as chat_router

app.include_router(chat_router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "RAG Chat Service is running"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "RAG Chat API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


if __name__ == "__main__":
    import uvicorn

    # Get port from environment or default to 8000
    port = int(os.getenv("PORT", "8000"))

    logger.info(f"Starting RAG Chat Service on port {port}")
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENV") == "development"
    )
