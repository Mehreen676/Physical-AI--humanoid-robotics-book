"""
Cohere Embedding Generator Module
Handles text embeddings via Cohere API with error handling and cost tracking.
"""

import logging
import time
from typing import List, Union
import os
from config import get_settings

logger = logging.getLogger(__name__)

# Token tracking for cost calculation
_tokens_used = {"input": 0, "total": 0}


class CohereEmbeddingGenerator:
    """Generate embeddings using Cohere API (embed-english-v3.0)."""

    # Cohere pricing: $0.10 per 1M tokens input
    PRICE_PER_1M_INPUT_TOKENS = 0.10
    # embed-english-v3.0 model produces 1024-dimensional embeddings
    EMBEDDING_DIMENSION = 1024

    def __init__(self):
        """Initialize Cohere embedding generator."""
        try:
            import cohere
        except ImportError:
            raise ImportError("cohere package not found. Install with: pip install cohere")

        settings = get_settings()

        # Validate that Cohere API key is available
        if not hasattr(settings, 'cohere_api_key') or not settings.cohere_api_key:
            raise ValueError("COHERE_API_KEY environment variable is required")

        try:
            self.client = cohere.Client(settings.cohere_api_key)
        except Exception as e:
            logger.error(f"❌ Failed to initialize Cohere client: {e}")
            raise

        self.model_name = "embed-english-v3.0"
        self.max_retries = 3
        self.retry_delay = 1

        logger.info(f"✅ Using Cohere embeddings with model: {self.model_name}")

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding using Cohere API."""
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")

        try:
            response = self.client.embed(
                texts=[text],
                model=self.model_name,
                input_type="search_document"  # Optimal for document embeddings in RAG
            )
            embedding = response.embeddings[0]
            logger.debug(f"✅ Embedded text ({len(text)} chars)")
            # Track token usage (Cohere counts tokens differently - using text length as proxy)
            _tokens_used["input"] += len(text.split())
            _tokens_used["total"] += len(text.split())
            return embedding
        except Exception as e:
            logger.error(f"❌ Error generating embedding: {e}")
            raise

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using Cohere API."""
        if not texts:
            raise ValueError("No texts provided")

        # Filter out empty texts
        texts = [text for text in texts if text and text.strip()]
        if not texts:
            raise ValueError("No valid texts provided after filtering empty strings")

        try:
            response = self.client.embed(
                texts=texts,
                model=self.model_name,
                input_type="search_document"  # Optimal for document embeddings in RAG
            )
            embeddings = response.embeddings
            logger.info(f"✅ Embedded {len(texts)} texts")

            # Track token usage
            total_tokens = sum(len(text.split()) for text in texts)
            _tokens_used["input"] += total_tokens
            _tokens_used["total"] += total_tokens

            return embeddings
        except Exception as e:
            logger.error(f"❌ Error generating embeddings: {e}")
            raise

    def cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float],
    ) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First embedding vector
            vec2: Second embedding vector

        Returns:
            Cosine similarity score (0-1)
        """
        import math

        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have the same dimensionality")

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm_1 = math.sqrt(sum(a * a for a in vec1))
        norm_2 = math.sqrt(sum(b * b for b in vec2))

        if norm_1 == 0 or norm_2 == 0:
            return 0.0

        return dot_product / (norm_1 * norm_2)

    def get_cost_estimate(self) -> dict:
        """
        Get estimated cost for tokens used.

        Returns:
            Dict with token count and estimated cost
        """
        estimated_cost = (
            _tokens_used["input"] / 1_000_000 * self.PRICE_PER_1M_INPUT_TOKENS
        )
        return {
            "input_tokens": _tokens_used["input"],
            "total_tokens": _tokens_used["total"],
            "estimated_cost_usd": round(estimated_cost, 4),
        }

    def reset_token_counter(self):
        """Reset token usage counter (useful for testing)."""
        global _tokens_used
        _tokens_used = {"input": 0, "total": 0}
        logger.info("✅ Token counter reset")

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate number of tokens in text using simple heuristic.

        Args:
            text: Text to estimate token count for

        Returns:
            Estimated token count
        """
        # Simple heuristic: count words
        estimated = max(1, len(text.split()))
        return estimated


# Singleton instance
_embedding_generator_instance = None


def get_embedding_generator() -> CohereEmbeddingGenerator:
    """Get or create Cohere embedding generator instance."""
    global _embedding_generator_instance
    if _embedding_generator_instance is None:
        _embedding_generator_instance = CohereEmbeddingGenerator()
    return _embedding_generator_instance


# Convenience functions
def embed_text(text: str) -> List[float]:
    """Convenience function to embed single text."""
    return get_embedding_generator().embed_text(text)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Convenience function to embed multiple texts."""
    return get_embedding_generator().embed_texts(texts)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Convenience function for cosine similarity."""
    return get_embedding_generator().cosine_similarity(vec1, vec2)