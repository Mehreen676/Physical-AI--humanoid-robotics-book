"""
Qdrant vector store wrapper.

- Works with newer qdrant-client versions where `client.search()` may not exist.
- Accepts text query, embeds it, then queries Qdrant using `query_points` (preferred).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

from ingestion.embeddings import get_embedder

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    def __init__(
        self,
        qdrant_url: str,
        api_key: str,
        collection_name: str,
        vector_dim: int,
        timeout: int = 60,
    ):
        self.collection_name = collection_name
        self.vector_dim = int(vector_dim)

        # NOTE: Some Qdrant Cloud setups can fail version check; warning is fine.
        self.client = QdrantClient(url=qdrant_url, api_key=api_key, timeout=timeout)

        logger.info(
            "Initialized QdrantVectorStore: collection=%s, dim=%s",
            self.collection_name,
            self.vector_dim,
        )
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Ensure collection exists, create if missing."""
        try:
            existing = self.client.get_collections().collections
        except Exception as e:
            logger.error("Failed to list collections: %s", e)
            raise

        exists = any(c.name == self.collection_name for c in existing)
        if exists:
            logger.info("Collection %s already exists", self.collection_name)
            return

        logger.info("Creating collection %s (dim=%s)", self.collection_name, self.vector_dim)
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=rest.VectorParams(
                size=self.vector_dim,
                distance=rest.Distance.COSINE,
            ),
        )
        logger.info("✅ Created collection %s", self.collection_name)

    def search(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search by TEXT:
        - Embed query_text
        - Query Qdrant using query_points (new API) or fallback to search_points/search (older)
        Returns: list of {id, score, payload}
        """
        embedder = get_embedder()
        query_vector = embedder.embed(query_text)

        if len(query_vector) != self.vector_dim:
            logger.warning(
                "Query vector dim mismatch: got=%s expected=%s",
                len(query_vector),
                self.vector_dim,
            )

        # ✅ Preferred (newer qdrant-client)
        if hasattr(self.client, "query_points"):
            res = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k,
                with_payload=True,
                with_vectors=False,
            )
            points = getattr(res, "points", res)  # some versions return .points
            return [
                {"id": p.id, "score": p.score, "payload": p.payload}
                for p in points
            ]

        # ✅ Fallback: search_points (some versions)
        if hasattr(self.client, "search_points"):
            points = self.client.search_points(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True,
                with_vectors=False,
            )
            return [
                {"id": p.id, "score": p.score, "payload": p.payload}
                for p in points
            ]

        # ✅ Very old fallback: search (rare)
        if hasattr(self.client, "search"):
            points = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True,
                with_vectors=False,
            )
            return [
                {"id": p.id, "score": p.score, "payload": p.payload}
                for p in points
            ]

        raise AttributeError(
            "Your qdrant-client does not support query_points/search_points/search. "
            "Please upgrade: pip install -U qdrant-client"
        )
