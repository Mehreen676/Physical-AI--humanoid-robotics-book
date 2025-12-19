#!/usr/bin/env python3
"""
Initialize the database tables for the RAG Chatbot.
"""

import sys
import os
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.database import get_db

def init_database():
    """Initialize database tables."""
    print("Initializing database tables...")

    try:
        db = get_db()
        db.create_tables()
        print("✅ Database tables created successfully!")
        print("✅ Database initialization complete!")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

    return True

if __name__ == "__main__":
    init_database()