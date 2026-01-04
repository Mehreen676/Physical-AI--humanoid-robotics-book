"""
Qdrant client wrapper for semantic search.
"""

import time
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import ScoredPoint


class QdrantRetriever:
    """
    Wrapper for Qdrant semantic search operations.

    Handles connection, retry logic, and result formatting.
    """

    def __init__(
        self,
        url: str,
        api_key: str,
        collection_name: str,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize Qdrant retriever.

        Args:
            url: Qdrant instance URL
            api_key: Qdrant API key
            collection_name: Name of the collection to search
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.url = url
        self.api_key = api_key
        self.collection_name = collection_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Initialize client
        self.client = QdrantClient(
            url=self.url,
            api_key=self.api_key,
            timeout=10.0
        )

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        score_threshold: float = 0.7
    ) -> List[ScoredPoint]:
        """
        Perform semantic search with retry logic.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            score_threshold: Minimum similarity score threshold

        Returns:
            List of ScoredPoint objects from Qdrant

        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    limit=top_k,
                    score_threshold=score_threshold,
                    with_payload=True,
                    with_vectors=False  # Don't return vectors to reduce payload
                )
                return results

            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = self.retry_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
                else:
                    # Final attempt failed
                    raise Exception(
                        f"Qdrant search failed after {self.max_retries} attempts: {str(e)}"
                    ) from e

        # Should not reach here, but for type safety
        raise last_exception

    def health_check(self) -> bool:
        """
        Check if Qdrant connection is healthy.

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            collections = self.client.get_collections()
            return True
        except Exception:
            return False

    def get_collection_info(self) -> Dict:
        """
        Get information about the collection.

        Returns:
            Dictionary with collection metadata

        Raises:
            Exception: If collection does not exist or fetch fails
        """
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "status": info.status
            }
        except Exception as e:
            raise Exception(f"Failed to get collection info: {str(e)}") from e
