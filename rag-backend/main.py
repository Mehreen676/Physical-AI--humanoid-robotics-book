"""
Main entry point for the RAG Chatbot Backend
Imports the FastAPI application from src.api
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import the FastAPI app from the integrated api module
from src.api import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",  # Using this module's app instance
        host="0.0.0.0",
        port=8000,
        reload=False
    )