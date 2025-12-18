"""
Embedding Generation Module
Handles text embeddings via OpenAI API with error handling and cost tracking.
"""

import logging
import time
from typing import List, Union
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from config import get_settings

logger = logging.getLogger(__name__)

# Token tracking for cost calculation
_tokens_used = {"input": 0, "total": 0}

# Global vectorizer instance
_vectorizer = None
_corpus = []


def _initialize_vectorizer():
    """Initialize TF-IDF vectorizer with default corpus."""
    global _vectorizer, _corpus
    if _vectorizer is None:
        # Default corpus to fit the vectorizer
        _corpus = [
            "robotics is the technology of robots",
            "machine learning and artificial intelligence",
            "computer vision and image processing",
            "natural language processing and text analysis",
            "deep learning neural networks",
            "data science and analytics",
            "autonomous systems and control",
            "human robot interaction",
            "sensor fusion and perception",
        ]
        _vectorizer = TfidfVectorizer(max_features=300, ngram_range=(1, 2))
        _vectorizer.fit(_corpus)
        logger.info("✅ TF-IDF vectorizer initialized with corpus")


class EmbeddingGenerator:
    """Generate embeddings using TF-IDF (FREE, pure Python, no GPU/PyTorch needed)."""

    # TF-IDF is completely FREE and pure Python
    PRICE_PER_1M_INPUT_TOKENS = 0.0
    EMBEDDING_DIMENSION = 300

    def __init__(self):
        """Initialize TF-IDF embedding generator."""
        settings = get_settings()

        # Initialize global vectorizer
        _initialize_vectorizer()

        logger.info(f"✅ Using TF-IDF embeddings (pure Python, FREE, no API keys needed!)")

        self.max_retries = 3
        self.retry_delay = 1

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding using TF-IDF."""
        try:
            embedding = _vectorizer.transform([text]).toarray()[0]
            logger.debug(f"✅ Embedded text ({len(text)} chars)")
            return embedding.tolist()
        except Exception as e:
            logger.error(f"❌ Error generating embedding: {e}")
            raise

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using TF-IDF."""
        if not texts:
            raise ValueError("No texts provided")

        try:
            embeddings = _vectorizer.transform(texts).toarray()
            logger.info(f"✅ Embedded {len(texts)} texts")
            return embeddings.tolist()
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

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate number of tokens in text using simple heuristic.

        Uses approximate ratio: 1 token ≈ 4 characters (common for English text).
        For more accurate estimation, would need to use tiktoken or similar.

        Args:
            text: Text to estimate token count for

        Returns:
            Estimated token count
        """
        # Simple heuristic: ~4 characters per token
        # More accurate methods would use tiktoken with specific model
        estimated = max(1, len(text) // 4)
        return estimated


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
