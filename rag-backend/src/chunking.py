"""
Document Chunking Module
Intelligently splits long documents into semantic chunks.
"""

import re
import hashlib
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

# Rough token estimation: 1 token ≈ 4 characters
TOKENS_PER_CHAR = 0.25
TARGET_CHUNK_TOKENS = 800
TARGET_CHUNK_CHARS = int(TARGET_CHUNK_TOKENS / TOKENS_PER_CHAR)


class DocumentChunker:
    """Intelligently chunk documents for RAG ingestion."""

    @staticmethod
    def chunk_by_headings(
        content: str,
        chapter: str = "Unknown",
        section: str = "Unknown",
    ) -> List[Dict[str, str]]:
        """
        Split document by H1/H2 headings, with fallback to token-based chunking.

        Args:
            content: Full document text
            chapter: Chapter name for metadata
            section: Section name for metadata

        Returns:
            List of chunks with metadata:
            {
                'chapter': str,
                'section': str,
                'content': str,
                'content_hash': str,
                'chunk_index': int
            }
        """
        chunks = []
        chunk_index = 0

        # Split by H1 (#) first
        h1_sections = re.split(r"^# +(.+?)$", content, flags=re.MULTILINE)

        # h1_sections format: [text_before_first_h1, h1_title, h1_content, h1_title2, h1_content2, ...]
        for i in range(1, len(h1_sections), 2):
            if i >= len(h1_sections):
                break

            section_title = h1_sections[i].strip()
            section_content = h1_sections[i + 1] if i + 1 < len(h1_sections) else ""

            # Split section by H2 (##)
            h2_sections = re.split(
                r"^## +(.+?)$", section_content, flags=re.MULTILINE
            )

            for j in range(1, len(h2_sections), 2):
                if j >= len(h2_sections):
                    break

                subsection_title = h2_sections[j].strip()
                subsection_content = (
                    h2_sections[j + 1] if j + 1 < len(h2_sections) else ""
                )

                # If subsection is small enough, keep it as one chunk
                if (
                    len(subsection_content)
                    <= TARGET_CHUNK_CHARS * 1.5
                ):
                    chunk_text = f"### {subsection_title}\n{subsection_content}".strip()
                    if chunk_text.strip():
                        chunk_hash = DocumentChunker.hash_content(chunk_text)
                        chunks.append(
                            {
                                "chapter": chapter,
                                "section": section_title,
                                "subsection": subsection_title,
                                "content": chunk_text,
                                "content_hash": chunk_hash,
                                "chunk_index": chunk_index,
                            }
                        )
                        chunk_index += 1
                else:
                    # Split large subsections by token count
                    sub_chunks = DocumentChunker.chunk_by_tokens(
                        subsection_content, TARGET_CHUNK_TOKENS
                    )
                    for sub_chunk in sub_chunks:
                        chunk_text = f"### {subsection_title}\n{sub_chunk}".strip()
                        chunk_hash = DocumentChunker.hash_content(chunk_text)
                        chunks.append(
                            {
                                "chapter": chapter,
                                "section": section_title,
                                "subsection": subsection_title,
                                "content": chunk_text,
                                "content_hash": chunk_hash,
                                "chunk_index": chunk_index,
                            }
                        )
                        chunk_index += 1

        # If no H1/H2 found, chunk the entire content by tokens
        if not chunks:
            sub_chunks = DocumentChunker.chunk_by_tokens(content, TARGET_CHUNK_TOKENS)
            for sub_chunk in sub_chunks:
                chunk_hash = DocumentChunker.hash_content(sub_chunk)
                chunks.append(
                    {
                        "chapter": chapter,
                        "section": section,
                        "content": sub_chunk,
                        "content_hash": chunk_hash,
                        "chunk_index": chunk_index,
                    }
                )
                chunk_index += 1

        logger.info(
            f"✅ Split '{chapter}' into {len(chunks)} chunks "
            f"(avg {len(content) / len(chunks) if chunks else 0:.0f} chars/chunk)"
        )
        return chunks

    @staticmethod
    def chunk_by_tokens(
        content: str, target_tokens: int = TARGET_CHUNK_TOKENS
    ) -> List[str]:
        """
        Split content into chunks based on token count.

        Args:
            content: Text to chunk
            target_tokens: Target tokens per chunk (actual chars = tokens / 0.25)

        Returns:
            List of text chunks
        """
        target_chars = int(target_tokens / TOKENS_PER_CHAR)
        chunks = []

        # Split by sentences first (if they exist)
        sentences = re.split(r"(?<=[.!?])\s+", content)

        # If no sentence boundaries found, split by newlines or words
        if len(sentences) <= 1:
            sentences = content.split("\n") if "\n" in content else content.split()

        current_chunk = ""
        for unit in sentences:
            test_chunk = current_chunk + (" " if current_chunk else "") + unit
            if len(test_chunk) <= target_chars:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = unit

        if current_chunk:
            chunks.append(current_chunk.strip())

        # If still no chunks (single very long unit), force split by char count
        if not chunks and content:
            for i in range(0, len(content), target_chars):
                chunks.append(content[i : i + target_chars].strip())

        return chunks

    @staticmethod
    def hash_content(content: str) -> str:
        """Generate SHA256 hash of content for deduplication."""
        return hashlib.sha256(content.encode()).hexdigest()

    @staticmethod
    def estimate_tokens(content: str) -> int:
        """Estimate token count (rough approximation)."""
        return int(len(content) * TOKENS_PER_CHAR)
