"""
Embeddings service for vectorizing text.

Provides EmbeddingsService interface for converting text to embedding vectors.
"""

import httpx
import logging
from typing import List, Optional
from backend.config import settings

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service for generating text embeddings."""

    def __init__(self, provider: str = "cohere", api_key: Optional[str] = None):
        """
        Initialize embeddings service.

        Args:
            provider: Embeddings provider ('cohere', 'openai', etc.)
            api_key: API key for the provider
        """
        self.provider = provider or settings.embeddings_provider
        self.api_key = api_key or settings.embeddings_api_key
        self.timeout = 30.0

        if not self.api_key:
            raise ValueError(f"API key not configured for {self.provider} embeddings")

    async def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (list of floats)

        Raises:
            Exception: If embedding generation fails
        """
        if self.provider == "cohere":
            return await self._embed_cohere([text])
        else:
            raise ValueError(f"Unsupported embeddings provider: {self.provider}")

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            Exception: If embedding generation fails
        """
        if self.provider == "cohere":
            return await self._embed_cohere(texts)
        else:
            raise ValueError(f"Unsupported embeddings provider: {self.provider}")

    async def _embed_cohere(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using Cohere API.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "texts": texts,
                "model": "embed-english-v3.0",
                "input_type": "search_document",
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    "https://api.cohere.ai/v1/embed",
                    json=payload,
                    headers=headers
                )

            if response.status_code != 200:
                error_msg = f"Cohere API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)

            data = response.json()
            embeddings = data.get("embeddings", [])

            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings

        except httpx.TimeoutException:
            error_msg = f"Cohere API timeout after {self.timeout}s"
            logger.error(error_msg)
            raise Exception(error_msg)
        except httpx.HTTPError as e:
            error_msg = f"Cohere API HTTP error: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    async def health_check(self) -> dict:
        """
        Check embeddings service health.

        Returns:
            Dictionary with 'status' key
        """
        try:
            await self.embed("test")
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"Embeddings service health check failed: {e}")
            return {"status": "error", "message": str(e)}
