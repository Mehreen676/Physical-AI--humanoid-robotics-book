"""
Tests for Content Retrieval Service.
Tests retrieval and ranking (with mocked dependencies).
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from retrieval_service import RetrievedChunk, RetrieverAgent, get_retriever


class TestRetrievedChunk:
    """Test RetrievedChunk dataclass."""

    def test_retrieved_chunk_creation(self):
        """Test creating a retrieved chunk."""
        chunk = RetrievedChunk(
            doc_id="doc_123",
            chapter="Chapter 1",
            section="Introduction",
            content="This is content",
            similarity_score=0.95,
        )

        assert chunk.doc_id == "doc_123"
        assert chunk.chapter == "Chapter 1"
        assert chunk.similarity_score == 0.95

    def test_retrieved_chunk_to_dict(self):
        """Test converting chunk to dictionary."""
        chunk = RetrievedChunk(
            doc_id="doc_123",
            chapter="Chapter 1",
            section="Intro",
            content="Content",
            similarity_score=0.85,
            subsection="Background",
        )

        chunk_dict = chunk.to_dict()

        assert chunk_dict["doc_id"] == "doc_123"
        assert chunk_dict["chapter"] == "Chapter 1"
        assert "similarity_score" in chunk_dict
        assert chunk_dict["subsection"] == "Background"


class TestRetrieverAgent:
    """Test retriever agent functionality."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock embeddings and vector store."""
        mocks = {
            "embeddings": MagicMock(),
            "vector_store": MagicMock(),
        }

        # Setup default returns
        mocks["embeddings"].embed_text.return_value = [0.1] * 1536
        mocks["embeddings"].estimate_tokens.return_value = 10
        mocks["vector_store"].query_vectors.return_value = [
            {
                "similarity_score": 0.95,
                "metadata": {
                    "doc_id": "doc_001",
                    "chapter": "Module 1",
                    "section": "Introduction",
                    "chunk_index": 0,
                    "book_version": "v1.0",
                },
                "content": "This is relevant content about ROS 2.",
            },
            {
                "similarity_score": 0.87,
                "metadata": {
                    "doc_id": "doc_002",
                    "chapter": "Module 1",
                    "section": "Basics",
                    "chunk_index": 1,
                    "book_version": "v1.0",
                },
                "content": "ROS 2 is a robotics framework.",
            },
        ]

        return mocks

    @patch("retrieval_service.get_embedding_generator")
    @patch("retrieval_service.get_vector_store")
    def test_retrieve_success(self, mock_vs, mock_emb, mock_dependencies):
        """Test successful retrieval."""
        mock_emb.return_value = mock_dependencies["embeddings"]
        mock_vs.return_value = mock_dependencies["vector_store"]

        retriever = RetrieverAgent(top_k=5, min_similarity=0.5)
        retriever.embeddings = mock_dependencies["embeddings"]
        retriever.vector_store = mock_dependencies["vector_store"]

        chunks, metadata = retriever.retrieve("What is ROS 2?")

        assert len(chunks) == 2
        assert chunks[0].similarity_score == 0.95
        assert chunks[1].similarity_score == 0.87
        assert metadata["chunks_retrieved"] == 2
        assert metadata["query_tokens"] == 10

    @patch("retrieval_service.get_embedding_generator")
    @patch("retrieval_service.get_vector_store")
    def test_retrieve_with_similarity_threshold(self, mock_vs, mock_emb, mock_dependencies):
        """Test retrieval with similarity threshold filtering."""
        mock_emb.return_value = mock_dependencies["embeddings"]
        mock_vs.return_value = mock_dependencies["vector_store"]

        # Add a low-similarity result
        mock_dependencies["vector_store"].query_vectors.return_value = [
            {
                "similarity_score": 0.95,
                "metadata": {
                    "doc_id": "doc_001",
                    "chapter": "Module 1",
                    "section": "Intro",
                    "chunk_index": 0,
                    "book_version": "v1.0",
                },
                "content": "Relevant content",
            },
            {
                "similarity_score": 0.3,  # Below threshold
                "metadata": {
                    "doc_id": "doc_002",
                    "chapter": "Module 1",
                    "section": "Basics",
                    "chunk_index": 1,
                    "book_version": "v1.0",
                },
                "content": "Not relevant",
            },
        ]

        retriever = RetrieverAgent(top_k=5, min_similarity=0.5)
        retriever.embeddings = mock_dependencies["embeddings"]
        retriever.vector_store = mock_dependencies["vector_store"]

        chunks, metadata = retriever.retrieve("What is ROS 2?")

        # Only 1 chunk should pass the similarity threshold
        assert len(chunks) == 1
        assert chunks[0].similarity_score == 0.95

    @patch("retrieval_service.get_embedding_generator")
    @patch("retrieval_service.get_vector_store")
    def test_retrieve_with_context(self, mock_vs, mock_emb, mock_dependencies):
        """Test retrieving with context assembly."""
        mock_emb.return_value = mock_dependencies["embeddings"]
        mock_vs.return_value = mock_dependencies["vector_store"]

        retriever = RetrieverAgent(top_k=5, min_similarity=0.5)
        retriever.embeddings = mock_dependencies["embeddings"]
        retriever.vector_store = mock_dependencies["vector_store"]

        context, metadata = retriever.retrieve_with_context("What is ROS 2?")

        assert "Source 1" in context
        assert "Source 2" in context
        assert "Module 1" in context
        assert "Introduction" in context
        assert metadata["context_chunks"] == 2
        assert metadata["context_length"] > 0

    @patch("retrieval_service.get_embedding_generator")
    @patch("retrieval_service.get_vector_store")
    def test_retrieve_empty_results(self, mock_vs, mock_emb, mock_dependencies):
        """Test retrieval with no results above threshold."""
        mock_emb.return_value = mock_dependencies["embeddings"]
        mock_vs.return_value = mock_dependencies["vector_store"]

        # All results below threshold
        mock_dependencies["vector_store"].query_vectors.return_value = [
            {
                "similarity_score": 0.3,
                "metadata": {
                    "doc_id": "doc_001",
                    "chapter": "Module 1",
                    "section": "Intro",
                    "chunk_index": 0,
                    "book_version": "v1.0",
                },
                "content": "Not relevant",
            },
        ]

        retriever = RetrieverAgent(top_k=5, min_similarity=0.5)
        retriever.embeddings = mock_dependencies["embeddings"]
        retriever.vector_store = mock_dependencies["vector_store"]

        chunks, metadata = retriever.retrieve("What is ROS 2?")

        assert len(chunks) == 0
        assert metadata["chunks_retrieved"] == 0

    @patch("retrieval_service.get_embedding_generator")
    @patch("retrieval_service.get_vector_store")
    def test_retrieve_with_chapter_filter(self, mock_vs, mock_emb, mock_dependencies):
        """Test retrieval with chapter filtering."""
        mock_emb.return_value = mock_dependencies["embeddings"]
        mock_vs.return_value = mock_dependencies["vector_store"]

        retriever = RetrieverAgent(top_k=5, min_similarity=0.5)
        retriever.embeddings = mock_dependencies["embeddings"]
        retriever.vector_store = mock_dependencies["vector_store"]

        chunks, metadata = retriever.retrieve(
            "What is ROS 2?",
            chapter_filter="Module 1",
        )

        # Verify query_vectors was called with filters
        call_args = mock_dependencies["vector_store"].query_vectors.call_args
        assert call_args is not None
        assert call_args.kwargs.get("filters", {}).get("chapter") == "Module 1"

    @patch("retrieval_service.get_embedding_generator")
    @patch("retrieval_service.get_vector_store")
    def test_retrieve_by_chapter(self, mock_vs, mock_emb, mock_dependencies):
        """Test retrieving all chunks from a chapter."""
        mock_emb.return_value = mock_dependencies["embeddings"]
        mock_vs.return_value = mock_dependencies["vector_store"]

        retriever = RetrieverAgent(top_k=5, min_similarity=0.5)
        retriever.embeddings = mock_dependencies["embeddings"]
        retriever.vector_store = mock_dependencies["vector_store"]

        chunks, metadata = retriever.retrieve_by_chapter("Module 1")

        assert len(chunks) == 2
        assert all(chunk.chapter == "Module 1" for chunk in chunks)
        assert metadata["mode"] == "chapter_browse"

    def test_retriever_singleton(self):
        """Test retriever singleton pattern."""
        with patch("retrieval_service.get_embedding_generator"):
            with patch("retrieval_service.get_vector_store"):
                retriever1 = get_retriever(top_k=5)
                retriever2 = get_retriever(top_k=10)

                # Should return same instance
                assert retriever1 is retriever2


class TestRetrieverIntegration:
    """Integration tests for retriever."""

    @patch("retrieval_service.get_embedding_generator")
    @patch("retrieval_service.get_vector_store")
    def test_full_retrieval_workflow(self, mock_vs, mock_emb):
        """Test full retrieval workflow: query -> embed -> search -> rank."""
        # Setup mocks
        mock_embeddings = MagicMock()
        mock_vector_store = MagicMock()

        mock_emb.return_value = mock_embeddings
        mock_vs.return_value = mock_vector_store

        mock_embeddings.embed_text.return_value = [0.1] * 1536
        mock_embeddings.estimate_tokens.return_value = 5

        # Simulate search results with various similarity scores
        mock_vector_store.query_vectors.return_value = [
            {
                "similarity_score": 0.98,
                "metadata": {
                    "doc_id": f"doc_{i:03d}",
                    "chapter": f"Module {(i // 5) + 1}",
                    "section": f"Section {i % 5}",
                    "chunk_index": i,
                    "book_version": "v1.0",
                },
                "content": f"Content for chunk {i}",
            }
            for i in range(10)
        ]

        retriever = RetrieverAgent(top_k=3, min_similarity=0.7)
        retriever.embeddings = mock_embeddings
        retriever.vector_store = mock_vector_store

        chunks, metadata = retriever.retrieve("Tell me about ROS 2")

        # Should get top 3 results
        assert len(chunks) <= 3
        assert all(chunk.similarity_score >= 0.7 for chunk in chunks)
        assert metadata["chunks_retrieved"] > 0

    @patch("retrieval_service.get_embedding_generator")
    @patch("retrieval_service.get_vector_store")
    def test_context_assembly_formatting(self, mock_vs, mock_emb):
        """Test context assembly with proper formatting."""
        mock_embeddings = MagicMock()
        mock_vector_store = MagicMock()

        mock_emb.return_value = mock_embeddings
        mock_vs.return_value = mock_vector_store

        mock_embeddings.embed_text.return_value = [0.1] * 1536
        mock_embeddings.estimate_tokens.return_value = 5

        mock_vector_store.query_vectors.return_value = [
            {
                "similarity_score": 0.95,
                "metadata": {
                    "doc_id": "doc_001",
                    "chapter": "Chapter 1",
                    "section": "Intro",
                    "subsection": "Background",
                    "chunk_index": 0,
                    "book_version": "v1.0",
                },
                "content": "Background information here.",
            },
            {
                "similarity_score": 0.88,
                "metadata": {
                    "doc_id": "doc_002",
                    "chapter": "Chapter 1",
                    "section": "Basics",
                    "chunk_index": 1,
                    "book_version": "v1.0",
                },
                "content": "Basic concepts here.",
            },
        ]

        retriever = RetrieverAgent(top_k=5, min_similarity=0.5)
        retriever.embeddings = mock_embeddings
        retriever.vector_store = mock_vector_store

        context, metadata = retriever.retrieve_with_context("What is this?")

        # Check formatting
        assert "[Source 1:" in context
        assert "[Source 2:" in context
        assert "Chapter 1 > Intro > Background" in context
        assert "Chapter 1 > Basics" in context
        assert "Background information here." in context
        assert "Basic concepts here." in context
        assert "sim: 0.95" in context
        assert "sim: 0.88" in context

    @patch("retrieval_service.get_embedding_generator")
    @patch("retrieval_service.get_vector_store")
    def test_multiversion_retrieval(self, mock_vs, mock_emb):
        """Test retrieval across different book versions."""
        mock_embeddings = MagicMock()
        mock_vector_store = MagicMock()

        mock_emb.return_value = mock_embeddings
        mock_vs.return_value = mock_vector_store

        mock_embeddings.embed_text.return_value = [0.1] * 1536
        mock_embeddings.estimate_tokens.return_value = 5

        mock_vector_store.query_vectors.return_value = [
            {
                "similarity_score": 0.92,
                "metadata": {
                    "doc_id": "doc_001",
                    "chapter": "Module 1",
                    "section": "Intro",
                    "chunk_index": 0,
                    "book_version": "v2.0",
                },
                "content": "Updated content for v2.0",
            },
        ]

        retriever = RetrieverAgent(top_k=5, min_similarity=0.5)
        retriever.embeddings = mock_embeddings
        retriever.vector_store = mock_vector_store

        chunks, metadata = retriever.retrieve(
            "What is new?",
            book_version="v2.0",
        )

        assert len(chunks) == 1
        assert chunks[0].book_version == "v2.0"
        assert metadata["book_version"] == "v2.0"
