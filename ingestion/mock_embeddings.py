"""
Mock embedding service for testing and demonstration.

Generates deterministic 768-dimensional vectors based on text hashing.
This is a drop-in replacement for GeminiEmbeddings when API quota is exhausted.

TODO: Replace with real GeminiEmbeddings after Gemini quota resets.
"""

import logging
import hashlib
import numpy as np
from typing import List

logger = logging.getLogger(__name__)


class MockEmbeddings:
    """
    Mock embeddings service for demonstration purposes.

    Generates deterministic 768-dimensional vectors using text hashing.
    Compatible with GeminiEmbeddings interface for drop-in replacement.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize mock embeddings service.

        Args:
            *args: Ignored (for compatibility with GeminiEmbeddings)
            **kwargs: Ignored (for compatibility with GeminiEmbeddings)
        """
        self.embedding_dim = 768

        logger.warning(
            "=" * 60 + "\n"
            "USING MOCK EMBEDDINGS (Gemini quota exhausted)\n"
            "Generating deterministic hash-based 768-dim vectors\n"
            "TODO: Replace with real Gemini embeddings after quota reset\n"
            "=" * 60
        )

    def embed_text(self, text: str) -> List[float]:
        """
        Generate deterministic mock embedding for text.

        Uses MD5 hash of text as seed for reproducible vector generation.

        Args:
            text: Input text

        Returns:
            768-dimensional vector as list of floats
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        # Create deterministic seed from text hash
        text_hash = hashlib.md5(text.encode()).hexdigest()
        seed = int(text_hash[:8], 16)  # Use first 8 hex chars as seed

        # Generate reproducible random vector
        np.random.seed(seed)
        embedding = np.random.randn(self.embedding_dim)

        # Normalize to unit length (cosine similarity compatible)
        embedding = embedding / np.linalg.norm(embedding)

        logger.debug(f"Generated mock embedding for text (length={len(text)})")

        return embedding.tolist()

    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate mock embeddings for multiple texts.

        Args:
            texts: List of input texts
            batch_size: Ignored (for compatibility)

        Returns:
            List of 768-dimensional vectors
        """
        if not texts:
            return []

        embeddings = []
        total_texts = len(texts)

        logger.info(f"Generating {total_texts} mock embeddings (hash-based)")

        for i, text in enumerate(texts, 1):
            if not text or not text.strip():
                logger.warning(f"Skipping empty text at index {i}")
                embeddings.append([0.0] * self.embedding_dim)
                continue

            embedding = self.embed_text(text)
            embeddings.append(embedding)

            if i % 10 == 0:
                logger.info(f"Generated {i}/{total_texts} mock embeddings")

        logger.info(f"Successfully generated {len(embeddings)} mock embeddings")

        return embeddings

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings.

        Returns:
            Embedding dimension (768, same as Gemini)
        """
        return self.embedding_dim
