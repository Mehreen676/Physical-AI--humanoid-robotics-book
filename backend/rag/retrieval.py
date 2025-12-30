"""
Vector retrieval from Qdrant vector database.

Provides QdrantRetriever for semantic search and VectorSearchSkill for RAG pipeline.
"""

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import logging
from typing import List, Dict, Any, Optional
from config import settings
from agent.skills import Skill
from services.embeddings import EmbeddingsService

logger = logging.getLogger(__name__)


class QdrantRetriever:
    """Client for querying Qdrant vector database."""

    def __init__(self, qdrant_url: str, api_key: str, collection_name: str = None):
        """
        Initialize Qdrant retriever.

        Args:
            qdrant_url: Qdrant cluster URL
            api_key: Qdrant API key
            collection_name: Name of the collection
        """
        self.qdrant_url = qdrant_url
        self.api_key = api_key
        self.collection_name = collection_name or settings.collection_name

        try:
            self.client = QdrantClient(
                url=qdrant_url,
                api_key=api_key,
                timeout=30.0
            )
            logger.info(f"Connected to Qdrant at {qdrant_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise

    async def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks in Qdrant.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            threshold: Minimum similarity score

        Returns:
            List of retrieved chunks with metadata
        """
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=threshold
            )

            chunks = []
            for result in results:
                chunk = {
                    "text": result.payload.get("text", ""),
                    "metadata": {
                        "url": result.payload.get("url", ""),
                        "section": result.payload.get("section", ""),
                        "chunk_id": result.payload.get("chunk_id", ""),
                        "position": result.payload.get("position", 0),
                        "embedding_score": result.score
                    }
                }
                chunks.append(chunk)

            logger.info(f"Retrieved {len(chunks)} chunks from Qdrant (threshold: {threshold})")
            return chunks

        except Exception as e:
            logger.error(f"Failed to search Qdrant: {e}")
            raise

    async def health_check(self) -> Dict[str, str]:
        """
        Check Qdrant connection health.

        Returns:
            Dictionary with 'status' key
        """
        try:
            health = self.client.get_collection_info(self.collection_name)
            logger.info("Qdrant health check passed")
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return {"status": "error", "message": str(e)}

    def create_collection(
        self,
        vector_size: int = 1280,
        distance: str = "cosine"
    ) -> bool:
        """
        Create a new Qdrant collection.

        Args:
            vector_size: Dimension of embedding vectors
            distance: Distance metric ('cosine', 'euclidean', 'manhattan')

        Returns:
            True if collection was created or already exists
        """
        try:
            from qdrant_client.models import VectorParams, Distance

            distance_map = {
                "cosine": Distance.COSINE,
                "euclidean": Distance.EUCLID,
                "manhattan": Distance.MANHATTAN,
            }

            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance_map.get(distance, Distance.COSINE)
                ),
            )
            logger.info(f"Created collection {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            return False

    def upsert(
        self,
        point_id: int,
        vector: List[float],
        payload: Dict[str, Any]
    ) -> bool:
        """
        Upsert a single point to Qdrant collection.

        Args:
            point_id: Unique ID for the point
            vector: Embedding vector
            payload: Metadata dictionary (text, url, section, etc.)

        Returns:
            True if successful
        """
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=[PointStruct(id=point_id, vector=vector, payload=payload)]
            )
            logger.debug(f"Upserted point {point_id} to {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to upsert point {point_id}: {e}")
            return False

    def upsert_batch(
        self,
        points: List[Dict[str, Any]]
    ) -> int:
        """
        Upsert multiple points to Qdrant collection.

        Args:
            points: List of dicts with 'id', 'vector', 'payload' keys

        Returns:
            Number of successfully upserted points
        """
        try:
            qdrant_points = [
                PointStruct(
                    id=p.get("id", i),
                    vector=p.get("vector", []),
                    payload=p.get("payload", {})
                )
                for i, p in enumerate(points)
            ]

            self.client.upsert(
                collection_name=self.collection_name,
                points=qdrant_points
            )
            logger.info(f"Upserted {len(qdrant_points)} points to {self.collection_name}")
            return len(qdrant_points)
        except Exception as e:
            logger.error(f"Failed to upsert batch: {e}")
            return 0


class VectorSearchSkill(Skill):
    """Skill for retrieving relevant chunks from vector database."""

    def __init__(
        self,
        retriever: QdrantRetriever,
        embeddings_service: EmbeddingsService,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ):
        """
        Initialize VectorSearchSkill.

        Args:
            retriever: QdrantRetriever instance
            embeddings_service: EmbeddingsService instance
            top_k: Number of chunks to retrieve
            similarity_threshold: Minimum similarity score
        """
        super().__init__("VectorSearchSkill")
        self.retriever = retriever
        self.embeddings_service = embeddings_service
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

    async def execute(
        self,
        query_text: str,
        retrieval_mode: str = "normal",
        top_k: Optional[int] = None,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for a query.

        Args:
            query_text: User's question/query
            retrieval_mode: 'normal' or 'selected-text' (for filtering)
            top_k: Override default top_k
            threshold: Override default similarity threshold

        Returns:
            List of retrieved chunks with metadata
        """
        try:
            # Use provided values or defaults
            top_k = top_k or self.top_k
            threshold = threshold if threshold is not None else self.similarity_threshold

            # Generate embedding for query
            logger.info(f"Embedding query: {query_text[:100]}...")
            query_embedding = await self.embeddings_service.embed(query_text)

            # Search in Qdrant
            logger.info(f"Searching Qdrant for {top_k} chunks with threshold {threshold}")
            chunks = await self.retriever.search(
                query_vector=query_embedding,
                top_k=top_k,
                threshold=threshold
            )

            logger.info(f"Retrieved {len(chunks)} chunks")
            return chunks

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise


class DataIngestionSkill(Skill):
    """Skill for ingesting and storing data in Qdrant vector database."""

    def __init__(
        self,
        retriever: QdrantRetriever,
        embeddings_service: EmbeddingsService
    ):
        """
        Initialize DataIngestionSkill.

        Args:
            retriever: QdrantRetriever instance
            embeddings_service: EmbeddingsService instance
        """
        super().__init__("DataIngestionSkill")
        self.retriever = retriever
        self.embeddings_service = embeddings_service
        self.point_id_counter = 0

    async def ingest_chunk(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Ingest a single text chunk with metadata.

        Args:
            text: Text content to embed and store
            metadata: Metadata dict (url, section, position, etc.)

        Returns:
            True if successful
        """
        try:
            # Generate embedding
            embedding = await self.embeddings_service.embed(text)

            # Prepare payload
            payload = {
                "text": text,
                **metadata  # Include all metadata
            }

            # Upsert to Qdrant
            self.point_id_counter += 1
            success = self.retriever.upsert(
                point_id=self.point_id_counter,
                vector=embedding,
                payload=payload
            )

            if success:
                logger.info(f"Ingested chunk {self.point_id_counter}: {text[:50]}...")
            else:
                logger.error(f"Failed to ingest chunk: {text[:50]}...")

            return success

        except Exception as e:
            logger.error(f"Failed to ingest chunk: {e}")
            return False

    async def ingest_batch(
        self,
        chunks: List[Dict[str, Any]]
    ) -> int:
        """
        Ingest multiple text chunks with metadata.

        Args:
            chunks: List of dicts with 'text' and 'metadata' keys

        Returns:
            Number of successfully ingested chunks
        """
        try:
            # Generate embeddings for all texts
            texts = [c.get("text", "") for c in chunks]
            embeddings = await self.embeddings_service.embed_batch(texts)

            # Prepare points for Qdrant
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                self.point_id_counter += 1
                points.append({
                    "id": self.point_id_counter,
                    "vector": embedding,
                    "payload": {
                        "text": chunk.get("text", ""),
                        **(chunk.get("metadata", {}))
                    }
                })

            # Upsert batch to Qdrant
            count = self.retriever.upsert_batch(points)
            logger.info(f"Ingested {count} chunks from batch")
            return count

        except Exception as e:
            logger.error(f"Failed to ingest batch: {e}")
            return 0
