"""
Content Ingestion Service
Orchestrates document ingestion: chunking, embedding, and storage.
"""

import logging
import uuid
from typing import Dict, List, Tuple
from chunking import DocumentChunker
from embeddings import get_embedding_generator
from vector_store import get_vector_store
from database import add_document, get_db

logger = logging.getLogger(__name__)


class IngestionService:
    """Handles document ingestion workflow."""

    def __init__(self):
        """Initialize ingestion service with dependencies."""
        self.chunker = DocumentChunker()
        self.embeddings = get_embedding_generator()
        self.vector_store = get_vector_store()
        self.db = get_db()

    def ingest_chapter(
        self,
        chapter: str,
        section: str,
        content: str,
        book_version: str = "v1.0",
    ) -> Dict:
        """
        Ingest a chapter: chunk, embed, deduplicate, and store.

        Args:
            chapter: Chapter name/identifier
            section: Section name
            content: Full chapter text
            book_version: Version of book for tracking

        Returns:
            Dict with ingestion stats:
            {
                "ingested": int,  # New chunks embedded and stored
                "skipped": int,   # Duplicate chunks skipped
                "vectors_stored": int,
                "total_chunks": int,
                "error": str (optional)
            }
        """
        try:
            logger.info(f"📥 Starting ingestion: {chapter} / {section}")

            # Step 1: Chunk the content
            chunks = self.chunker.chunk_by_headings(
                content, chapter=chapter, section=section
            )

            if not chunks:
                return {
                    "ingested": 0,
                    "skipped": 0,
                    "vectors_stored": 0,
                    "total_chunks": 0,
                    "error": "No chunks generated",
                }

            # Step 2: Check for duplicates
            db_session = self.db.get_session()
            existing_hashes = set()

            try:
                from database import Document

                existing_docs = db_session.query(Document).filter(
                    Document.book_version == book_version
                ).all()
                existing_hashes = {doc.content_hash for doc in existing_docs}
            finally:
                db_session.close()

            # Separate new chunks from duplicates
            new_chunks = [
                chunk
                for chunk in chunks
                if chunk["content_hash"] not in existing_hashes
            ]
            skipped_count = len(chunks) - len(new_chunks)

            logger.info(
                f"📊 Chunk analysis: {len(chunks)} total, "
                f"{len(new_chunks)} new, {skipped_count} duplicates"
            )

            if not new_chunks:
                return {
                    "ingested": 0,
                    "skipped": skipped_count,
                    "vectors_stored": 0,
                    "total_chunks": len(chunks),
                }

            # Step 3: Generate embeddings for new chunks
            logger.info(f"🔄 Generating embeddings for {len(new_chunks)} chunks...")
            chunk_texts = [chunk["content"] for chunk in new_chunks]

            try:
                embeddings = self.embeddings.embed_texts(chunk_texts)
            except Exception as e:
                logger.error(f"❌ Embedding generation failed: {e}")
                return {
                    "ingested": 0,
                    "skipped": skipped_count,
                    "vectors_stored": 0,
                    "total_chunks": len(chunks),
                    "error": f"Embedding failed: {str(e)}",
                }

            # Step 4: Store in Qdrant + Neon
            logger.info(
                f"💾 Storing {len(new_chunks)} chunks in vector DB and Postgres..."
            )

            vectors_data = []
            ingested_count = 0

            for i, (chunk, embedding) in enumerate(zip(new_chunks, embeddings)):
                chunk_id = f"{chapter}_{section}_{chunk['chunk_index']}"
                doc_id = f"doc_{uuid.uuid4().hex[:12]}"

                # Prepare metadata for Qdrant
                metadata = {
                    "chapter": chunk["chapter"],
                    "section": chunk["section"],
                    "chunk_index": chunk["chunk_index"],
                    "book_version": book_version,
                    "doc_id": doc_id,
                }

                # Add optional subsection info
                if "subsection" in chunk:
                    metadata["subsection"] = chunk["subsection"]

                vectors_data.append((chunk_id, embedding, metadata))

                # Store in Neon
                try:
                    add_document(
                        doc_id=doc_id,
                        title=f"{chapter}: {section}",
                        chapter=chunk["chapter"],
                        section=chunk["section"],
                        content=chunk["content"],
                        content_hash=chunk["content_hash"],
                        vector_id=chunk_id,
                    )
                    ingested_count += 1
                except Exception as e:
                    logger.error(f"❌ Database storage failed for {doc_id}: {e}")
                    # Continue with next chunk
                    continue

            # Store all vectors in Qdrant
            try:
                vectors_stored = self.vector_store.store_vectors_batch(vectors_data)
            except Exception as e:
                logger.error(f"❌ Vector storage failed: {e}")
                vectors_stored = 0

            logger.info(
                f"✅ Ingestion complete: "
                f"ingested={ingested_count}, skipped={skipped_count}, "
                f"vectors_stored={vectors_stored}"
            )

            return {
                "ingested": ingested_count,
                "skipped": skipped_count,
                "vectors_stored": vectors_stored,
                "total_chunks": len(chunks),
            }

        except Exception as e:
            logger.error(f"❌ Unexpected error during ingestion: {e}", exc_info=True)
            return {
                "ingested": 0,
                "skipped": 0,
                "vectors_stored": 0,
                "total_chunks": 0,
                "error": str(e),
            }


# Singleton instance
_ingest_service_instance = None


def get_ingest_service() -> IngestionService:
    """Get or create ingestion service instance."""
    global _ingest_service_instance
    if _ingest_service_instance is None:
        _ingest_service_instance = IngestionService()
    return _ingest_service_instance
