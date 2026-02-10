"""
Qdrant Cloud vector store client for managing embeddings.

Handles collection creation, vector insertion, and similarity search with Qdrant.
Uses stable UUID-based IDs for safe re-ingestion without duplicates.
"""

import logging
import hashlib
import uuid
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    """Qdrant vector store for book embeddings."""

    def __init__(
        self,
        url: str,
        api_key: str,
        collection_name: str,
        embedding_dim: int = 768,
    ):
        self.url = url
        self.api_key = api_key
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim

        self.client = QdrantClient(
            url=url,
            api_key=api_key,
            timeout=30,
        )

        logger.info(
            f"Initialized QdrantVectorStore: collection={collection_name}, dim={embedding_dim}"
        )

    def create_collection(self, recreate: bool = False) -> None:
        """Create Qdrant collection with cosine similarity."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]

            if self.collection_name in collection_names:
                if recreate:
                    logger.warning(f"Deleting existing collection: {self.collection_name}")
                    self.client.delete_collection(self.collection_name)
                else:
                    logger.info(f"Collection {self.collection_name} already exists")
                    return

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE,
                ),
            )

            logger.info(f"Created collection: {self.collection_name}")

        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise

    def generate_point_id(self, metadata: Dict[str, Any]) -> str:
        """Generate stable UUID from metadata for idempotent insertion."""
        source = metadata.get("source_file", "unknown")
        chunk_idx = metadata.get("chunk_index", 0)

        hash_input = f"{source}::{chunk_idx}"
        hash_digest = hashlib.md5(hash_input.encode()).hexdigest()
        point_id = str(uuid.UUID(hash_digest))
        return point_id

    def insert_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        batch_size: int = 100,
    ) -> int:
        """Insert chunks with embeddings into Qdrant."""
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Chunks ({len(chunks)}) and embeddings ({len(embeddings)}) length mismatch"
            )

        total_chunks = len(chunks)
        logger.info(f"Inserting {total_chunks} chunks in batches of {batch_size}")

        inserted_count = 0

        for i in range(0, total_chunks, batch_size):
            batch_chunks = chunks[i : i + batch_size]
            batch_embeddings = embeddings[i : i + batch_size]

            batch_num = (i // batch_size) + 1
            total_batches = (total_chunks + batch_size - 1) // batch_size
            logger.info(f"Inserting batch {batch_num}/{total_batches}")

            try:
                points: List[PointStruct] = []
                for chunk, embedding in zip(batch_chunks, batch_embeddings):
                    point_id = self.generate_point_id(chunk["metadata"])
                    point = PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "text": chunk["text"],
                            **chunk["metadata"],
                        },
                    )
                    points.append(point)

                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points,
                    wait=True,
                )

                inserted_count += len(points)
                logger.debug(f"Inserted batch {batch_num}: {len(points)} points")

            except Exception as e:
                logger.error(f"Failed to insert batch {batch_num}: {e}")
                raise

        logger.info(f"Successfully inserted {inserted_count} chunks")
        return inserted_count

    def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: Optional[float] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks."""
        try:
            query_filter = None
            if filter_dict:
                conditions = [
                    FieldCondition(key=k, match=MatchValue(value=v))
                    for k, v in filter_dict.items()
                ]
                query_filter = Filter(must=conditions)

            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter,
                with_payload=True,
                with_vectors=False,
            )

            formatted_results = []
            for r in results:
                formatted_results.append(
                    {
                        "id": r.id,
                        "score": r.score,
                        "text": (r.payload or {}).get("text", ""),
                        "metadata": {k: v for k, v in (r.payload or {}).items() if k != "text"},
                    }
                )

            logger.info(f"Found {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get collection information.

        NOTE: Different qdrant-client versions expose different fields.
        We read fields safely via getattr to avoid crashes.
        """
        try:
            info = self.client.get_collection(self.collection_name)

            points_count = getattr(info, "points_count", None)
            indexed_vectors_count = getattr(info, "indexed_vectors_count", None)

            # Try to detect distance config safely
            distance = None
            try:
                vectors_cfg = info.config.params.vectors  # can be VectorParams or dict
                if isinstance(vectors_cfg, dict):
                    vectors_cfg = next(iter(vectors_cfg.values()))
                if vectors_cfg is not None and getattr(vectors_cfg, "distance", None) is not None:
                    distance = vectors_cfg.distance.name
            except Exception:
                distance = None

            status = getattr(info, "status", None)
            status_name = getattr(status, "name", str(status)) if status is not None else None

            # Some versions don't have vectors_count; for single-vector collections it's basically points_count
            vectors_count = getattr(info, "vectors_count", None)
            if vectors_count is None:
                vectors_count = points_count

            return {
                "collection_name": self.collection_name,
                "distance": distance,
                "points_count": points_count,
                "vectors_count": vectors_count,
                "indexed_vectors_count": indexed_vectors_count,
                "status": status_name,
            }

        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            raise

    def count_points(self) -> int:
        """Count total points in collection."""
        try:
            result = self.client.count(collection_name=self.collection_name, exact=True)
            return result.count
        except Exception as e:
            logger.error(f"Failed to count points: {e}")
            raise
