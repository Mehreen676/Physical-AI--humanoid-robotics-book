"""
Configuration management for RAG Chatbot backend.
Loads environment variables and validates required keys.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator, ConfigDict
from typing import List, Optional
import logging
import os

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application configuration settings."""

    model_config = ConfigDict(env_file=".env", case_sensitive=False, extra='allow')

    # FastAPI Configuration
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    environment: str = "development"

    # OpenAI Configuration
    openai_api_key: str
    openai_embedding_model: str = "text-embedding-3-small"
    openai_llm_model: str = "gpt-4o"
    openai_llm_fallback_model: str = "gpt-3.5-turbo"
    openai_temperature: float = 0.3
    openai_max_tokens: int = 500

    # Qdrant Configuration
    qdrant_url: str
    qdrant_api_key: str
    qdrant_collection_name: str = "book_v1.0_chapters"

    # Neon Postgres Configuration
    database_url: str

    # Chat Configuration
    rate_limit_queries_per_minute: int = 10
    session_timeout_hours: int = 24
    max_selected_text_tokens: int = 2000
    max_selected_text_characters: int = 10000

    # CORS Configuration (parsed from comma-separated string)
    allowed_origins_str: str = "http://localhost:3000"

    # JWT/Auth Configuration (Phase 4+)
    secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # OAuth 2.0 Configuration (Phase 5 - optional, nullable)
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    oauth_redirect_uri: str = "http://localhost:3000/auth/callback"

    # Phase 6 - MFA Configuration
    mfa_enabled: bool = True
    mfa_issuer_name: str = "RAG-Chatbot"
    mfa_required_for_admins: bool = True
    totp_time_step: int = 30
    totp_window: int = 1

    # Phase 6 - Refresh Token Configuration
    refresh_token_enabled: bool = True
    refresh_token_expiration_days: int = 30
    access_token_expiration_minutes: int = 15
    enable_token_rotation: bool = True
    max_refresh_token_chains: int = 3

    # Phase 6 - API Key Configuration
    api_keys_enabled: bool = True
    api_key_default_expiration_days: int = 365
    max_api_keys_per_user: int = 10
    api_key_length: int = 32

    # Phase 6 - RBAC Configuration
    rbac_enabled: bool = True
    default_role: str = "user"
    permission_check_cache_ttl: int = 300  # 5 minutes

    # Logging
    log_level: str = "INFO"

    def __init__(self, **data):
        super().__init__(**data)
        self._validate_required_keys()

    @property
    def allowed_origins(self) -> List[str]:
        """Parse allowed origins from comma-separated string."""
        return [
            origin.strip()
            for origin in self.allowed_origins_str.split(",")
            if origin.strip()
        ]

    def _validate_required_keys(self):
        """Validate that all required keys are present."""
        required_keys = [
            "openai_api_key",
            "qdrant_url",
            "qdrant_api_key",
            "database_url",
        ]

        missing_keys = [
            key for key in required_keys if not getattr(self, key, None)
        ]

        if missing_keys:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_keys)}. "
                f"Please check your .env file."
            )

        logger.info("✅ All required configuration keys validated successfully.")


def get_settings() -> Settings:
    """Get or create settings instance."""
    try:
        return Settings()
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        raise
