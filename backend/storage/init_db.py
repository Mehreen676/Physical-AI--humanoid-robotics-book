"""
Database initialization module.

Creates and initializes database schema from SQLAlchemy models.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session as SASession
import logging
from urllib.parse import urlparse, parse_qs
from storage.models import Base, User, Session, ChatMessage
from config import settings

logger = logging.getLogger(__name__)


def clean_database_url(url: str) -> str:
    """
    Remove query parameters from database URL and convert to synchronous psycopg2.

    asyncpg requires async context, so we use psycopg2 for sync operations.
    """
    # Parse the URL
    parsed = urlparse(url)

    # Reconstruct URL without query parameters, using psycopg2 driver
    scheme = "postgresql+psycopg2" if "postgresql" in parsed.scheme else parsed.scheme
    clean_url = f"{scheme}://{parsed.username}:{parsed.password}@{parsed.hostname}"

    # Add port if present
    if parsed.port:
        clean_url += f":{parsed.port}"

    # Add database name
    if parsed.path:
        clean_url += parsed.path

    logger.debug(f"Original URL: {url[:50]}...")
    logger.debug(f"Cleaned URL: {clean_url[:50]}...")

    return clean_url


def init_db():
    """Initialize database schema."""
    try:
        # Clean the database URL and convert to synchronous driver
        clean_url = clean_database_url(settings.database_url)
        engine = create_engine(clean_url)

        # Create all tables
        Base.metadata.create_all(engine)
        logger.info("Database schema initialized successfully")

        return engine
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def get_engine():
    """Get or create database engine."""
    clean_url = clean_database_url(settings.database_url)
    return create_engine(clean_url)


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
