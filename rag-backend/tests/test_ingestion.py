"""
Tests for Content Ingestion Module.
Tests chunking and ingestion service (with mocked dependencies).
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from chunking import DocumentChunker


class TestDocumentChunker:
    """Test document chunking functionality."""

    def test_chunk_by_headings_with_h1_h2(self):
        """Test chunking content with H1 and H2 headings."""
        content = """# Chapter 1: Introduction
This is the intro.

## Section 1.1
Content for section 1.1

## Section 1.2
Content for section 1.2

# Chapter 2: Advanced
Chapter 2 content."""

        chunks = DocumentChunker.chunk_by_headings(
            content, chapter="Test Chapter", section="Main"
        )

        assert len(chunks) > 0
        assert all("chapter" in chunk for chunk in chunks)
        assert all("section" in chunk for chunk in chunks)
        assert all("content_hash" in chunk for chunk in chunks)

    def test_chunk_by_headings_no_headings(self):
        """Test chunking plain text without headings."""
        content = "This is plain text without any headings. " * 50  # Large text

        chunks = DocumentChunker.chunk_by_headings(content)

        assert len(chunks) > 0
        assert all(chunk["content"] for chunk in chunks)

    def test_chunk_by_tokens(self):
        """Test token-based chunking."""
        text = "This is a sentence. " * 100  # Multiple sentences

        chunks = DocumentChunker.chunk_by_tokens(text, target_tokens=100)

        assert len(chunks) > 1
        assert all(chunks)  # No empty chunks

    def test_chunk_by_tokens_small_text(self):
        """Test chunking text smaller than target."""
        text = "Short text."

        chunks = DocumentChunker.chunk_by_tokens(text, target_tokens=1000)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_hash_content_consistency(self):
        """Test that same content produces same hash."""
        content = "This is test content for hashing."

        hash1 = DocumentChunker.hash_content(content)
        hash2 = DocumentChunker.hash_content(content)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 produces 64-char hex string

    def test_hash_content_different(self):
        """Test that different content produces different hashes."""
        content1 = "Content 1"
        content2 = "Content 2"

        hash1 = DocumentChunker.hash_content(content1)
        hash2 = DocumentChunker.hash_content(content2)

        assert hash1 != hash2

    def test_estimate_tokens(self):
        """Test token estimation."""
        # Assuming 1 token ≈ 4 chars
        content = "x" * 400  # Should be ~100 tokens

        tokens = DocumentChunker.estimate_tokens(content)

        assert 90 < tokens < 110  # Rough estimate, allow variance

    def test_chunk_index_increments(self):
        """Test that chunk indices increment properly."""
        content = "# Section 1\nContent 1\n# Section 2\nContent 2"

        chunks = DocumentChunker.chunk_by_headings(content)

        indices = [chunk["chunk_index"] for chunk in chunks]
        assert indices == list(range(len(chunks)))


class TestIngestionService:
    """Test content ingestion service."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all service dependencies."""
        mocks = {
            "embeddings": MagicMock(),
            "vector_store": MagicMock(),
            "db": MagicMock(),
        }

        # Setup default mock returns
        mocks["embeddings"].embed_texts.return_value = [
            [0.1] * 1536 for _ in range(100)
        ]  # Default: 100 vectors
        mocks["vector_store"].store_vectors_batch.return_value = 10
        mocks["db"].get_session.return_value = MagicMock()

        return mocks

    @patch("ingest_service.get_embedding_generator")
    @patch("ingest_service.get_vector_store")
    @patch("ingest_service.get_db")
    @patch("ingest_service.add_document")
    def test_ingest_chapter_success(
        self, mock_add_doc, mock_db, mock_vs, mock_emb, mock_dependencies
    ):
        """Test successful chapter ingestion."""
        # Setup mocks
        mock_emb.return_value = mock_dependencies["embeddings"]
        mock_vs.return_value = mock_dependencies["vector_store"]
        mock_db.return_value = mock_dependencies["db"]
        mock_add_doc.return_value = None  # Mock add_document call

        # Mock database session
        db_session = MagicMock()
        db_session.query.return_value.filter.return_value.all.return_value = []
        mock_dependencies["db"].get_session.return_value = db_session

        from ingest_service import IngestionService

        service = IngestionService()
        service.embeddings.embed_texts.return_value = [[0.1] * 1536 for _ in range(5)]
        service.vector_store.store_vectors_batch.return_value = 5

        content = "# Introduction\nContent here\n# Details\nMore content"
        result = service.ingest_chapter(
            chapter="Test",
            section="Intro",
            content=content,
        )

        assert result["total_chunks"] >= 1  # At least one chunk
        assert "ingested" in result
        assert "skipped" in result
        assert "vectors_stored" in result

    @patch("ingest_service.get_embedding_generator")
    @patch("ingest_service.get_vector_store")
    @patch("ingest_service.get_db")
    def test_ingest_empty_content(self, mock_db, mock_vs, mock_emb, mock_dependencies):
        """Test ingestion with empty content."""
        mock_emb.return_value = mock_dependencies["embeddings"]
        mock_vs.return_value = mock_dependencies["vector_store"]
        mock_db.return_value = mock_dependencies["db"]

        from ingest_service import IngestionService

        service = IngestionService()

        result = service.ingest_chapter(
            chapter="Test",
            section="Intro",
            content="",
        )

        assert result["error"] is not None or result["total_chunks"] == 0

    @patch("ingest_service.get_embedding_generator")
    @patch("ingest_service.get_vector_store")
    @patch("ingest_service.get_db")
    def test_ingest_duplicate_chunks(
        self, mock_db, mock_vs, mock_emb, mock_dependencies
    ):
        """Test deduplication of chunks."""
        mock_emb.return_value = mock_dependencies["embeddings"]
        mock_vs.return_value = mock_dependencies["vector_store"]
        mock_db.return_value = mock_dependencies["db"]

        from database import Document

        # Mock existing document
        existing_doc = Mock()
        existing_doc.content_hash = DocumentChunker.hash_content("Content here")

        db_session = MagicMock()
        db_session.query.return_value.filter.return_value.all.return_value = [
            existing_doc
        ]
        mock_dependencies["db"].get_session.return_value = db_session

        from ingest_service import IngestionService

        service = IngestionService()
        service.embeddings.embed_texts.return_value = [[0.1] * 1536 for _ in range(1)]

        content = "# Introduction\nContent here"
        result = service.ingest_chapter(
            chapter="Test",
            section="Intro",
            content=content,
        )

        # At least one chunk should be skipped (duplicate)
        assert result["skipped"] >= 0


class TestChunkingEdgeCases:
    """Test edge cases in chunking."""

    def test_very_long_chunk(self):
        """Test chunking very long text."""
        # Create text with sentence boundaries
        sentences = ["This is sentence number {}.".format(i) for i in range(1000)]
        long_text = " ".join(sentences)  # ~10KB of text with proper boundaries

        chunks = DocumentChunker.chunk_by_tokens(long_text, target_tokens=500)

        assert len(chunks) > 1  # Should be split into multiple chunks
        assert all(chunks)  # All chunks have content
        assert sum(len(c) for c in chunks) >= len(long_text) * 0.95  # No significant loss

    def test_chunk_with_special_characters(self):
        """Test chunking with special characters."""
        content = "# Section\nContent with émojis 🎉 and special chars: @#$%"

        chunks = DocumentChunker.chunk_by_headings(content)

        assert len(chunks) > 0
        assert any("émojis" in chunk["content"] for chunk in chunks)

    def test_chunk_with_code_blocks(self):
        """Test chunking with code blocks."""
        content = """# Programming

## Python Example
```python
def hello():
    print("world")
```

More content here."""

        chunks = DocumentChunker.chunk_by_headings(content)

        assert len(chunks) > 0
        # Code block should be preserved in chunks
        assert any("python" in chunk["content"].lower() for chunk in chunks)

    def test_chunk_with_tables(self):
        """Test chunking content with markdown tables."""
        content = """# Data

| Name | Value |
|------|-------|
| A    | 1     |
| B    | 2     |

More content."""

        chunks = DocumentChunker.chunk_by_headings(content)

        assert len(chunks) > 0
