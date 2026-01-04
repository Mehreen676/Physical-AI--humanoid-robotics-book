"""
Qdrant Cloud vector store client for managing embeddings.

Handles collection creation, vector insertion, and similarity search with Qdrant Cloud.
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
    MatchValue
)

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    """Qdrant Cloud vector store for book embeddings."""

    def __init__(
        self,
        url: str,
        api_key: str,
        collection_name: str,
        embedding_dim: int = 768
    ):
        """
        Initialize Qdrant vector store.

        Args:
            url: Qdrant Cloud URL
            api_key: Qdrant API key
            collection_name: Name of the collection
            embedding_dim: Dimension of embedding vectors
        """
        self.url = url
        self.api_key = api_key
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim

        # Initialize client
        self.client = QdrantClient(
            url=url,
            api_key=api_key,
            timeout=30
        )

        logger.info(
            f"Initialized QdrantVectorStore: collection={collection_name}, "
            f"dim={embedding_dim}"
        )

    def create_collection(self, recreate: bool = False) -> None:
        """
        Create Qdrant collection with cosine similarity.

        Args:
            recreate: If True, delete existing collection and recreate

        Raises:
            Exception: If collection creation fails
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]

            if self.collection_name in collection_names:
                if recreate:
                    logger.warning(f"Deleting existing collection: {self.collection_name}")
                    self.client.delete_collection(self.collection_name)
                else:
                    logger.info(f"Collection {self.collection_name} already exists")
                    return

            # Create collection with cosine similarity
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )

            logger.info(f"Created collection: {self.collection_name}")

        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise

    def generate_point_id(self, metadata: Dict[str, Any]) -> str:
        """
        Generate stable UUID from metadata for idempotent insertion.

        Args:
            metadata: Chunk metadata containing source_file and chunk_index

        Returns:
            UUID string
        """
        # Create deterministic ID from source file and chunk index
        source = metadata.get("source_file", "unknown")
        chunk_idx = metadata.get("chunk_index", 0)

        # Hash to UUID
        hash_input = f"{source}::{chunk_idx}"
        hash_digest = hashlib.md5(hash_input.encode()).hexdigest()
        point_id = str(uuid.UUID(hash_digest))

        return point_id

    def insert_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        batch_size: int = 100
    ) -> int:
        """
        Insert chunks with embeddings into Qdrant.

        Args:
            chunks: List of chunk dicts with 'text' and 'metadata'
            embeddings: List of embedding vectors
            batch_size: Number of points to insert per batch

        Returns:
            Number of points inserted

        Raises:
            ValueError: If chunks and embeddings length mismatch
            Exception: If insertion fails
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Chunks ({len(chunks)}) and embeddings ({len(embeddings)}) "
                f"length mismatch"
            )

        total_chunks = len(chunks)
        logger.info(f"Inserting {total_chunks} chunks in batches of {batch_size}")

        inserted_count = 0

        for i in range(0, total_chunks, batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size]

            batch_num = (i // batch_size) + 1
            total_batches = (total_chunks + batch_size - 1) // batch_size

            logger.info(f"Inserting batch {batch_num}/{total_batches}")

            try:
                points = []

                for chunk, embedding in zip(batch_chunks, batch_embeddings):
                    # Generate stable ID
                    point_id = self.generate_point_id(chunk["metadata"])

                    # Create point
                    point = PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "text": chunk["text"],
                            **chunk["metadata"]
                        }
                    )

                    points.append(point)

                # Upsert batch (insert or update if exists)
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
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
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks.

        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score (0-1 for cosine)
            filter_dict: Optional metadata filters

        Returns:
            List of search results with 'text', 'metadata', and 'score'
        """
        try:
            # Build filter
            query_filter = None
            if filter_dict:
                conditions = []
                for key, value in filter_dict.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                query_filter = Filter(must=conditions)

            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "score": result.score,
                    "text": result.payload.get("text", ""),
                    "metadata": {
                        k: v for k, v in result.payload.items()
                        if k != "text"
                    }
                })

            logger.info(f"Found {len(formatted_results)} results")

            return formatted_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get collection information.

        Returns:
            Dict with collection stats
        """
        try:
            info = self.client.get_collection(self.collection_name)

            return {
                "name": info.config.params.vectors.distance.name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "status": info.status.name
            }

        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            raise

    def count_points(self) -> int:
        """
        Count total points in collection.

        Returns:
            Number of points
        """
        try:
            result = self.client.count(collection_name=self.collection_name)
            return result.count

        except Exception as e:
            logger.error(f"Failed to count points: {e}")
            raise
