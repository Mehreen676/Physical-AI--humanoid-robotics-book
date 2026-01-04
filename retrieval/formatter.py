"""
Result formatting utilities.
"""

from typing import List, Dict
from qdrant_client.models import ScoredPoint
from .schemas import RetrievedChunk, ChunkMetadata


class ResultFormatter:
    """Format Qdrant search results to standard schema."""

    @staticmethod
    def format_results(scored_points: List[ScoredPoint]) -> List[Dict]:
        """
        Format Qdrant ScoredPoint objects to RetrievedChunk dictionaries.

        Args:
            scored_points: List of ScoredPoint objects from Qdrant

        Returns:
            List of formatted chunk dictionaries

        Raises:
            ValueError: If metadata validation fails
        """
        formatted_chunks = []

        for point in scored_points:
            # Extract payload
            payload = point.payload

            # Create metadata
            metadata = ChunkMetadata(
                chapter=payload.get("chapter", "Unknown"),
                section=payload.get("section", "Unknown"),
                source_file=payload.get("source_file", "Unknown"),
                chunk_index=payload.get("chunk_index", 0),
                total_chunks=payload.get("total_chunks", 1),
                token_count=payload.get("token_count")
            )

            # Create chunk
            chunk = RetrievedChunk(
                text=payload.get("text", ""),
                metadata=metadata,
                score=point.score
            )

            formatted_chunks.append(chunk.dict())

        # Sort by score descending
        formatted_chunks.sort(key=lambda x: x["score"], reverse=True)

        return formatted_chunks

    @staticmethod
    def validate_metadata_integrity(chunks: List[Dict]) -> bool:
        """
        Validate that all chunks have complete metadata.

        Args:
            chunks: List of formatted chunk dictionaries

        Returns:
            True if all metadata is valid

        Raises:
            ValueError: If validation fails
        """
        required_fields = ["text", "metadata", "score"]
        required_metadata_fields = [
            "chapter", "section", "source_file",
            "chunk_index", "total_chunks"
        ]

        for i, chunk in enumerate(chunks):
            # Check top-level fields
            for field in required_fields:
                if field not in chunk:
                    raise ValueError(f"Chunk {i} missing required field: {field}")

            # Check metadata fields
            metadata = chunk["metadata"]
            for field in required_metadata_fields:
                if field not in metadata:
                    raise ValueError(f"Chunk {i} metadata missing required field: {field}")

            # Validate chunk_index < total_chunks
            if metadata["chunk_index"] >= metadata["total_chunks"]:
                raise ValueError(
                    f"Chunk {i} has invalid chunk_index ({metadata['chunk_index']}) >= "
                    f"total_chunks ({metadata['total_chunks']})"
                )

            # Validate score range
            if not (0.0 <= chunk["score"] <= 1.0):
                raise ValueError(f"Chunk {i} has invalid score: {chunk['score']}")

        return True
