"""
Qdrant client wrapper for semantic search.

This wrapper is compatible across qdrant-client versions:
- Older versions: client.search(...)
- Newer versions: client.query_points(...)
"""

import time
from typing import List, Dict, Optional, Any

from qdrant_client import QdrantClient
from qdrant_client.models import ScoredPoint


class QdrantRetriever:
    """
    Wrapper for Qdrant semantic search operations.

    Handles connection, retry logic, and result formatting.
    Compatible with multiple qdrant-client versions.
    """

    def __init__(
        self,
        url: str,
        api_key: Optional[str],
        collection_name: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 10.0,
    ):
        self.url = url
        self.api_key = api_key
        self.collection_name = collection_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # NOTE: If api_key is used with http://, qdrant-client warns about insecure connection.
        # Prefer https:// in production.
        self.client = QdrantClient(
            url=self.url,
            api_key=self.api_key,
            timeout=timeout,
        )

    def _search_impl(
        self,
        query_vector: List[float],
        top_k: int,
        score_threshold: Optional[float],
    ) -> List[ScoredPoint]:
        """
        Internal search implementation compatible across versions.
        """
        # Prefer legacy `search` if available
        if hasattr(self.client, "search"):
            kwargs: Dict[str, Any] = dict(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True,
                with_vectors=False,
            )
            # score_threshold is optional; if None, don't pass it
            if score_threshold is not None:
                kwargs["score_threshold"] = score_threshold

            return self.client.search(**kwargs)  # type: ignore

        # Newer clients use `query_points`
        if hasattr(self.client, "query_points"):
            kwargs = dict(
                collection_name=self.collection_name,
                query=query_vector,      # IMPORTANT: `query` is the vector
                limit=top_k,
                with_payload=True,
                with_vectors=False,
            )
            if score_threshold is not None:
                kwargs["score_threshold"] = score_threshold

            res = self.client.query_points(**kwargs)  # type: ignore
            # Newer API returns an object with `.points`
            points = getattr(res, "points", None)
            if points is None:
                # In some variants it may return dict-like
                points = res.get("points", []) if isinstance(res, dict) else []
            return points  # type: ignore

        raise RuntimeError(
            "Your installed qdrant-client does not support `search` or `query_points`."
        )

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        score_threshold: float = 0.0,
    ) -> List[ScoredPoint]:
        """
        Perform semantic search with retry logic.

        NOTE:
        - I set default score_threshold=0.0 to avoid getting 0 results when embeddings mismatch.
        - If you want strict matching, set it back to 0.7.
        """
        last_exception: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                # If you want to disable threshold completely, set score_threshold=None here:
                # return self._search_impl(query_vector, top_k, None)
                return self._search_impl(query_vector, top_k, score_threshold)

            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                else:
                    raise Exception(
                        f"Qdrant search failed after {self.max_retries} attempts: {str(e)}"
                    ) from e

        raise last_exception  # type: ignore

    def health_check(self) -> bool:
        try:
            _ = self.client.get_collections()
            return True
        except Exception:
            return False

    def get_collection_info(self) -> Dict:
        """Get collection metadata safely across qdrant-client versions."""
        try:
            info = self.client.get_collection(self.collection_name)

            points_count = getattr(info, "points_count", None)
            indexed_vectors_count = getattr(info, "indexed_vectors_count", None)

            vectors_count = getattr(info, "vectors_count", None)
            if vectors_count is None:
                vectors_count = points_count

            status = getattr(info, "status", None)
            status_name = getattr(status, "name", str(status)) if status is not None else None

            distance = None
            try:
                vectors_cfg = info.config.params.vectors
                if isinstance(vectors_cfg, dict):
                    vectors_cfg = next(iter(vectors_cfg.values()))
                if vectors_cfg is not None and getattr(vectors_cfg, "distance", None) is not None:
                    distance = vectors_cfg.distance.name
            except Exception:
                distance = None

            return {
                "collection_name": self.collection_name,
                "distance": distance,
                "points_count": points_count,
                "vectors_count": vectors_count,
                "indexed_vectors_count": indexed_vectors_count,
                "status": status_name,
            }
        except Exception as e:
            raise Exception(f"Failed to get collection info: {str(e)}") from e
