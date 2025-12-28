#!/usr/bin/env python3
"""
RAG Embedding Pipeline: Extract, Embed, Store

Extracts text from deployed Docusaurus textbook, generates Cohere embeddings,
and stores vectors in Qdrant Cloud for RAG-based retrieval.
"""

import os
import logging
import sys
import time
from datetime import datetime
from typing import List, Tuple
from uuid import uuid4

import requests
from bs4 import BeautifulSoup
from xml.etree import ElementTree
import cohere
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from dotenv import load_dotenv


# ============================================================================
# LOGGING SETUP (T006)
# ============================================================================

def setup_logging() -> logging.Logger:
    """Set up structured logging with file and console output.

    Returns:
        Configured logger instance
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"backend_{timestamp}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized, output: {log_file}")
    return logger


logger = setup_logging()


# ============================================================================
# ENVIRONMENT & CONFIGURATION
# ============================================================================

load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
BASE_URL = os.getenv("BASE_URL", "https://mehreen676.github.io/Physical-AI--humanoid-robotics-book/")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))


# ============================================================================
# PHASE 2: CONTENT INGESTION (US1) - T007, T008, T009
# ============================================================================

def get_urls(base_url: str = BASE_URL) -> List[str]:
    """Fetch all content URLs from deployed Docusaurus site.

    Extracts URLs from sitemap.xml and filters to content pages.

    Args:
        base_url: Base URL of Docusaurus site (default from .env)

    Returns:
        List of content URLs, sorted and deduplicated

    Raises:
        None (logs warnings on error, returns empty list)
    """
    try:
        sitemap_url = f"{base_url}/sitemap.xml"
        logger.info(f"Fetching sitemap from {sitemap_url}")

        response = requests.get(sitemap_url, timeout=10)
        response.raise_for_status()

        root = ElementTree.fromstring(response.content)

        # Parse namespace
        namespace = {'': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        urls = []
        for url_elem in root.findall('.//loc', {'': 'http://www.sitemaps.org/schemas/sitemap/0.9'}):
            url = url_elem.text
            if url and not any(skip in url for skip in ['/search', '/api']):
                urls.append(url)

        # Fallback to simple parsing if namespace parsing fails
        if not urls:
            logger.warning("Namespace parsing failed, using simple regex")
            import re
            urls = re.findall(r'<loc>(.*?)</loc>', response.text)

        urls = sorted(list(set(urls)))
        logger.info(f"Found {len(urls)} content URLs")
        return urls

    except requests.Timeout:
        logger.warning("Timeout fetching sitemap, returning empty list")
        return []
    except Exception as e:
        logger.error(f"Error fetching URLs: {e}")
        return []


def extract_text(url: str) -> str:
    """Extract clean text from HTML page.

    Fetches HTML, parses with BeautifulSoup, removes navigation/footer,
    and returns cleaned main content text.

    Args:
        url: URL to extract text from

    Returns:
        Cleaned text string (empty string if extraction fails)
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove unwanted elements
        for element in soup.find_all(['script', 'style', 'nav', 'footer', 'aside', 'header']):
            element.decompose()

        # Try common content selectors for Docusaurus
        content = None
        for selector in ['article', 'main', '.markdown', '.content', '.docusaurus-content']:
            content = soup.select_one(selector)
            if content:
                break

        if not content:
            content = soup.body if soup.body else soup

        # Extract and normalize text
        text = content.get_text(strip=True)
        text = ' '.join(text.split())  # Normalize whitespace

        # Validate content
        if len(text) < 50:
            logger.warning(f"Content too short from {url}: {len(text)} chars")
            return ""

        if text.count(' ') < 5:  # Less than 5 words
            logger.warning(f"Content has too few words from {url}")
            return ""

        logger.debug(f"Extracted {len(text)} chars from {url}")
        return text

    except requests.Timeout:
        logger.warning(f"Timeout fetching {url}")
        return ""
    except Exception as e:
        logger.error(f"Error extracting text from {url}: {e}")
        return ""


# ============================================================================
# PHASE 3: EMBEDDING GENERATION (US2) - T011, T012, T013
# ============================================================================

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks for embedding.

    Divides text into fixed-size chunks with overlap to preserve context
    across chunk boundaries.

    Args:
        text: Source text to chunk
        chunk_size: Size of each chunk in characters (default 1000)
        overlap: Overlap between consecutive chunks (default 100)

    Returns:
        List of text chunks, each ≤ 2000 characters

    Raises:
        ValueError: If chunk_size <= overlap or invalid parameters
    """
    if not text or len(text) == 0:
        return []

    if chunk_size <= overlap:
        raise ValueError(f"chunk_size ({chunk_size}) must be > overlap ({overlap})")

    if chunk_size <= 0:
        raise ValueError(f"chunk_size must be positive, got {chunk_size}")

    chunks = []
    stride = chunk_size - overlap

    for i in range(0, len(text), stride):
        chunk = text[i:i + chunk_size]

        # Validate chunk
        if len(chunk) > 2000:
            logger.warning(f"Chunk exceeds 2000 char limit: {len(chunk)}")
            chunk = chunk[:2000]

        chunk = chunk.strip()
        if chunk:  # Skip empty chunks
            chunks.append(chunk)

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} char text")
    return chunks


def embed_chunks(chunks: List[str], model: str = "embed-english-v3.0") -> List[List[float]]:
    """Generate Cohere embeddings for text chunks.

    Batches chunks and calls Cohere API with exponential backoff retry
    on rate limits. Returns embeddings in same order as input.

    Args:
        chunks: List of text chunks to embed
        model: Cohere embedding model (default: embed-english-light-v3.0)

    Returns:
        List of embedding vectors (1024 dimensions each)

    Raises:
        Exception: On critical API errors (after retries)
    """
    if not chunks:
        return []

    try:
        client = cohere.ClientV2(api_key=COHERE_API_KEY)
        logger.info(f"Embedding {len(chunks)} chunks with Cohere")

        all_embeddings = []

        # Batch into groups of BATCH_SIZE
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i:i + BATCH_SIZE]

            retry_count = 0
            max_retries = 5
            wait_time = 1

            while retry_count < max_retries:
                try:
                    response = client.embed(
                        texts=batch,
                        model=model,
                        input_type="search_document"
                    )

                    # Extract embeddings from Cohere ClientV2 response
                    # response.embeddings.float_ contains the list of embedding vectors
                    if hasattr(response.embeddings, 'float_') and response.embeddings.float_:
                        embeddings_list = response.embeddings.float_
                        for emb in embeddings_list:
                            all_embeddings.append(list(emb) if not isinstance(emb, list) else emb)
                        logger.debug(f"Embedded batch {i//BATCH_SIZE + 1}: {len(batch)} chunks, got {len(embeddings_list)} embeddings")
                    else:
                        logger.warning(f"No embeddings in response for batch {i//BATCH_SIZE + 1}")
                    break

                except Exception as e:
                    if "429" in str(e) or "rate limit" in str(e).lower():
                        retry_count += 1
                        logger.warning(f"Rate limit hit, retry {retry_count}/{max_retries} in {wait_time}s")
                        time.sleep(wait_time)
                        wait_time *= 2
                    else:
                        raise

        logger.info(f"Generated {len(all_embeddings)} embeddings")
        return all_embeddings

    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise


def validate_embeddings(embeddings: List[List[float]]) -> List[List[float]]:
    """Validate embeddings for correct format and values.

    Checks that each embedding has 1024 dimensions and values in [-1, 1].

    Args:
        embeddings: List of embedding vectors

    Returns:
        List of valid embeddings (invalid ones skipped)
    """
    valid_embeddings = []

    for i, emb in enumerate(embeddings):
        if not isinstance(emb, list) or len(emb) != 1024:
            logger.warning(f"Embedding {i} has wrong dimensions: {len(emb) if isinstance(emb, list) else 'N/A'}")
            continue

        # Check for NaN or extreme values
        if any(v is None or (isinstance(v, float) and (v != v or abs(v) > 1)) for v in emb):
            logger.warning(f"Embedding {i} has invalid values")
            continue

        valid_embeddings.append(emb)

    logger.info(f"Validated {len(valid_embeddings)} embeddings (skipped {len(embeddings) - len(valid_embeddings)})")
    return valid_embeddings


# ============================================================================
# PHASE 4: VECTOR STORAGE (US3) - T015, T016
# ============================================================================

def store_in_qdrant(
    chunks: List[str],
    urls: List[str],
    embeddings: List[List[float]],
    positions: List[int]
) -> int:
    """Upsert document chunks to Qdrant collection.

    Creates/updates "rag_embedding" collection and stores points with
    full metadata for retrieval context.

    Args:
        chunks: Text chunks to store
        urls: Source URLs (parallel to chunks)
        embeddings: Embedding vectors (parallel to chunks)
        positions: Position indices (parallel to chunks)

    Returns:
        Count of successfully stored points
    """
    try:
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        collection_name = "rag_embedding"

        logger.info(f"Connecting to Qdrant at {QDRANT_URL}")

        # Check if collection exists, recreate if dimensions don't match
        try:
            collection = client.get_collection(collection_name)
            # Check if dimensions match
            if hasattr(collection, 'config') and hasattr(collection.config, 'params'):
                actual_dim = collection.config.params.vectors.size
                if actual_dim != 1024:
                    logger.warning(f"Collection exists but has {actual_dim} dims, expected 1024. Recreating...")
                    client.delete_collection(collection_name)
                    logger.info(f"Creating collection '{collection_name}' with 1024 dimensions")
                    client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
                    )
                else:
                    logger.info(f"Collection '{collection_name}' exists with correct dimensions")
            else:
                logger.info(f"Collection '{collection_name}' exists")
        except Exception as e:
            logger.info(f"Creating collection '{collection_name}' with 1024 dimensions")
            try:
                client.delete_collection(collection_name)
            except:
                pass
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
            )

        # Prepare points
        points = []
        for chunk, url, embedding, position in zip(chunks, urls, embeddings, positions):
            point = PointStruct(
                id=str(uuid4()),
                vector=embedding,
                payload={
                    "content": chunk,
                    "url": url,
                    "position": position,
                    "created_at": datetime.now().isoformat(),
                    "chunk_size": len(chunk)
                }
            )
            points.append(point)

        # Upsert points
        logger.info(f"Upserting {len(points)} points to Qdrant")
        client.upsert(
            collection_name=collection_name,
            points=points
        )

        # Verify retrieval
        logger.info("Verifying vectors are searchable...")
        if embeddings:
            try:
                results = client.search(
                    collection_name=collection_name,
                    query_vector=embeddings[0],
                    limit=1
                )
                logger.info(f"Verification: {len(results)} results found in search")
            except Exception as e:
                logger.warning(f"Verification search failed: {e}")

        logger.info(f"Successfully stored {len(points)} vectors in Qdrant")
        return len(points)

    except Exception as e:
        logger.error(f"Error storing vectors in Qdrant: {e}")
        raise


# ============================================================================
# PHASE 5: MAIN ORCHESTRATOR (T018) - T019, T020
# ============================================================================

def main() -> None:
    """Orchestrate the complete RAG embedding pipeline.

    Executes: URL discovery → text extraction → chunking → embedding → storage

    Logs progress and final summary of processed content.
    """
    try:
        # Validate configuration
        if not all([COHERE_API_KEY, QDRANT_URL, QDRANT_API_KEY]):
            logger.error("Missing required environment variables (COHERE_API_KEY, QDRANT_URL, QDRANT_API_KEY)")
            sys.exit(1)

        logger.info("="*70)
        logger.info("Starting RAG Embedding Pipeline")
        logger.info("="*70)

        # Phase 2: Get URLs
        urls = get_urls()
        if not urls:
            logger.error("No URLs found, aborting")
            sys.exit(1)

        logger.info(f"Processing {len(urls)} URLs")

        # Accumulators
        total_chunks = 0
        total_vectors = 0
        processed_urls = 0
        failed_urls = 0

        # Process each URL
        for idx, url in enumerate(urls, 1):
            logger.info(f"[{idx}/{len(urls)}] Processing {url}")

            try:
                # Extract text
                text = extract_text(url)
                if not text:
                    logger.warning(f"Skipping {url}: no content extracted")
                    failed_urls += 1
                    continue

                # Chunk text
                chunks = chunk_text(text)
                if not chunks:
                    logger.warning(f"Skipping {url}: no chunks created")
                    failed_urls += 1
                    continue

                # Embed chunks
                embeddings = embed_chunks(chunks)
                embeddings = validate_embeddings(embeddings)

                if not embeddings:
                    logger.warning(f"Skipping {url}: no valid embeddings")
                    failed_urls += 1
                    continue

                # Store in Qdrant
                positions = list(range(len(chunks)))
                url_list = [url] * len(chunks)

                count = store_in_qdrant(chunks, url_list, embeddings, positions)

                # Update accumulators
                total_chunks += len(chunks)
                total_vectors += count
                processed_urls += 1

                # Progress checkpoint every 10 URLs
                if idx % 10 == 0:
                    logger.info(f"Checkpoint: Processed {processed_urls} URLs, "
                              f"created {total_chunks} chunks, stored {total_vectors} vectors")

            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                failed_urls += 1
                continue

        # Final summary
        logger.info("="*70)
        logger.info("Pipeline Complete!")
        logger.info("="*70)
        logger.info(f"Total URLs processed: {processed_urls}/{len(urls)}")
        logger.info(f"Failed URLs: {failed_urls}")
        logger.info(f"Total chunks created: {total_chunks}")
        logger.info(f"Total vectors stored: {total_vectors}")
        logger.info("="*70)

        if processed_urls > 0:
            logger.info(f"Success rate: {100*processed_urls/len(urls):.1f}%")

        sys.exit(0)

    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error in pipeline: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
