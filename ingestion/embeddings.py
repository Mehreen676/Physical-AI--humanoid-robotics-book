"""
Google Gemini embedding service for generating text embeddings.

Uses Gemini's free embedding model (embedding-001) to generate 768-dimensional
embeddings for text chunks.
"""

import logging
import time
from typing import List, Optional
import os

import google.generativeai as genai
from google.api_core import retry

logger = logging.getLogger(__name__)


class GeminiEmbeddings:
    """Generates embeddings using Google Gemini API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "models/embedding-001",
        rate_limit_delay: float = 0.1
    ):
        """
        Initialize Gemini embeddings service.

        Args:
            api_key: Gemini API key (if None, reads from GEMINI_API_KEY env var)
            model_name: Gemini embedding model name
            rate_limit_delay: Delay between API calls to avoid rate limits (seconds)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise ValueError(
                "Gemini API key required. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter"
            )

        # Configure Gemini
        genai.configure(api_key=self.api_key)

        self.model_name = model_name
        self.rate_limit_delay = rate_limit_delay

        # Test connection
        try:
            test_result = genai.embed_content(
                model=self.model_name,
                content="test",
                task_type="retrieval_document"
            )
            self.embedding_dim = len(test_result['embedding'])
            logger.info(
                f"Initialized GeminiEmbeddings: model={model_name}, "
                f"dim={self.embedding_dim}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            raise

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Embedding vector as list of floats

        Raises:
            Exception: If embedding generation fails
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        try:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document"
            )

            embedding = result['embedding']

            logger.debug(f"Generated embedding for text (length={len(text)})")

            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts with batching and rate limiting.

        Args:
            texts: List of input texts
            batch_size: Number of texts to embed in one API call

        Returns:
            List of embedding vectors

        Raises:
            Exception: If embedding generation fails
        """
        if not texts:
            return []

        embeddings = []
        total_texts = len(texts)

        logger.info(f"Embedding {total_texts} texts in batches of {batch_size}")

        for i in range(0, total_texts, batch_size):
            batch = texts[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_texts + batch_size - 1) // batch_size

            logger.info(f"Processing batch {batch_num}/{total_batches}")

            try:
                # Gemini API supports batch embedding
                for text in batch:
                    if not text or not text.strip():
                        logger.warning(f"Skipping empty text at index {i + batch.index(text)}")
                        embeddings.append([0.0] * self.embedding_dim)
                        continue

                    embedding = self.embed_text(text)
                    embeddings.append(embedding)

                    # Rate limiting
                    if self.rate_limit_delay > 0:
                        time.sleep(self.rate_limit_delay)

            except Exception as e:
                logger.error(f"Failed to process batch {batch_num}: {e}")
                raise

        logger.info(f"Successfully embedded {len(embeddings)} texts")

        return embeddings

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this model.

        Returns:
            Embedding dimension
        """
        return self.embedding_dim
