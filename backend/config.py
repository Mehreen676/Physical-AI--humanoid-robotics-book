"""
Configuration module for BookRAGAgent.

Loads and validates environment variables at startup.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator, Field
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Find .env file - search in multiple locations
def find_env_file():
    """Find .env file in project root or backend directory."""
    locations = [
        Path.cwd() / ".env",
        Path(__file__).parent.parent / ".env",
        Path(__file__).parent / ".env",
    ]
    for path in locations:
        if path.exists():
            logger.info(f"Found .env file at: {path}")
            return str(path)
    logger.warning("No .env file found in standard locations")
    return None

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    base_url: str = Field(default="http://localhost:8000", env="BASE_URL")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Qdrant Configuration (Vector Database)
    qdrant_url: str = Field(default="", env="QDRANT_URL")
    qdrant_api_key: str = Field(default="", env="QDRANT_API_KEY")
    collection_name: str = Field(default="book-chunks", env="COLLECTION_NAME")

    # OpenRouter Configuration (LLM Provider)
    openrouter_api_key: str = Field(default="", env="OPENROUTER_API_KEY")
    openrouter_url: str = Field(default="https://openrouter.io/api/v1", env="OPENROUTER_URL")
    model_name: str = Field(default="claude-3-5-sonnet", env="MODEL_NAME")

    # Database Configuration (Neon PostgreSQL)
    database_url: str = Field(default="", env="DATABASE_URL")

    # Embeddings Configuration
    embeddings_provider: str = Field(default="cohere", env="EMBEDDINGS_PROVIDER")
    embeddings_api_key: Optional[str] = Field(default=None, env="EMBEDDINGS_API_KEY")
    cohere_embedding_model: str = Field(default="embed-english-light-v3.0", env="COHERE_EMBEDDING_MODEL")

    # RAG Configuration
    retrieval_top_k: int = Field(default=5, env="RETRIEVAL_TOP_K")
    similarity_threshold: float = Field(default=0.7, env="SIMILARITY_THRESHOLD")
    session_retention_days: int = Field(default=90, env="SESSION_RETENTION_DAYS")

    class Config:
        env_file = find_env_file() or ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env file

    @field_validator("qdrant_url", mode="before")
    @classmethod
    def validate_qdrant_url(cls, v):
        """Validate Qdrant URL is configured."""
        if not v:
            raise ValueError("QDRANT_URL is required")
        return v

    @field_validator("qdrant_api_key", mode="before")
    @classmethod
    def validate_qdrant_api_key(cls, v):
        """Validate Qdrant API key is configured."""
        if not v:
            raise ValueError("QDRANT_API_KEY is required")
        return v

    @field_validator("openrouter_api_key", mode="before")
    @classmethod
    def validate_openrouter_api_key(cls, v):
        """Validate OpenRouter API key is configured."""
        if not v:
            raise ValueError("OPENROUTER_API_KEY is required")
        return v

    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v):
        """Validate database URL is configured."""
        if not v:
            raise ValueError("DATABASE_URL is required")
        if not v.startswith("postgresql://"):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v

    @field_validator("similarity_threshold", mode="before")
    @classmethod
    def validate_similarity_threshold(cls, v):
        """Validate similarity threshold is between 0 and 1."""
        threshold = float(v) if isinstance(v, str) else v
        if not (0 <= threshold <= 1):
            raise ValueError("SIMILARITY_THRESHOLD must be between 0 and 1")
        return threshold

# Create settings instance (validates on import)
try:
    settings = Settings()
    logger.info("Configuration loaded and validated successfully")
except ValueError as e:
    logger.error(f"Configuration validation failed: {e}")
    raise
