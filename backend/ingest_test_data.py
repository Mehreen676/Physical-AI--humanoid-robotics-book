"""
Test data ingestion script for Qdrant vector database.
Ingests sample book chunks and verifies they can be retrieved.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from services.embeddings import EmbeddingsService
from rag.retrieval import QdrantRetriever, DataIngestionSkill

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample book chunks for testing
SAMPLE_CHUNKS = [
    {
        "text": "Robotics is the field of engineering and science that deals with robots. Robots are programmable machines that can perform tasks autonomously or semi-autonomously.",
        "metadata": {
            "url": "https://example.com/robotics-intro",
            "section": "Introduction to Robotics",
            "chunk_id": "chunk_001",
            "position": 0
        }
    },
    {
        "text": "A humanoid robot is a robot with a human-like appearance and structure. They typically have two arms, two legs, a torso, and a head. Humanoid robots are designed to interact with human environments and tools.",
        "metadata": {
            "url": "https://example.com/humanoid-robots",
            "section": "Humanoid Robots Definition",
            "chunk_id": "chunk_002",
            "position": 1
        }
    },
    {
        "text": "Machine learning is a subset of artificial intelligence that focuses on teaching computers to learn from data. Deep learning uses neural networks with multiple layers to process complex patterns.",
        "metadata": {
            "url": "https://example.com/machine-learning",
            "section": "Machine Learning Basics",
            "chunk_id": "chunk_003",
            "position": 2
        }
    },
    {
        "text": "The Boston Dynamics Atlas is a humanoid robot designed for research and development. It stands 5 feet 9 inches tall and weighs about 330 pounds. Atlas can perform complex movements including running, jumping, and manipulation tasks.",
        "metadata": {
            "url": "https://example.com/atlas-robot",
            "section": "Atlas Robot Overview",
            "chunk_id": "chunk_004",
            "position": 3
        }
    },
    {
        "text": "Neural networks are computing systems inspired by biological neural networks. They consist of interconnected nodes (neurons) that process information. Convolutional neural networks are particularly effective for image recognition tasks.",
        "metadata": {
            "url": "https://example.com/neural-networks",
            "section": "Neural Network Architecture",
            "chunk_id": "chunk_005",
            "position": 4
        }
    },
]


async def ingest_data():
    """Ingest test data into Qdrant and verify retrieval."""
    try:
        logger.info("Initializing services...")

        # Initialize embeddings service
        embeddings_service = EmbeddingsService(
            provider="cohere",
            api_key=settings.embeddings_api_key,
            model=settings.cohere_embedding_model
        )

        # Initialize Qdrant retriever
        retriever = QdrantRetriever(
            qdrant_url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            collection_name=settings.collection_name
        )

        # Create collection (will recreate if exists)
        logger.info(f"Creating/recreating collection: {settings.collection_name}")
        retriever.create_collection(vector_size=384, distance="cosine")

        # Initialize data ingestion skill
        ingestion_skill = DataIngestionSkill(
            retriever=retriever,
            embeddings_service=embeddings_service
        )

        # Ingest sample chunks
        logger.info(f"Ingesting {len(SAMPLE_CHUNKS)} test chunks...")
        ingested_count = await ingestion_skill.ingest_batch(SAMPLE_CHUNKS)
        logger.info(f"Successfully ingested {ingested_count} chunks")

        # Test retrieval with a sample query
        logger.info("\nTesting retrieval...")
        test_query = "Tell me about humanoid robots"
        logger.info(f"Query: {test_query}")

        # Generate embedding for query
        query_embedding = await embeddings_service.embed(test_query)
        logger.info(f"Generated query embedding (dimension: {len(query_embedding)})")

        # Search in Qdrant
        retrieved_chunks = retriever.search(
            query_vector=query_embedding,
            top_k=3,
            threshold=0.5
        )

        logger.info(f"\nRetrieved {len(retrieved_chunks)} chunks:")
        for i, chunk in enumerate(retrieved_chunks, 1):
            logger.info(f"\n  Chunk {i}:")
            logger.info(f"    Text: {chunk['text'][:80]}...")
            logger.info(f"    Section: {chunk['metadata'].get('section')}")
            logger.info(f"    URL: {chunk['metadata'].get('url')}")
            logger.info(f"    Similarity Score: {chunk['metadata'].get('embedding_score'):.4f}")

        # Verify data integrity
        if not retrieved_chunks:
            logger.error("ERROR: No chunks retrieved! Data may not have been stored correctly.")
            return False

        logger.info("\n[SUCCESS] Data ingestion and retrieval working correctly!")
        return True

    except Exception as e:
        logger.error(f"[ERROR] Data ingestion failed: {e}", exc_info=True)
        return False


async def main():
    """Run the data ingestion test."""
    logger.info("=" * 60)
    logger.info("FastAPI RAG Backend - Data Ingestion Test")
    logger.info("=" * 60)
    logger.info(f"Qdrant URL: {settings.qdrant_url}")
    logger.info(f"Collection: {settings.collection_name}")
    logger.info(f"Embeddings Provider: {settings.embeddings_provider}")
    logger.info("=" * 60)

    success = await ingest_data()

    if success:
        logger.info("\n[PASSED] All checks passed!")
        return 0
    else:
        logger.error("\n[FAILED] One or more checks failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
