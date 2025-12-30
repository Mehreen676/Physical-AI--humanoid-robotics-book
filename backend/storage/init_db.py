"""
Database initialization module.

Creates and initializes database schema from SQLAlchemy models.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session as SASession
import logging
from backend.storage.models import Base, User, Session, ChatMessage
from backend.config import settings

logger = logging.getLogger(__name__)


def init_db():
    """Initialize database schema."""
    try:
        engine = create_engine(settings.database_url)

        # Create all tables
        Base.metadata.create_all(engine)
        logger.info("Database schema initialized successfully")

        return engine
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def get_engine():
    """Get or create database engine."""
    return create_engine(settings.database_url)


def create_session():
    """Create a new database session."""
    engine = get_engine()
    return SASession(engine)


def health_check():
    """Check database connection health."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return {"status": "ok"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "error", "message": str(e)}
