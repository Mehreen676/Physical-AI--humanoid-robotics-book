#!/usr/bin/env python3
"""
Test script for similarity search in Qdrant.

Validates that embeddings were stored correctly and can be retrieved via
semantic search.
"""

import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from embeddings import GeminiEmbeddings
from mock_embeddings import MockEmbeddings  # TODO: Remove after Gemini quota reset
from vector_store import QdrantVectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


def load_config() -> dict:
    """Load configuration from environment variables."""
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)

    config = {
        'qdrant_api_key': os.getenv('QDRANT_API_KEY'),
        'qdrant_url': os.getenv('QDRANT_URL'),
        'collection_name': os.getenv('COLLECTION_NAME'),
        'gemini_api_key': os.getenv('GEMINI_API_KEY')
    }

    return config


def test_search(query: str, top_k: int = 5):
    """
    Test similarity search with a query.

    Args:
        query: Search query
        top_k: Number of results to return
    """
    logger.info("=" * 60)
    logger.info("Testing Similarity Search")
    logger.info("=" * 60)

    try:
        # Load config
        config = load_config()

        # Initialize embeddings service
        logger.info("\nInitializing mock embeddings...")
        # TODO: Replace MockEmbeddings with GeminiEmbeddings after quota reset
        # embedder = GeminiEmbeddings(api_key=config['gemini_api_key'])
        embedder = MockEmbeddings()

        # Initialize vector store
        logger.info("Connecting to Qdrant...")
        vector_store = QdrantVectorStore(
            url=config['qdrant_url'],
            api_key=config['qdrant_api_key'],
            collection_name=config['collection_name'],
            embedding_dim=embedder.get_embedding_dimension()
        )

        # Get collection info
        # Skipping get_collection_info() due to Qdrant client/server version mismatch
        logger.info(f"\nCollection: {config['collection_name']}")
        # collection_info = vector_store.get_collection_info()
        # logger.info(f"Total points: {collection_info.get('points_count', 0)}")
        # logger.info(f"Status: {collection_info.get('status', 'unknown')}")

        # Generate query embedding
        logger.info(f"\nQuery: {query}")
        logger.info("Generating query embedding...")
        query_embedding = embedder.embed_text(query)

        # Search
        logger.info(f"Searching for top {top_k} results...")
        results = vector_store.search(
            query_vector=query_embedding,
            limit=top_k,
            score_threshold=0.3  # Minimum cosine similarity
        )

        # Display results
        logger.info("\n" + "=" * 60)
        logger.info(f"Search Results ({len(results)} found)")
        logger.info("=" * 60)

        for i, result in enumerate(results, 1):
            logger.info(f"\n--- Result {i} ---")
            logger.info(f"Score: {result['score']:.4f}")
            logger.info(f"Chapter: {result['metadata'].get('chapter', 'N/A')}")
            logger.info(f"Section: {result['metadata'].get('section', 'N/A')}")
            logger.info(f"Source: {result['metadata'].get('source_file', 'N/A')}")
            logger.info(f"Chunk: {result['metadata'].get('chunk_index', 0) + 1}/{result['metadata'].get('total_chunks', 0)}")

            # Display text snippet
            text = result['text']
            snippet = text[:200] + "..." if len(text) > 200 else text
            logger.info(f"\nText snippet:\n{snippet}\n")

        logger.info("=" * 60)

        return results

    except Exception as e:
        logger.error(f"Search test failed: {e}", exc_info=True)
        raise


def main():
    """Main test function with sample queries."""
    logger.info("\n" + "=" * 60)
    logger.info("Qdrant Similarity Search Test")
    logger.info("=" * 60)

    # Test queries
    test_queries = [
        "What is ROS 2?",
        "How do humanoid robots work?",
        "Explain vision-language-action systems",
        "What is Gazebo simulation?",
        "How to control robotic hardware?"
    ]

    logger.info("\nRunning sample queries...")

    for i, query in enumerate(test_queries, 1):
        logger.info(f"\n\n{'=' * 60}")
        logger.info(f"Query {i}/{len(test_queries)}")
        logger.info(f"{'=' * 60}")

        try:
            test_search(query, top_k=3)
        except Exception as e:
            logger.error(f"Query failed: {e}")
            continue

        # Add separator
        if i < len(test_queries):
            logger.info("\n" + "-" * 60 + "\n")

    logger.info("\n" + "=" * 60)
    logger.info("Test Complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Test similarity search in Qdrant"
    )
    parser.add_argument(
        '--query',
        type=str,
        help='Custom search query'
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=5,
        help='Number of results to return (default: 5)'
    )
    parser.add_argument(
        '--run-samples',
        action='store_true',
        help='Run sample queries instead of custom query'
    )

    args = parser.parse_args()

    try:
        if args.run_samples:
            main()
        elif args.query:
            test_search(args.query, args.top_k)
        else:
            # Default: run samples
            main()

    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)
