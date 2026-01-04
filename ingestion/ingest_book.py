#!/usr/bin/env python3
"""
Main ingestion script for book content to Qdrant.

Loads Docusaurus markdown files, chunks text, generates Gemini embeddings,
and stores vectors in Qdrant Cloud with metadata.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from chunker import TextChunker
from embeddings import GeminiEmbeddings
from mock_embeddings import MockEmbeddings  # TODO: Remove after Gemini quota reset
from vector_store import QdrantVectorStore
from markdown_processor import MarkdownProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ingestion.log')
    ]
)

logger = logging.getLogger(__name__)


def load_config() -> dict:
    """
    Load configuration from environment variables.

    Returns:
        Config dict

    Raises:
        ValueError: If required environment variables are missing
    """
    # Load .env file if it exists
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded environment from {env_path}")
    else:
        logger.warning("No .env file found, using system environment variables")

    # Required variables
    required_vars = [
        'QDRANT_API_KEY',
        'QDRANT_URL',
        'COLLECTION_NAME',
        'GEMINI_API_KEY'
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            f"Please set them in .env file or environment"
        )

    config = {
        'qdrant_api_key': os.getenv('QDRANT_API_KEY'),
        'qdrant_url': os.getenv('QDRANT_URL'),
        'collection_name': os.getenv('COLLECTION_NAME'),
        'gemini_api_key': os.getenv('GEMINI_API_KEY'),
        'book_title': os.getenv('BOOK_TITLE', 'Physical AI & Humanoid Robotics Textbook'),
        'docs_path': os.getenv('DOCS_PATH', 'front-end/docs'),
        'chunk_size': int(os.getenv('CHUNK_SIZE', '400')),
        'chunk_overlap': int(os.getenv('CHUNK_OVERLAP', '100')),
        'rate_limit_delay': float(os.getenv('RATE_LIMIT_DELAY', '0.1'))
    }

    # Mask sensitive values in logs
    logger.info("Configuration loaded:")
    logger.info(f"  QDRANT_URL: {config['qdrant_url']}")
    logger.info(f"  COLLECTION_NAME: {config['collection_name']}")
    logger.info(f"  BOOK_TITLE: {config['book_title']}")
    logger.info(f"  DOCS_PATH: {config['docs_path']}")
    logger.info(f"  CHUNK_SIZE: {config['chunk_size']}")
    logger.info(f"  CHUNK_OVERLAP: {config['chunk_overlap']}")
    logger.info(f"  RATE_LIMIT_DELAY: {config['rate_limit_delay']}s")
    logger.info("  QDRANT_API_KEY: [REDACTED]")
    logger.info("  GEMINI_API_KEY: [REDACTED]")

    return config


def main(recreate_collection: bool = False):
    """
    Main ingestion pipeline.

    Args:
        recreate_collection: If True, delete and recreate Qdrant collection

    Raises:
        Exception: If ingestion fails
    """
    logger.info("=" * 60)
    logger.info("Starting Book Content Ingestion Pipeline")
    logger.info("=" * 60)

    try:
        # Load configuration
        logger.info("\n[1/6] Loading configuration...")
        config = load_config()

        # Initialize markdown processor
        logger.info("\n[2/6] Processing markdown files...")
        processor = MarkdownProcessor(
            docs_path=config['docs_path'],
            book_title=config['book_title']
        )
        documents = processor.process_all_files()

        if not documents:
            raise ValueError("No documents found to process")

        logger.info(f"Processed {len(documents)} documents")

        # Initialize chunker
        logger.info("\n[3/6] Chunking documents...")
        chunker = TextChunker(
            chunk_size=config['chunk_size'],
            chunk_overlap=config['chunk_overlap']
        )

        all_chunks = []
        for doc in documents:
            chunks = chunker.chunk_text(
                text=doc['content'],
                metadata=doc['metadata']
            )
            all_chunks.extend(chunks)

        logger.info(f"Created {len(all_chunks)} chunks from {len(documents)} documents")

        # Initialize embeddings service
        logger.info("\n[4/6] Generating embeddings...")

        # TODO: Replace MockEmbeddings with GeminiEmbeddings after quota reset
        # Using mock embeddings due to Gemini free-tier daily quota exhaustion
        # embedder = GeminiEmbeddings(
        #     api_key=config['gemini_api_key'],
        #     rate_limit_delay=config['rate_limit_delay']
        # )
        embedder = MockEmbeddings()

        # Extract texts for embedding
        chunk_texts = [chunk['text'] for chunk in all_chunks]
        embeddings = embedder.embed_batch(chunk_texts, batch_size=50)

        logger.info(f"Generated {len(embeddings)} embeddings")

        # Initialize vector store
        logger.info("\n[5/6] Initializing Qdrant vector store...")
        vector_store = QdrantVectorStore(
            url=config['qdrant_url'],
            api_key=config['qdrant_api_key'],
            collection_name=config['collection_name'],
            embedding_dim=embedder.get_embedding_dimension()
        )

        # Create collection
        vector_store.create_collection(recreate=recreate_collection)

        # Insert chunks
        logger.info("\n[6/6] Inserting chunks into Qdrant...")
        inserted_count = vector_store.insert_chunks(
            chunks=all_chunks,
            embeddings=embeddings,
            batch_size=100
        )

        # Get collection info
        collection_info = vector_store.get_collection_info()

        logger.info("\n" + "=" * 60)
        logger.info("Ingestion Complete!")
        logger.info("=" * 60)
        logger.info(f"Documents processed: {len(documents)}")
        logger.info(f"Chunks created: {len(all_chunks)}")
        logger.info(f"Embeddings generated: {len(embeddings)}")
        logger.info(f"Points inserted: {inserted_count}")
        logger.info(f"Collection status: {collection_info.get('status', 'unknown')}")
        logger.info(f"Total points in collection: {collection_info.get('points_count', 0)}")
        logger.info("=" * 60)

        logger.info("\nNext steps:")
        logger.info("1. Check Qdrant Cloud dashboard to verify vectors")
        logger.info("2. Run test_search.py to test similarity search")
        logger.info("3. Integrate with OpenAI Agents SDK for RAG chatbot")

    except Exception as e:
        logger.error(f"\n\nIngestion failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Ingest Docusaurus book content into Qdrant"
    )
    parser.add_argument(
        '--recreate',
        action='store_true',
        help='Delete and recreate Qdrant collection'
    )

    args = parser.parse_args()

    try:
        main(recreate_collection=args.recreate)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)
