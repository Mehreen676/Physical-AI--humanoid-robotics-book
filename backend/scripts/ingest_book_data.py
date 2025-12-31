"""
Ingest book content from Docusaurus frontend into Qdrant vector database.

This script:
1. Reads markdown files from the frontend docs/ directory
2. Parses content and metadata
3. Chunks the content intelligently
4. Generates embeddings for each chunk
5. Uploads to Qdrant with full metadata
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any
import logging
import re
from datetime import datetime
from uuid import uuid4

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from config import settings
from rag.retrieval import QdrantRetriever
from services.embeddings import EmbeddingsService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MarkdownChunker:
    """Intelligently chunk markdown content."""

    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        """
        Initialize chunker.

        Args:
            chunk_size: Target characters per chunk
            overlap: Character overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_content(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split markdown content into chunks.

        Args:
            content: Markdown text
            metadata: File metadata (path, title, section, etc.)

        Returns:
            List of chunk dicts with text and metadata
        """
        # Remove YAML front matter
        content = self._remove_frontmatter(content)

        # Split by headings to preserve semantic boundaries
        sections = self._split_by_headings(content)

        chunks = []
        chunk_id = 0

        for section in sections:
            # Further split sections by paragraph
            paragraphs = section.split('\n\n')

            current_chunk = ""
            for paragraph in paragraphs:
                if not paragraph.strip():
                    continue

                # If adding paragraph exceeds chunk_size, save current chunk
                if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                    chunk_dict = {
                        "text": current_chunk.strip(),
                        "metadata": {
                            **metadata,
                            "chunk_id": f"{metadata.get('file_id', 'unknown')}_{chunk_id}",
                            "position": chunk_id,
                        }
                    }
                    chunks.append(chunk_dict)
                    chunk_id += 1

                    # Add overlap from end of previous chunk
                    overlap_text = current_chunk[-self.overlap:] if len(current_chunk) > self.overlap else current_chunk
                    current_chunk = overlap_text + "\n\n" + paragraph
                else:
                    if current_chunk:
                        current_chunk += "\n\n" + paragraph
                    else:
                        current_chunk = paragraph

            # Save remaining chunk
            if current_chunk.strip():
                chunk_dict = {
                    "text": current_chunk.strip(),
                    "metadata": {
                        **metadata,
                        "chunk_id": f"{metadata.get('file_id', 'unknown')}_{chunk_id}",
                        "position": chunk_id,
                    }
                }
                chunks.append(chunk_dict)

        logger.info(f"Created {len(chunks)} chunks from {metadata.get('section', 'unknown')}")
        return chunks

    def _remove_frontmatter(self, content: str) -> str:
        """Remove YAML front matter from markdown."""
        if content.startswith('---'):
            # Find the closing ---
            lines = content.split('\n')
            for i in range(1, len(lines)):
                if lines[i].startswith('---'):
                    return '\n'.join(lines[i+1:])
        return content

    def _split_by_headings(self, content: str) -> List[str]:
        """Split content by markdown headings."""
        # Split by h2, h3, h4 headings
        sections = re.split(r'\n(#{2,4} .+)\n', content)

        result = []
        for i in range(0, len(sections), 2):
            heading = sections[i] if i < len(sections) else ""
            body = sections[i+1] if i+1 < len(sections) else ""

            if heading:
                section = heading + "\n" + body
            else:
                section = body

            if section.strip():
                result.append(section.strip())

        return result if result else [content]


class BookDataIngester:
    """Ingest book data from Docusaurus into Qdrant."""

    def __init__(
        self,
        frontend_docs_dir: Path,
        embeddings_service: EmbeddingsService,
        qdrant_retriever: QdrantRetriever
    ):
        """
        Initialize ingester.

        Args:
            frontend_docs_dir: Path to frontend docs/ directory
            embeddings_service: Embeddings service instance
            qdrant_retriever: Qdrant retriever instance
        """
        self.docs_dir = frontend_docs_dir
        self.embeddings = embeddings_service
        self.qdrant = qdrant_retriever
        self.chunker = MarkdownChunker(chunk_size=500, overlap=100)
        self.ingested_count = 0

    async def ingest_all(self) -> Dict[str, Any]:
        """
        Ingest all markdown files from frontend.

        Returns:
            Dictionary with ingestion statistics
        """
        if not self.docs_dir.exists():
            raise ValueError(f"Docs directory not found: {self.docs_dir}")

        logger.info(f"Starting ingestion from {self.docs_dir}")

        # Find all markdown files
        markdown_files = sorted(self.docs_dir.glob('**/*.md'))
        logger.info(f"Found {len(markdown_files)} markdown files")

        stats = {
            "total_files": len(markdown_files),
            "total_chunks": 0,
            "total_embeddings": 0,
            "start_time": datetime.now().isoformat(),
            "files_processed": []
        }

        for i, file_path in enumerate(markdown_files, 1):
            try:
                logger.info(f"[{i}/{len(markdown_files)}] Processing {file_path.name}...")
                file_stats = await self._ingest_file(file_path)
                stats["total_chunks"] += file_stats["chunks"]
                stats["total_embeddings"] += file_stats["embeddings"]
                stats["files_processed"].append({
                    "file": str(file_path.relative_to(self.docs_dir)),
                    "chunks": file_stats["chunks"],
                    "status": "success"
                })
            except Exception as e:
                logger.error(f"Failed to ingest {file_path.name}: {e}")
                stats["files_processed"].append({
                    "file": str(file_path.relative_to(self.docs_dir)),
                    "error": str(e),
                    "status": "failed"
                })

        stats["end_time"] = datetime.now().isoformat()
        return stats

    async def _ingest_file(self, file_path: Path) -> Dict[str, int]:
        """
        Ingest a single markdown file.

        Args:
            file_path: Path to markdown file

        Returns:
            Dictionary with chunk and embedding counts
        """
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract metadata from file path and front matter
        metadata = self._extract_metadata(file_path, content)

        # Chunk content
        chunks = self.chunker.chunk_content(content, metadata)

        if not chunks:
            logger.warning(f"No chunks created from {file_path.name}")
            return {"chunks": 0, "embeddings": 0}

        # Generate embeddings and upsert to Qdrant
        embedding_count = 0
        for chunk in chunks:
            try:
                # Generate embedding
                embedding = await self.embeddings.embed(chunk["text"])

                if not embedding or len(embedding) == 0:
                    logger.warning(f"Empty embedding for chunk {chunk['metadata']['chunk_id']}")
                    continue

                # Create unique point ID using UUID to avoid collisions
                point_id = int(uuid4().int & ((1 << 63) - 1))  # Use positive UUID as point ID

                # Upsert to Qdrant
                success = self.qdrant.upsert(
                    point_id=point_id,
                    vector=embedding,
                    payload={
                        "text": chunk["text"],
                        "point_id": str(point_id),  # Store ID in payload for tracking
                        **chunk["metadata"]
                    }
                )

                if success:
                    embedding_count += 1
                    self.ingested_count += 1
            except Exception as e:
                logger.error(f"Failed to embed chunk {chunk['metadata']['chunk_id']}: {e}")
                continue

        logger.info(f"✓ {file_path.name}: {len(chunks)} chunks → {embedding_count} embeddings")
        return {"chunks": len(chunks), "embeddings": embedding_count}

    def _extract_metadata(self, file_path: Path, content: str) -> Dict[str, Any]:
        """
        Extract metadata from file path and YAML front matter.

        Args:
            file_path: Path to markdown file
            content: File content

        Returns:
            Metadata dictionary
        """
        # Extract from file path
        rel_path = file_path.relative_to(self.docs_dir)
        parts = rel_path.parts

        section = parts[0] if len(parts) > 0 else "unknown"
        file_id = file_path.stem

        # Try to extract from front matter
        title = file_id.replace('-', ' ').title()
        if content.startswith('---'):
            lines = content.split('\n')
            for line in lines[1:]:
                if line.startswith('---'):
                    break
                if line.startswith('title:'):
                    title = line.split('title:', 1)[1].strip().strip('"\'')
                    break

        return {
            "section": section,
            "file_id": file_id,
            "file_path": str(rel_path),
            "title": title,
            "url": f"https://mehreen676.github.io/Physical-AI--humanoid-robotics-book/{rel_path.with_suffix('')}",
            "source": "frontend_docs",
            "ingested_at": datetime.now().isoformat()
        }


async def main():
    """Main ingestion function."""
    try:
        # Locate frontend docs directory
        frontend_dir = backend_dir.parent / "front-end" / "docs"
        if not frontend_dir.exists():
            raise ValueError(f"Frontend docs directory not found: {frontend_dir}")

        logger.info(f"Frontend docs directory: {frontend_dir}")

        # Initialize services
        logger.info("Initializing embeddings service...")
        embeddings = EmbeddingsService(
            provider=settings.embeddings_provider,
            api_key=settings.embeddings_api_key
        )

        logger.info("Initializing Qdrant retriever...")
        qdrant = QdrantRetriever(
            qdrant_url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            collection_name=settings.collection_name
        )

        # Create collection if it doesn't exist
        logger.info("Creating Qdrant collection if needed...")
        qdrant.create_collection(vector_size=384, distance="cosine")

        # Ingest data
        logger.info("=" * 80)
        logger.info("STARTING BOOK DATA INGESTION")
        logger.info("=" * 80)

        ingester = BookDataIngester(frontend_dir, embeddings, qdrant)
        stats = await ingester.ingest_all()

        # Print summary
        logger.info("=" * 80)
        logger.info("INGESTION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total files processed: {stats['total_files']}")
        logger.info(f"Total chunks created: {stats['total_chunks']}")
        logger.info(f"Total embeddings stored: {stats['total_embeddings']}")
        logger.info(f"Start time: {stats['start_time']}")
        logger.info(f"End time: {stats['end_time']}")

        # Print per-file stats
        logger.info("\nPer-file statistics:")
        for file_stat in stats['files_processed']:
            if file_stat['status'] == 'success':
                logger.info(f"  ✓ {file_stat['file']}: {file_stat['chunks']} chunks")
            else:
                logger.info(f"  ✗ {file_stat['file']}: {file_stat.get('error', 'unknown error')}")

        return stats

    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    logger.info(f"Backend directory: {backend_dir}")
    stats = asyncio.run(main())
