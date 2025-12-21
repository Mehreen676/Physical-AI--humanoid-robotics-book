"""
Qdrant Vector Store Integration
Handles vector embeddings storage and semantic similarity search.
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Dict, Optional, Tuple
import logging
from src.config import get_settings

logger = logging.getLogger(__name__)

# Vector dimensions for TF-IDF embeddings
EMBEDDING_DIMENSION = 300


class QdrantVectorStore:
    """Qdrant vector store client for semantic search."""

    def __init__(self):
        """Initialize Qdrant client with cloud credentials."""
        settings = get_settings()

        try:
            self.client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
                timeout=30,
            )
        except Exception as e:
            logger.error(f"❌ Failed to initialize Qdrant client: {e}")
            raise

        self.collection_name = settings.qdrant_collection_name
        logger.info(f"✅ Qdrant client initialized: {settings.qdrant_url}")

    def create_collection(self, collection_name: Optional[str] = None) -> bool:
        """
        Create a vector collection in Qdrant with HNSW index.

        Args:
            collection_name: Name of collection (uses default if None)

        Returns:
            bool: True if created successfully
        """
        name = collection_name or self.collection_name

        try:
            # Check if collection exists
            try:
                self.client.get_collection(name)
                logger.info(f"ℹ️  Collection '{name}' already exists")
                return True
            except Exception:
                # Collection doesn't exist, create it
                pass

            # Create collection with HNSW index
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIMENSION,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(
                f"✅ Created collection '{name}' with {EMBEDDING_DIMENSION}-dim vectors"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Error creating collection: {e}")
            raise

    def store_vector(
        self,
        vector_id: str,
        embedding: List[float],
        metadata: Dict,
        collection_name: Optional[str] = None,
    ) -> bool:
        """
        Store a single vector with metadata.

        Args:
            vector_id: Unique identifier for the vector
            embedding: 300-dim vector from TF-IDF
            metadata: Document metadata (chapter, section, chunk_id, etc.)
            collection_name: Collection name (uses default if None)

        Returns:
            bool: True if stored successfully
        """
        name = collection_name or self.collection_name

        try:
            point = PointStruct(
                id=hash(vector_id) % (2**31),  # Convert string ID to positive int
                vector=embedding,
                payload=metadata,
            )

            self.client.upsert(collection_name=name, points=[point])
            logger.debug(f"✅ Stored vector {vector_id} in '{name}'")
            return True

        except Exception as e:
            logger.error(f"❌ Error storing vector: {e}")
            raise

    def store_vectors_batch(
        self,
        vectors_data: List[Tuple[str, List[float], Dict]],
        collection_name: Optional[str] = None,
    ) -> int:
        """
        Store multiple vectors efficiently in batch.

        Args:
            vectors_data: List of (id, embedding, metadata) tuples
            collection_name: Collection name (uses default if None)

        Returns:
            int: Number of vectors stored
        """
        name = collection_name or self.collection_name

        try:
            points = [
                PointStruct(
                    id=hash(vec_id) % (2**31),
                    vector=embedding,
                    payload=metadata,
                )
                for vec_id, embedding, metadata in vectors_data
            ]

            self.client.upsert(collection_name=name, points=points)
            logger.info(f"✅ Stored {len(points)} vectors in batch to '{name}'")
            return len(points)

        except Exception as e:
            logger.error(f"❌ Error storing vectors in batch: {e}")
            raise

    def query_vectors(self, *args, **kwargs) -> List[Dict]:
        """
        Query for top-k similar vectors (semantic search).
        Supports both 'query_embedding' and 'query_vector' parameter names for compatibility.

        Args:
            query_embedding or query_vector: Query vector (300-dim)
            k: Number of results to return (default 5)
            filters: Optional metadata filters (Qdrant filter format)
            collection_name: Collection name (uses default if None)

        Returns:
            List of dicts with: {id, score, chapter, section, content, ...}
        """
        # Handle both parameter names for compatibility
        query_embedding = None
        k = 5
        filters = None
        collection_name = None

        # Handle positional arguments
        if len(args) > 0:
            query_embedding = args[0]
        if len(args) > 1:
            k = args[1]
        if len(args) > 2:
            filters = args[2]
        if len(args) > 3:
            collection_name = args[3]

        # Override with keyword arguments
        query_embedding = kwargs.get('query_embedding', kwargs.get('query_vector', query_embedding))
        k = kwargs.get('k', k)
        filters = kwargs.get('filters', filters)
        collection_name = kwargs.get('collection_name', collection_name)
        name = collection_name or self.collection_name

        try:
            # Convert filters to Qdrant format if they exist
            qdrant_filter = None
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    filter_conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))

                if filter_conditions:
                    qdrant_filter = Filter(must=filter_conditions)

            results = self.client.search(
                collection_name=name,
                query_vector=query_embedding,
                limit=k,
                query_filter=qdrant_filter,
            )

            scored_results = [
                {
                    "id": result.id,
                    "score": result.score,
                    **result.payload,
                }
                for result in results
            ]

            logger.debug(
                f"✅ Found {len(scored_results)} similar vectors "
                f"(top score: {scored_results[0]['score']:.3f})"
            )
            return scored_results

        except Exception as e:
            logger.error(f"❌ Error querying vectors: {e}")
            raise

    def get_collection_info(
        self, collection_name: Optional[str] = None
    ) -> Dict:
        """
        Get collection statistics.

        Args:
            collection_name: Collection name (uses default if None)

        Returns:
            Dict with collection info (point count, vector size, etc.)
        """
        name = collection_name or self.collection_name

        try:
            collection_info = self.client.get_collection(name)
            return {
                "name": name,
                "points_count": collection_info.points_count,
                "vector_size": EMBEDDING_DIMENSION,
                "distance_metric": "cosine",
            }
        except Exception as e:
            logger.error(f"❌ Error getting collection info: {e}")
            raise

    def delete_collection(self, collection_name: Optional[str] = None) -> bool:
        """
        Delete a collection (useful for testing).

        Args:
            collection_name: Collection name (uses default if None)

        Returns:
            bool: True if deleted successfully
        """
        name = collection_name or self.collection_name

        try:
            self.client.delete_collection(name)
            logger.info(f"✅ Deleted collection '{name}'")
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting collection: {e}")
            raise


# Singleton instance
_vector_store_instance: Optional[QdrantVectorStore] = None


def get_vector_store() -> QdrantVectorStore:
    """Get or create Qdrant vector store instance."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = QdrantVectorStore()
    return _vector_store_instance
