"""
Configuration management for semantic retrieval layer.
"""

import os
from pydantic import BaseModel, Field


class RetrievalConfig(BaseModel):
    """Configuration for semantic retrieval system."""

    # Qdrant Configuration
    qdrant_url: str = Field(default_factory=lambda: os.getenv("QDRANT_URL", "").strip())
    # Local Qdrant me API key empty ho sakti hai, is liye optional rakhi hai
    qdrant_api_key: str = Field(default_factory=lambda: os.getenv("QDRANT_API_KEY", "").strip())
    collection_name: str = Field(default_factory=lambda: os.getenv("COLLECTION_NAME", "data_collection").strip())

    # Embedding Configuration
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", "").strip())
    use_mock_embeddings: bool = Field(
        default_factory=lambda: os.getenv("USE_MOCK_EMBEDDINGS", "false").lower().strip() == "true"
    )
    embedding_dimension: int = Field(default_factory=lambda: int(os.getenv("EMBEDDING_DIMENSION", "768")))

    # Normal Mode Retrieval Parameters
    retrieval_top_k: int = Field(default_factory=lambda: int(os.getenv("RETRIEVAL_TOP_K", "5")))
    retrieval_score_threshold: float = Field(
        default_factory=lambda: float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", "0.05"))
    )

    # Selected Text Mode Retrieval Parameters
    selected_text_top_k: int = Field(default_factory=lambda: int(os.getenv("SELECTED_TEXT_TOP_K", "3")))
    selected_text_score_threshold: float = Field(
        default_factory=lambda: float(os.getenv("SELECTED_TEXT_SCORE_THRESHOLD", "0.05"))
    )

    # Retry Configuration
    max_retries: int = Field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))
    retry_delay: float = Field(default_factory=lambda: float(os.getenv("RETRY_DELAY", "1.0")))

    def validate_required_fields(self) -> None:
        """Validate that required configuration fields are set."""
        if not self.qdrant_url:
            raise ValueError("QDRANT_URL is required")

        # Gemini key sirf tab required hai jab mock embeddings OFF hon
        if not self.use_mock_embeddings and not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when USE_MOCK_EMBEDDINGS=false")

        # QDRANT_API_KEY local me empty ho sakti hai — required NAHI
        # (Agar cloud/secured Qdrant ho to env me set kar do)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_config() -> RetrievalConfig:
    """
    Get validated retrieval configuration.
    """
    config = RetrievalConfig()
    config.validate_required_fields()
    return config
