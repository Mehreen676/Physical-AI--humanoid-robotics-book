"""Main FastAPI application."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import init_db, Base, engine
from app.models.user import User, UserPreferences
from app.models.chat import ChatSession, ChatMessage
from app.models.content import Chapter, UserProgress
from app.api import health, auth

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    logger.info("=" * 50)
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info("=" * 50)

    try:
        init_db()
        logger.info("✓ Database initialized")
    except Exception as e:
        logger.error(f"✗ Failed to initialize database: {e}")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    try:
        engine.dispose()
        logger.info("✓ Database connections closed")
    except Exception as e:
        logger.error(f"✗ Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for Physical AI & Humanoid Robotics Interactive Textbook",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} → {response.status_code}")
    return response


# Include routers
app.include_router(health.router)
app.include_router(auth.router)

# Root endpoint
@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
