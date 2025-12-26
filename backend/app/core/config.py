"""Application configuration and settings."""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Server Configuration
    APP_NAME: str = "Physical AI Textbook Backend"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))

    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/physical_ai_textbook"
    )

    # Qdrant Vector Database
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY", None)

    # Authentication & JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_DAYS: int = 30

    # Better-Auth Configuration
    BETTER_AUTH_SECRET: str = os.getenv(
        "BETTER_AUTH_SECRET",
        "your-better-auth-secret-change-in-production"
    )

    # Email Service (SendGrid)
    SENDGRID_API_KEY: Optional[str] = os.getenv("SENDGRID_API_KEY", None)
    SENDGRID_FROM_EMAIL: str = os.getenv(
        "SENDGRID_FROM_EMAIL",
        "no-reply@textbook.example.com"
    )

    # OpenAI API
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    OPENAI_EMBEDDING_MODEL: str = os.getenv(
        "OPENAI_EMBEDDING_MODEL",
        "text-embedding-3-small"
    )

    # CORS Configuration
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ]
    if frontend_url := os.getenv("FRONTEND_URL"):
        ALLOWED_ORIGINS.append(frontend_url)

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Monitoring
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", None)

    class Config:
        """Pydantic config."""
        env_file = ".env.local"
        case_sensitive = True


# Global settings instance
settings = Settings()
