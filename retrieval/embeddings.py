"""
Embedding service with support for Gemini and Mock embeddings.
"""

import time
import hashlib
import numpy as np
from abc import ABC, abstractmethod
from typing import List
import google.generativeai as genai


class EmbeddingService(ABC):
    """Abstract base class for embedding services."""

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for query text.

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector
        """
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return embedding dimension."""
        pass


class GeminiEmbeddings(EmbeddingService):
    """
    Gemini embeddings-001 service.

    Free tier limits:
    - 1,500 requests per day
    - 15 requests per minute
    """

    def __init__(self, api_key: str):
        """
        Initialize Gemini embeddings service.

        Args:
            api_key: Google Gemini API key
        """
        self.api_key = api_key
        self.model = "models/embedding-001"
        self._dimension = 768
        self._min_request_interval = 4.0  # 15 req/min = 1 req per 4 seconds
        self._last_request_time = 0.0

        # Configure Gemini
        genai.configure(api_key=self.api_key)

    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting to stay within free tier."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()

    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding using Gemini.

        Args:
            text: Input text to embed

        Returns:
            768-dimensional embedding vector

        Raises:
            Exception: If API call fails
        """
        self._enforce_rate_limit()

        result = genai.embed_content(
            model=self.model,
            content=text,
            task_type="retrieval_query"
        )

        return result['embedding']

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        return self._dimension


class MockEmbeddings(EmbeddingService):
    """
    Mock embedding service for testing.

    Uses MD5 hash + numpy random with fixed seed for deterministic embeddings.
    """

    def __init__(self, dimension: int = 768):
        """
        Initialize mock embeddings service.

        Args:
            dimension: Embedding dimension (default: 768 to match Gemini)
        """
        self._dimension = dimension

    def embed_query(self, text: str) -> List[float]:
        """
        Generate deterministic mock embedding.

        Args:
            text: Input text to embed

        Returns:
            768-dimensional mock embedding vector
        """
        # Use MD5 hash as seed for determinism
        hash_obj = hashlib.md5(text.encode('utf-8'))
        seed = int(hash_obj.hexdigest(), 16) % (2**32)

        # Generate deterministic random vector
        rng = np.random.RandomState(seed)
        embedding = rng.randn(self._dimension)

        # Normalize to unit length (for cosine similarity)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding.tolist()

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        return self._dimension


def get_embedding_service(use_mock: bool = False, api_key: str = "") -> EmbeddingService:
    """
    Factory function to create appropriate embedding service.

    Args:
        use_mock: If True, use MockEmbeddings; otherwise use GeminiEmbeddings
        api_key: Gemini API key (required if use_mock=False)

    Returns:
        EmbeddingService instance

    Raises:
        ValueError: If use_mock=False and api_key is empty
    """
    if use_mock:
        return MockEmbeddings()
    else:
        if not api_key:
            raise ValueError("api_key is required for GeminiEmbeddings")
        return GeminiEmbeddings(api_key)
