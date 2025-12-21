"""
Main entry point for the RAG Chatbot Backend
Imports the FastAPI application from src.api
"""

import sys
import os
from pathlib import Path

# ============================================================================
# Python Path Configuration (for container deployments)
# ============================================================================
# Aggressively add paths to handle various deployment contexts
_current_file = Path(__file__).resolve()
_project_root = _current_file.parent  # Project root (where main.py is)

# Add paths to sys.path (only if not already present)
_paths_to_add = [
    str(_project_root),                     # Project root (where main.py is)
    str(_project_root / "src"),             # src directory
    os.getcwd(),                            # Current working directory
    os.path.dirname(os.getcwd()),           # Parent of cwd (for nested structures)
]

for _path in _paths_to_add:
    if _path and _path not in sys.path:
        sys.path.insert(0, _path)

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