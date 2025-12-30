"""
Unit tests for Qdrant retrieval.

Tests vector search, metadata preservation, and health checks.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from backend.rag.retrieval import QdrantRetriever


@pytest.fixture
def qdrant_retriever():
    """Create Qdrant retriever for testing."""
    with patch("backend.rag.retrieval.QdrantClient"):
        return QdrantRetriever(
            qdrant_url="https://test.qdrant.io",
            api_key="test-api-key",
            collection_name="test-collection"
        )


class TestQdrantRetriever:
    """Test cases for QdrantRetriever."""

    @pytest.mark.asyncio
    async def test_search_success(self, qdrant_retriever):
        """Test successful vector search."""
        # Mock search results
        mock_result = MagicMock()
        mock_result.score = 0.87
        mock_result.payload = {
            "text": "Chapter 3 covers neural networks",
            "url": "https://example.com/chapter-3",
            "section": "Chapter 3: Neural Networks",
            "chunk_id": "chunk-042",
            "position": 1
        }

        qdrant_retriever.client.search = MagicMock(return_value=[mock_result])

        # Perform search
        query_vector = [0.1] * 1280
        results = await qdrant_retriever.search(
            query_vector=query_vector,
            top_k=5,
            threshold=0.7
        )

        # Verify results
        assert len(results) == 1
        assert results[0]["text"] == "Chapter 3 covers neural networks"
        assert results[0]["metadata"]["embedding_score"] == 0.87
        assert results[0]["metadata"]["chunk_id"] == "chunk-042"

    @pytest.mark.asyncio
    async def test_search_metadata_preservation(self, qdrant_retriever):
        """Test that metadata is preserved during search."""
        mock_result = MagicMock()
        mock_result.score = 0.92
        mock_result.payload = {
            "text": "Sample text",
            "url": "https://example.com/page",
            "section": "Chapter 1",
            "chunk_id": "chunk-001",
            "position": 42
        }

        qdrant_retriever.client.search = MagicMock(return_value=[mock_result])

        results = await qdrant_retriever.search(
            query_vector=[0.1] * 1280,
            top_k=1
        )

        assert results[0]["metadata"]["url"] == "https://example.com/page"
        assert results[0]["metadata"]["section"] == "Chapter 1"
        assert results[0]["metadata"]["position"] == 42

    @pytest.mark.asyncio
    async def test_search_empty_results(self, qdrant_retriever):
        """Test search with no results above threshold."""
        qdrant_retriever.client.search = MagicMock(return_value=[])

        results = await qdrant_retriever.search(
            query_vector=[0.1] * 1280,
            top_k=5,
            threshold=0.9
        )

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_multiple_results(self, qdrant_retriever):
        """Test search returning multiple results."""
        mock_results = []
        for i in range(3):
            result = MagicMock()
            result.score = 0.85 - (i * 0.05)
            result.payload = {
                "text": f"Chunk {i}",
                "url": f"https://example.com/{i}",
                "section": f"Section {i}",
                "chunk_id": f"chunk-{i:03d}",
                "position": i
            }
            mock_results.append(result)

        qdrant_retriever.client.search = MagicMock(return_value=mock_results)

        results = await qdrant_retriever.search(
            query_vector=[0.1] * 1280,
            top_k=5
        )

        assert len(results) == 3
        assert results[0]["metadata"]["chunk_id"] == "chunk-000"
        assert results[2]["metadata"]["chunk_id"] == "chunk-002"

    @pytest.mark.asyncio
    async def test_search_error(self, qdrant_retriever):
        """Test error handling during search."""
        qdrant_retriever.client.search = MagicMock(
            side_effect=Exception("Connection failed")
        )

        with pytest.raises(Exception) as exc_info:
            await qdrant_retriever.search(
                query_vector=[0.1] * 1280
            )

        assert "Connection failed" in str(exc_info.value)

    def test_health_check_success(self, qdrant_retriever):
        """Test health check on working Qdrant."""
        qdrant_retriever.client.get_collection_info = MagicMock(
            return_value={"status": "ok"}
        )

        result = qdrant_retriever.health_check()

        assert result["status"] == "ok"

    def test_health_check_failure(self, qdrant_retriever):
        """Test health check on failing Qdrant."""
        qdrant_retriever.client.get_collection_info = MagicMock(
            side_effect=Exception("Collection not found")
        )

        result = qdrant_retriever.health_check()

        assert result["status"] == "error"
        assert "Collection not found" in result["message"]

    def test_create_collection(self, qdrant_retriever):
        """Test collection creation."""
        qdrant_retriever.client.recreate_collection = MagicMock()

        result = qdrant_retriever.create_collection(
            vector_size=1280,
            distance="cosine"
        )

        assert result is True
        qdrant_retriever.client.recreate_collection.assert_called_once()
