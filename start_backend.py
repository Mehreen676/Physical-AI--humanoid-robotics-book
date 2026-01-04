"""Simple startup script for backend_v3."""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables
from dotenv import load_dotenv
load_dotenv("backend_v3/.env")

# Import and run
from backend_v3.main import app
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Backend with Gemini (FREE)")
    print("=" * 60)

    # Get config
    from backend_v3.config import get_config
    config = get_config()

    # Start server
    uvicorn.run(
        app,
        host=config.api_host,
        port=config.api_port,
        reload=False,
        log_level="info"
    )
