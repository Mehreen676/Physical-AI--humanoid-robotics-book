"""
Unit tests for Embeddings service.

Tests embedding generation, batch processing, and error handling.
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from backend.services.embeddings import EmbeddingsService


@pytest.fixture
def embeddings_service():
    """Create embeddings service for testing."""
    return EmbeddingsService(
        provider="cohere",
        api_key="test-api-key"
    )


class TestEmbeddingsService:
    """Test cases for EmbeddingsService."""

    def test_init_missing_api_key(self):
        """Test initialization fails without API key."""
        with pytest.raises(ValueError) as exc_info:
            EmbeddingsService(provider="cohere", api_key=None)

        assert "API key" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_embed_single_text(self, embeddings_service):
        """Test embedding a single text."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embeddings": [[0.1, 0.2, 0.3, 0.4, 0.5]]
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await embeddings_service.embed("test text")

            assert isinstance(result, list)
            assert len(result) == 5
            assert result[0] == 0.1

    @pytest.mark.asyncio
    async def test_embed_batch(self, embeddings_service):
        """Test embedding multiple texts."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embeddings": [
                [0.1, 0.2, 0.3],
                [0.4, 0.5, 0.6],
                [0.7, 0.8, 0.9]
            ]
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await embeddings_service.embed_batch(["text1", "text2", "text3"])

            assert len(result) == 3
            assert len(result[0]) == 3
            assert result[0][0] == 0.1
            assert result[2][2] == 0.9

    @pytest.mark.asyncio
    async def test_embed_api_error(self, embeddings_service):
        """Test handling of API errors."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Invalid API key"

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(Exception) as exc_info:
                await embeddings_service.embed("test")

            assert "API error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_embed_timeout(self, embeddings_service):
        """Test timeout handling."""
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Timeout")

            with pytest.raises(Exception) as exc_info:
                await embeddings_service.embed("test")

            assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_embed_invalid_response(self, embeddings_service):
        """Test invalid response format."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # Missing embeddings

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            # Should still return empty list or handle gracefully
            with pytest.raises(Exception):
                result = await embeddings_service.embed("test")

    @pytest.mark.asyncio
    async def test_health_check_success(self, embeddings_service):
        """Test health check on working service."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embeddings": [[0.1, 0.2, 0.3]]
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await embeddings_service.health_check()

            assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health_check_failure(self, embeddings_service):
        """Test health check on failing service."""
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = Exception("Connection failed")

            result = await embeddings_service.health_check()

            assert result["status"] == "error"
            assert "Connection failed" in result["message"]

    def test_unsupported_provider(self):
        """Test initialization with unsupported provider."""
        with pytest.raises(ValueError) as exc_info:
            EmbeddingsService(provider="unsupported", api_key="key")

        # This would happen on embed(), not init, since we just store the provider
