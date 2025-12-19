"""
Content Retrieval Service
Retrieves relevant chunks from vector store based on semantic search.
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from src.embeddings import get_embedding_generator
from src.vector_store import get_vector_store

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    """A retrieved chunk with metadata and similarity score."""

    doc_id: str
    chapter: str
    section: str
    content: str
    similarity_score: float
    chunk_index: int = 0
    subsection: Optional[str] = None
    book_version: str = "v1.0"

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "doc_id": self.doc_id,
            "chapter": self.chapter,
            "section": self.section,
            "subsection": self.subsection,
            "content": self.content,
            "similarity_score": round(self.similarity_score, 4),
            "chunk_index": self.chunk_index,
            "book_version": self.book_version,
        }


class RetrieverAgent:
    """Retrieves relevant content chunks via semantic search."""

    def __init__(self, top_k: int = 5, min_similarity: float = 0.5):
        """
        Initialize retriever.

        Args:
            top_k: Number of top results to return
            min_similarity: Minimum similarity threshold (0-1)
        """
        self.top_k = top_k
        self.min_similarity = min_similarity
        self.embeddings = get_embedding_generator()
        self.vector_store = get_vector_store()

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        book_version: str = "v1.0",
        chapter_filter: Optional[str] = None,
        mode: str = "full_book",
    ) -> Tuple[List[RetrievedChunk], Dict]:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: User query text
            top_k: Override default top_k for this request
            book_version: Book version to search in
            chapter_filter: Optional chapter to filter by
            mode: "full_book" or "selected_text" (for future use)

        Returns:
            Tuple of (retrieved_chunks, metadata_dict) where metadata includes:
            - query_tokens: Number of tokens in query
            - chunks_retrieved: Number of chunks returned
            - search_time_ms: Search latency
            - mode: Retrieval mode used
        """
        try:
            k = top_k or self.top_k
            logger.info(
                f"🔍 Retrieving: '{query}' (top_k={k}, book_version={book_version})"
            )

            # Step 1: Generate query embedding
            query_embedding = self.embeddings.embed_text(query)
            query_tokens = self.embeddings.estimate_tokens(query)

            # Step 2: Build filter for Qdrant
            filters = {
                "book_version": book_version,
            }
            if chapter_filter:
                filters["chapter"] = chapter_filter

            # Step 3: Search in Qdrant
            logger.info(
                f"🔎 Searching Qdrant for '{query}' with filters: {filters}"
            )
            search_results = self.vector_store.query_vectors(
                query_embedding=query_embedding,
                k=k * 2,  # Get more than needed for filtering
                filters=filters,
            )

            # Step 4: Parse and filter results
            retrieved_chunks = []
            for result in search_results:
                # Check minimum similarity threshold
                if result["similarity_score"] < self.min_similarity:
                    logger.debug(
                        f"⏭️  Skipping: similarity {result['similarity_score']:.4f} < {self.min_similarity}"
                    )
                    continue

                # Create RetrievedChunk object
                chunk = RetrievedChunk(
                    doc_id=result.get("metadata", {}).get("doc_id", "unknown"),
                    chapter=result.get("metadata", {}).get("chapter", "Unknown"),
                    section=result.get("metadata", {}).get("section", "Unknown"),
                    subsection=result.get("metadata", {}).get("subsection"),
                    content=result.get("content", ""),
                    similarity_score=result["similarity_score"],
                    chunk_index=result.get("metadata", {}).get("chunk_index", 0),
                    book_version=result.get("metadata", {}).get(
                        "book_version", "v1.0"
                    ),
                )

                retrieved_chunks.append(chunk)

                # Stop after getting enough results
                if len(retrieved_chunks) >= k:
                    break

            logger.info(
                f"✅ Retrieved {len(retrieved_chunks)} relevant chunks "
                f"(min_similarity={self.min_similarity})"
            )

            # Metadata about retrieval
            metadata = {
                "query_tokens": query_tokens,
                "chunks_retrieved": len(retrieved_chunks),
                "mode": mode,
                "book_version": book_version,
                "min_similarity": self.min_similarity,
            }

            return retrieved_chunks, metadata

        except Exception as e:
            logger.error(f"❌ Retrieval failed: {e}", exc_info=True)
            raise

    def retrieve_with_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        book_version: str = "v1.0",
    ) -> Tuple[str, Dict]:
        """
        Retrieve chunks and assemble into context string for generation.

        Args:
            query: User query
            top_k: Number of top results
            book_version: Book version to search

        Returns:
            Tuple of (context_string, metadata) where context_string
            is formatted for use in LLM prompts
        """
        chunks, metadata = self.retrieve(
            query=query,
            top_k=top_k,
            book_version=book_version,
        )

        # Assemble context from chunks
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            # Format: "Source N: [Chapter > Section] Content"
            source = f"{chunk.chapter} > {chunk.section}"
            if chunk.subsection:
                source += f" > {chunk.subsection}"

            part = f"[Source {i}: {source} (sim: {chunk.similarity_score:.2f})]\n{chunk.content}"
            context_parts.append(part)

        context_string = "\n\n".join(context_parts)

        metadata["context_length"] = len(context_string)
        metadata["context_chunks"] = len(chunks)

        return context_string, metadata

    def retrieve_by_chapter(
        self,
        chapter: str,
        book_version: str = "v1.0",
        limit: int = 50,
    ) -> Tuple[List[RetrievedChunk], Dict]:
        """
        Retrieve all chunks from a specific chapter.

        Args:
            chapter: Chapter name
            book_version: Book version
            limit: Maximum chunks to return

        Returns:
            Tuple of (chunks, metadata)
        """
        logger.info(f"📖 Retrieving all chunks from chapter: {chapter}")

        try:
            # Use a dummy query embedding (e.g., zeros) to get all results
            # In practice, this would filter by chapter directly in Qdrant
            dummy_query = "chapter contents"
            query_embedding = self.embeddings.embed_text(dummy_query)

            filters = {
                "book_version": book_version,
                "chapter": chapter,
            }

            search_results = self.vector_store.query_vectors(
                query_embedding=query_embedding,
                k=limit,
                filters=filters,
            )

            chunks = []
            for result in search_results:
                chunk = RetrievedChunk(
                    doc_id=result.get("metadata", {}).get("doc_id", "unknown"),
                    chapter=result.get("metadata", {}).get("chapter", "Unknown"),
                    section=result.get("metadata", {}).get("section", "Unknown"),
                    subsection=result.get("metadata", {}).get("subsection"),
                    content=result.get("content", ""),
                    similarity_score=result["similarity_score"],
                    chunk_index=result.get("metadata", {}).get("chunk_index", 0),
                    book_version=book_version,
                )
                chunks.append(chunk)

            logger.info(f"✅ Retrieved {len(chunks)} chunks from chapter: {chapter}")

            metadata = {
                "chapter": chapter,
                "book_version": book_version,
                "chunks_retrieved": len(chunks),
                "mode": "chapter_browse",
            }

            return chunks, metadata

        except Exception as e:
            logger.error(f"❌ Chapter retrieval failed: {e}", exc_info=True)
            raise


# Singleton instance
_retriever_instance = None


def get_retriever(top_k: int = 5, min_similarity: float = 0.5) -> RetrieverAgent:
    """Get or create retriever instance."""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = RetrieverAgent(top_k=top_k, min_similarity=min_similarity)
    return _retriever_instance
