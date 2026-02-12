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
    description="Grounded Q&A chatbot using Google Gemini",
    version="3.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# IMPORTANT: prefix removed here
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    print("=" * 60)
    print("Starting Agentic RAG Backend v3.0.0")
    print("=" * 60)

    config = get_config()

    retrieval_config = RetrievalConfig(
        qdrant_url=config.qdrant_url,
        qdrant_api_key=config.qdrant_api_key,
        collection_name=config.collection_name,
        gemini_api_key=config.gemini_api_key,
        use_mock_embeddings=config.use_mock_embeddings
    )

    retriever = SemanticRetriever(retrieval_config)
    set_retriever(retriever)
    print("[OK] Retrieval layer initialized")

    agent = GeminiAgent(
        api_key=config.gemini_api_key,
        model=config.gemini_model
    )
    set_agent(agent)
    print(f"[OK] Gemini agent initialized (model: {config.gemini_model})")

    print("[OK] SQLite database: chatbot.db")

    print("=" * 60)
    print("[OK] Agentic RAG Backend ready")
    print("=" * 60)


@app.get("/")
async def root():
    return {
        "message": "Agentic RAG Chatbot API",
        "version": "3.0.0"
    }
