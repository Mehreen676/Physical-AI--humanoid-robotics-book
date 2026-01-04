"""Configuration for Agentic RAG backend."""

import os
from pydantic import BaseModel, Field


class Config(BaseModel):
    """Application configuration."""

    # API Configuration
    api_host: str = Field(default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"))
    api_port: int = Field(default_factory=lambda: int(os.getenv("API_PORT", "8000")))
    cors_origins: list[str] = Field(default_factory=lambda: os.getenv("CORS_ORIGINS", "*").split(","))

    # Gemini Configuration (for agent)
    gemini_model: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))

    # Database Configuration
    database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    sqlite_db_path: str = Field(default_factory=lambda: os.getenv("SQLITE_DB_PATH", "chatbot.db"))

    # Retrieval Configuration (reuse from existing system)
    qdrant_url: str = Field(default_factory=lambda: os.getenv("QDRANT_URL", ""))
    qdrant_api_key: str = Field(default_factory=lambda: os.getenv("QDRANT_API_KEY", ""))
    collection_name: str = Field(default_factory=lambda: os.getenv("COLLECTION_NAME", "data_collection"))

    # Gemini Configuration
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    use_mock_embeddings: bool = Field(
        default_factory=lambda: os.getenv("USE_MOCK_EMBEDDINGS", "false").lower() == "true"
    )

    # Logging
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    def validate_required(self):
        """Validate required configuration."""
        required = {
            "gemini_api_key": self.gemini_api_key,
            "qdrant_url": self.qdrant_url,
            "qdrant_api_key": self.qdrant_api_key,
        }

        # Database URL optional (will use SQLite if not provided)

        missing = [k for k, v in required.items() if not v]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")


def get_config() -> Config:
    """Get validated configuration."""
    config = Config()
    config.validate_required()
    return config
