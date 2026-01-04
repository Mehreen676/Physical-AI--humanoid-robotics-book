"""
Text chunking module with configurable token-based overlap.

Chunks text into segments of 300-500 tokens with overlap to maintain context
across chunk boundaries. Uses tiktoken for accurate token counting.
"""

import logging
from typing import List, Dict, Any
import tiktoken

logger = logging.getLogger(__name__)


class TextChunker:
    """Chunks text into token-based segments with overlap."""

    def __init__(self, chunk_size: int = 400, chunk_overlap: int = 100):
        """
        Initialize the text chunker.

        Args:
            chunk_size: Target tokens per chunk (300-500 recommended)
            chunk_overlap: Token overlap between consecutive chunks
        """
        if not (300 <= chunk_size <= 500):
            logger.warning(f"chunk_size {chunk_size} outside recommended range 300-500")

        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Use cl100k_base encoding (same as GPT-3.5/4)
        self.encoding = tiktoken.get_encoding("cl100k_base")

        logger.info(
            f"Initialized TextChunker: chunk_size={chunk_size}, "
            f"overlap={chunk_overlap}"
        )

    def chunk_text(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Chunk text into overlapping segments with metadata.

        Args:
            text: Input text to chunk
            metadata: Metadata to attach to each chunk

        Returns:
            List of dicts with 'text', 'metadata', and 'chunk_index'
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to chunker")
            return []

        # Tokenize the entire text
        tokens = self.encoding.encode(text)
        total_tokens = len(tokens)

        logger.debug(f"Chunking {total_tokens} tokens from {metadata.get('source_file', 'unknown')}")

        chunks = []
        chunk_index = 0
        start_idx = 0

        while start_idx < total_tokens:
            # Extract chunk tokens
            end_idx = min(start_idx + self.chunk_size, total_tokens)
            chunk_tokens = tokens[start_idx:end_idx]

            # Decode back to text
            chunk_text = self.encoding.decode(chunk_tokens)

            # Create chunk with metadata
            chunk = {
                "text": chunk_text,
                "metadata": {
                    **metadata,
                    "chunk_index": chunk_index,
                    "total_chunks": -1,  # Will be updated after all chunks created
                    "token_count": len(chunk_tokens),
                    "start_token": start_idx,
                    "end_token": end_idx
                }
            }

            chunks.append(chunk)
            chunk_index += 1

            # Move to next chunk with overlap
            start_idx += (self.chunk_size - self.chunk_overlap)

        # Update total_chunks in all chunks
        total_chunks = len(chunks)
        for chunk in chunks:
            chunk["metadata"]["total_chunks"] = total_chunks

        logger.info(
            f"Created {total_chunks} chunks from {metadata.get('source_file', 'unknown')}"
        )

        return chunks

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Input text

        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))
