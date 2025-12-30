"""
Unit tests for OpenRouter service.

Tests LLM API calls, error handling, and timeouts.
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from backend.services.openrouter_service import OpenRouterClient


@pytest.fixture
def openrouter_client():
    """Create OpenRouter client for testing."""
    return OpenRouterClient(
        api_key="test-api-key",
        model_name="claude-3-5-sonnet",
        base_url="https://api.openrouter.io/api/v1"
    )


class TestOpenRouterClient:
    """Test cases for OpenRouterClient."""

    @pytest.mark.asyncio
    async def test_call_success(self, openrouter_client):
        """Test successful LLM call."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "This is a test response"
                }
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await openrouter_client.call(
                prompt="Test prompt",
                temperature=0.7,
                max_tokens=100
            )

            assert result["content"] == "This is a test response"
            assert result["usage"]["total_tokens"] == 15

    @pytest.mark.asyncio
    async def test_call_api_error(self, openrouter_client):
        """Test API error response."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Invalid API key"

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(Exception) as exc_info:
                await openrouter_client.call(prompt="Test")

            assert "API error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_call_timeout(self, openrouter_client):
        """Test timeout handling."""
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Timeout")

            with pytest.raises(Exception) as exc_info:
                await openrouter_client.call(prompt="Test")

            assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_call_invalid_response(self, openrouter_client):
        """Test invalid response format."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # Missing expected fields

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(Exception) as exc_info:
                await openrouter_client.call(prompt="Test")

            assert "response format" in str(exc_info.value).lower() or "key" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_health_check_success(self, openrouter_client):
        """Test health check on working API."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {"content": "ok"}
            }],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await openrouter_client.health_check()

            assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health_check_failure(self, openrouter_client):
        """Test health check on failing API."""
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = Exception("Connection failed")

            result = await openrouter_client.health_check()

            assert result["status"] == "error"
            assert "Connection failed" in result["message"]
