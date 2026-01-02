#!/usr/bin/env python3
"""
Ingest book content from markdown files into Qdrant vector database.

Reads all markdown files from front-end/docs, chunks them,
generates embeddings, and indexes into Qdrant.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Tuple
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
import cohere
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DOCS_PATH = Path(__file__).parent.parent / "front-end" / "docs"
CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks
EMBEDDING_MODEL = "embed-english-light-v3.0"


def read_markdown_files() -> List[Tuple[str, str]]:
    """Read all markdown files from docs directory."""
    logger.info(f"Reading markdown files from {DOCS_PATH}")

    files = []
    if not DOCS_PATH.exists():
        logger.error(f"Docs directory not found: {DOCS_PATH}")
        return files

    # Find all .md files recursively
    for md_file in DOCS_PATH.rglob("*.md"):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Get relative path for file name
                rel_path = md_file.relative_to(DOCS_PATH)
                files.append((str(rel_path), content))
                logger.info(f"✓ Read: {rel_path}")
        except Exception as e:
            logger.error(f"✗ Failed to read {md_file}: {e}")

    logger.info(f"Total files read: {len(files)}")
    return files


def chunk_text(text: str, file_name: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[Dict]:
    """Split text into chunks with overlap."""
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # Create chunk metadata
        chunk_data = {
            "text": chunk.strip(),
            "source_file": file_name,
            "start_pos": start,
            "end_pos": min(end, len(text))
        }

        if chunk_data["text"]:  # Only add non-empty chunks
            chunks.append(chunk_data)

        start += chunk_size - overlap

    return chunks


def create_qdrant_collection(client: QdrantClient, collection_name: str):
    """Create collection in Qdrant if it doesn't exist."""
    try:
        # Check if collection exists
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if collection_name in collection_names:
            logger.info(f"✓ Collection '{collection_name}' already exists")
            return

        # Create collection
        logger.info(f"Creating collection '{collection_name}'...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=384,  # Cohere embed-english-light-v3.0 is 384-dimensional
                distance=Distance.COSINE
            )
        )
        logger.info(f"✓ Collection '{collection_name}' created successfully")

    except Exception as e:
        logger.error(f"Failed to create collection: {e}")
        raise


def generate_embeddings(texts: List[str], client: cohere.ClientV2, batch_size: int = 5) -> List[List[float]]:
    """Generate embeddings using Cohere with retry logic and batching."""
    if not texts:
        return []

    import time
    from cohere.errors import TooManyRequestsError

    all_embeddings = []
    total_texts = len(texts)

    try:
        logger.info(f"Generating embeddings for {total_texts} chunks (batch size: {batch_size})...")

        # Process in batches with retry logic
        for batch_start in range(0, total_texts, batch_size):
            batch_end = min(batch_start + batch_size, total_texts)
            batch = texts[batch_start:batch_end]
            batch_num = (batch_start // batch_size) + 1
            total_batches = (total_texts + batch_size - 1) // batch_size

            retry_count = 0
            max_retries = 5
            wait_time = 2

            while retry_count < max_retries:
                try:
                    logger.info(f"  Batch {batch_num}/{total_batches}...")
                    response = client.embed(
                        model=EMBEDDING_MODEL,
                        input_type="search_document",
                        texts=batch
                    )
                    all_embeddings.extend(response.embeddings)
                    logger.info(f"  ✓ Batch {batch_num}/{total_batches} done ({len(all_embeddings)}/{total_texts})")
                    break

                except TooManyRequestsError as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        logger.warning(f"  ⚠ Rate limited. Waiting {wait_time}s before retry {retry_count}/{max_retries}...")
                        time.sleep(wait_time)
                        wait_time *= 2  # Exponential backoff
                    else:
                        raise

            # Small delay between batches
            if batch_end < total_texts:
                time.sleep(1)

        logger.info(f"✓ Generated {len(all_embeddings)} embeddings")
        return all_embeddings

    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        raise


def ingest_into_qdrant(
    client: QdrantClient,
    collection_name: str,
    chunks: List[Dict],
    embeddings: List[List[float]]
) -> int:
    """Ingest chunks and embeddings into Qdrant."""
    if not chunks or not embeddings:
        logger.warning("No chunks or embeddings to ingest")
        return 0

    try:
        logger.info(f"Ingesting {len(chunks)} chunks into Qdrant...")

        points = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point = PointStruct(
                id=idx,
                vector=embedding,
                payload={
                    "text": chunk["text"],
                    "source_file": chunk["source_file"],
                    "start_pos": chunk["start_pos"],
                    "end_pos": chunk["end_pos"],
                    "timestamp": datetime.now().isoformat()
                }
            )
            points.append(point)

        # Upsert points into collection
        client.upsert(
            collection_name=collection_name,
            points=points
        )

        logger.info(f"✓ Successfully ingested {len(points)} chunks")
        return len(points)

    except Exception as e:
        logger.error(f"Failed to ingest into Qdrant: {e}")
        raise


def main():
    """Main ingestion pipeline."""
    logger.info("="*70)
    logger.info("BOOK CONTENT INGESTION - START")
    logger.info("="*70)

    try:
        # Step 1: Initialize clients
        logger.info("\n[STEP 1] Initializing clients...")

        # Qdrant client
        qdrant_url = settings.qdrant_url
        qdrant_api_key = settings.qdrant_api_key
        collection_name = settings.collection_name

        qdrant_client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key
        )
        logger.info(f"✓ Connected to Qdrant: {qdrant_url}")

        # Cohere client
        cohere_client = cohere.ClientV2(api_key=settings.embeddings_api_key)
        logger.info(f"✓ Connected to Cohere")

        # Step 2: Create collection
        logger.info("\n[STEP 2] Creating Qdrant collection...")
        create_qdrant_collection(qdrant_client, collection_name)

        # Step 3: Read markdown files
        logger.info("\n[STEP 3] Reading markdown files...")
        files = read_markdown_files()
        if not files:
            logger.error("No markdown files found!")
            return False

        # Step 4: Chunk all content
        logger.info("\n[STEP 4] Chunking content...")
        all_chunks = []
        all_texts = []

        for file_name, content in files:
            chunks = chunk_text(content, file_name)
            all_chunks.extend(chunks)
            all_texts.extend([c["text"] for c in chunks])

        logger.info(f"✓ Created {len(all_chunks)} chunks")

        # Step 5: Generate embeddings
        logger.info("\n[STEP 5] Generating embeddings...")
        embeddings = generate_embeddings(all_texts, cohere_client)

        # Step 6: Ingest into Qdrant
        logger.info("\n[STEP 6] Ingesting into Qdrant...")
        ingested_count = ingest_into_qdrant(
            qdrant_client,
            collection_name,
            all_chunks,
            embeddings
        )

        # Step 7: Verify ingestion
        logger.info("\n[STEP 7] Verifying ingestion...")
        collection_info = qdrant_client.get_collection(collection_name)
        logger.info(f"✓ Collection '{collection_name}' now contains {collection_info.points_count} points")

        logger.info("\n" + "="*70)
        logger.info("✓ INGESTION COMPLETE - SUCCESS!")
        logger.info("="*70)
        logger.info(f"\nSummary:")
        logger.info(f"  Files processed: {len(files)}")
        logger.info(f"  Total chunks: {len(all_chunks)}")
        logger.info(f"  Points in collection: {collection_info.points_count}")
        logger.info(f"  Embeddings dimension: 384")
        logger.info(f"  Collection name: {collection_name}")
        logger.info("\nYour RAG chatbot is now ready to answer questions about your book!")

        return True

    except Exception as e:
        logger.error(f"\n✗ INGESTION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
