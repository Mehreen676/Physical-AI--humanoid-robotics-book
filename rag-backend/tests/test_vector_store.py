"""
Tests for Qdrant Vector Store Integration.
Uses mock client to avoid requiring live Qdrant instance.
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestQdrantVectorStore:
    """Test Qdrant vector store operations."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings configuration."""
        mock_settings = Mock()
        mock_settings.qdrant_url = "https://test.qdrant.io"
        mock_settings.qdrant_api_key = "test-key"
        mock_settings.qdrant_collection_name = "book_v1.0_chapters"
        return mock_settings

    @pytest.fixture
    def mock_vector_store(self, mock_settings):
        """Create mock vector store for testing."""
        with patch(
            "vector_store.get_settings", return_value=mock_settings
        ):
            with patch("vector_store.QdrantClient"):
                from vector_store import QdrantVectorStore

                store = QdrantVectorStore()
                store.client = MagicMock()
                return store

    def test_create_collection(self, mock_vector_store):
        """Test collection creation."""
        mock_vector_store.client.get_collection.side_effect = Exception(
            "Not found"
        )
        mock_vector_store.client.create_collection.return_value = True

        result = mock_vector_store.create_collection()

        assert result is True
        mock_vector_store.client.create_collection.assert_called_once()

    def test_store_vector(self, mock_vector_store):
        """Test storing a single vector."""
        mock_vector_store.client.upsert.return_value = None

        vector_id = "chunk_123"
        embedding = [0.1] * 1536
        metadata = {
            "chapter": "Module 1",
            "section": "Basics",
            "content": "ROS 2 is...",
        }

        result = mock_vector_store.store_vector(vector_id, embedding, metadata)

        assert result is True
        mock_vector_store.client.upsert.assert_called_once()

    def test_store_vectors_batch(self, mock_vector_store):
        """Test storing multiple vectors in batch."""
        mock_vector_store.client.upsert.return_value = None

        vectors_data = [
            ("id_1", [0.1] * 1536, {"chapter": "Ch1"}),
            ("id_2", [0.2] * 1536, {"chapter": "Ch2"}),
            ("id_3", [0.3] * 1536, {"chapter": "Ch3"}),
        ]

        result = mock_vector_store.store_vectors_batch(vectors_data)

        assert result == 3
        mock_vector_store.client.upsert.assert_called_once()

    def test_query_vectors(self, mock_vector_store):
        """Test semantic similarity search."""
        # Mock search results
        mock_result_1 = Mock()
        mock_result_1.id = 1
        mock_result_1.score = 0.92
        mock_result_1.payload = {
            "chapter": "Module 1",
            "section": "Basics",
            "content": "ROS 2 is a robotics middleware...",
        }

        mock_result_2 = Mock()
        mock_result_2.id = 2
        mock_result_2.score = 0.87
        mock_result_2.payload = {
            "chapter": "Module 2",
            "section": "Advanced",
            "content": "Distributed systems...",
        }

        mock_vector_store.client.search.return_value = [
            mock_result_1,
            mock_result_2,
        ]

        query_embedding = [0.15] * 1536
        results = mock_vector_store.query_vectors(query_embedding, k=5)

        assert len(results) == 2
        assert results[0]["score"] == 0.92
        assert results[0]["chapter"] == "Module 1"
        assert results[1]["score"] == 0.87

    def test_query_vectors_with_filters(self, mock_vector_store):
        """Test semantic search with metadata filters."""
        mock_result = Mock()
        mock_result.id = 1
        mock_result.score = 0.88
        mock_result.payload = {"chapter": "Module 1"}

        mock_vector_store.client.search.return_value = [mock_result]

        query_embedding = [0.15] * 1536
        filters = {"chapter": {"$eq": "Module 1"}}

        results = mock_vector_store.query_vectors(query_embedding, filters=filters)

        assert len(results) == 1
        mock_vector_store.client.search.assert_called_with(
            collection_name="book_v1.0_chapters",
            query_vector=query_embedding,
            limit=5,
            query_filter=filters,
        )

    def test_get_collection_info(self, mock_vector_store):
        """Test retrieving collection statistics."""
        mock_collection = Mock()
        mock_collection.points_count = 1250
        mock_vector_store.client.get_collection.return_value = mock_collection

        info = mock_vector_store.get_collection_info()

        assert info["name"] == "book_v1.0_chapters"
        assert info["points_count"] == 1250
        assert info["vector_size"] == 1536
        assert info["distance_metric"] == "cosine"

    def test_delete_collection(self, mock_vector_store):
        """Test collection deletion."""
        mock_vector_store.client.delete_collection.return_value = None

        result = mock_vector_store.delete_collection()

        assert result is True
        mock_vector_store.client.delete_collection.assert_called_once_with(
            "book_v1.0_chapters"
        )

    def test_vector_dimensions(self):
        """Test that vector dimension matches OpenAI embedding model."""
        from vector_store import EMBEDDING_DIMENSION

        assert EMBEDDING_DIMENSION == 1536
