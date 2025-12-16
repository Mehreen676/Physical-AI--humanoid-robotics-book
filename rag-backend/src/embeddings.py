"""
Embedding Generation Module
Handles text embeddings via OpenAI API with error handling and cost tracking.
"""

from openai import OpenAI, RateLimitError, APIConnectionError
import logging
import time
from typing import List, Union
from config import get_settings

logger = logging.getLogger(__name__)

# Token tracking for cost calculation
_tokens_used = {"input": 0, "total": 0}


class EmbeddingGenerator:
    """Generate embeddings using OpenAI API."""

    # OpenAI pricing (as of 2024)
    PRICE_PER_1M_INPUT_TOKENS = 0.02  # text-embedding-3-small
    EMBEDDING_DIMENSION = 1536

    def __init__(self):
        """Initialize OpenAI client."""
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_embedding_model
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        logger.info(f"✅ Embedding generator initialized: {self.model}")

    def embed_text(
        self,
        text: str,
        retry_count: int = 0,
    ) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed (max ~8000 tokens)
            retry_count: Internal retry counter

        Returns:
            List of 1536 floats representing the embedding

        Raises:
            Exception: If embedding fails after retries
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
            )

            embedding = response.data[0].embedding
            tokens_used = response.usage.prompt_tokens

            # Track tokens for cost monitoring
            _tokens_used["input"] += tokens_used
            _tokens_used["total"] += tokens_used

            logger.debug(
                f"✅ Embedded text ({len(text)} chars, {tokens_used} tokens)"
            )
            return embedding

        except RateLimitError as e:
            if retry_count < self.max_retries:
                wait_time = self.retry_delay * (2 ** retry_count)
                logger.warning(
                    f"⚠️  Rate limited. Retrying in {wait_time}s... "
                    f"(attempt {retry_count + 1}/{self.max_retries})"
                )
                time.sleep(wait_time)
                return self.embed_text(text, retry_count + 1)
            else:
                logger.error(f"❌ Rate limit exceeded after {self.max_retries} retries")
                raise

        except APIConnectionError as e:
            logger.error(f"❌ API connection error: {e}")
            raise

        except Exception as e:
            logger.error(f"❌ Error generating embedding: {e}")
            raise

    def embed_texts(
        self,
        texts: List[str],
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in a single API call.

        Args:
            texts: List of texts to embed (up to 2048 texts per call)

        Returns:
            List of embedding vectors (same order as input)

        Raises:
            ValueError: If texts list is empty or too large
        """
        if not texts:
            raise ValueError("No texts provided")

        if len(texts) > 2048:
            raise ValueError(f"Too many texts: {len(texts)} (max 2048)")

        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
            )

            # Extract embeddings in order
            embeddings = [item.embedding for item in response.data]
            tokens_used = response.usage.prompt_tokens

            # Track tokens
            _tokens_used["input"] += tokens_used
            _tokens_used["total"] += tokens_used

            logger.info(
                f"✅ Embedded {len(texts)} texts ({tokens_used} tokens)"
            )
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


# Singleton instance
_embedding_generator_instance = None


def get_embedding_generator() -> EmbeddingGenerator:
    """Get or create embedding generator instance."""
    global _embedding_generator_instance
    if _embedding_generator_instance is None:
        _embedding_generator_instance = EmbeddingGenerator()
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
