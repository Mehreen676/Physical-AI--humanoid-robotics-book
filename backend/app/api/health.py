"""Health check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from qdrant_client import QdrantClient
import logging

from app.core.database import get_db, check_db_connection

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """Basic health check endpoint."""
    return {
        "status": "ok",
        "service": "Physical AI Textbook Backend",
        "version": "0.1.0",
    }


@router.get("/api/health")
async def detailed_health_check(db: Session = Depends(get_db)) -> dict:
    """Detailed health check with database status."""
    db_status = "unknown"
    qdrant_status = "unknown"

    # Check Postgres
    try:
        db.execute("SELECT 1")
        db_status = "ok"
        logger.info("✓ Postgres connection OK")
    except Exception as e:
        db_status = "error"
        logger.error(f"✗ Postgres connection failed: {e}")

    # Check Qdrant (if configured)
    try:
        # Import here to avoid issues if credentials not set
        from app.core.config import settings
        if settings.QDRANT_URL:
            client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
            )
            client.get_collections()
            qdrant_status = "ok"
            logger.info("✓ Qdrant connection OK")
        else:
            qdrant_status = "not_configured"
    except Exception as e:
        qdrant_status = "error"
        logger.error(f"✗ Qdrant connection failed: {e}")

    return {
        "status": "healthy" if db_status == "ok" else "degraded",
        "postgres": db_status,
        "qdrant": qdrant_status,
        "service": "Physical AI Textbook Backend",
        "version": "0.1.0",
    }
