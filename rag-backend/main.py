"""
Main entry point for the RAG Chatbot Backend
Imports the FastAPI application from src.api
"""

import sys
import os
from pathlib import Path

# Fix Python path for module imports
# This ensures the project root is in the path so src module can be imported
_current_file = Path(__file__).resolve()
_project_root = _current_file.parent  # Project root (where main.py is)

# Add both the project root and src directory to sys.path
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

_src_path = _project_root / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

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