"""
Tests for Embedding Generation Module.
Uses mock OpenAI API to avoid requiring actual API calls.
"""

import pytest
import sys
import os
import math
from unittest.mock import Mock, MagicMock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestEmbeddingGenerator:
    """Test Embedding Generator functionality."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings configuration."""
        mock_settings = Mock()
        mock_settings.openai_api_key = "sk-test-key"
        mock_settings.openai_embedding_model = "text-embedding-3-small"
        return mock_settings

    @pytest.fixture
    def mock_generator(self, mock_settings):
        """Create mock embedding generator for testing."""
        with patch("embeddings.get_settings", return_value=mock_settings):
            with patch("embeddings.OpenAI"):
                from embeddings import EmbeddingGenerator

                gen = EmbeddingGenerator()
                gen.client = MagicMock()
                return gen

    def test_embed_text_single(self, mock_generator):
        """Test embedding a single text."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3] + [0.0] * 1533)]
        mock_response.usage.prompt_tokens = 10

        mock_generator.client.embeddings.create.return_value = mock_response

        text = "Hello, this is a test text."
        embedding = mock_generator.embed_text(text)

        assert len(embedding) == 1536
        assert embedding[0] == 0.1
        assert embedding[1] == 0.2
        mock_generator.client.embeddings.create.assert_called_once()

    def test_embed_texts_batch(self, mock_generator):
        """Test embedding multiple texts in one call."""
        # Mock OpenAI response for batch
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1] * 1536),
            Mock(embedding=[0.2] * 1536),
            Mock(embedding=[0.3] * 1536),
        ]
        mock_response.usage.prompt_tokens = 50

        mock_generator.client.embeddings.create.return_value = mock_response

        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = mock_generator.embed_texts(texts)

        assert len(embeddings) == 3
        assert all(len(emb) == 1536 for emb in embeddings)
        assert embeddings[0][0] == 0.1
        assert embeddings[1][0] == 0.2
        mock_generator.client.embeddings.create.assert_called_once()

    def test_embed_texts_empty_list(self, mock_generator):
        """Test that empty list raises error."""
        with pytest.raises(ValueError, match="No texts provided"):
            mock_generator.embed_texts([])

    def test_embed_texts_too_many(self, mock_generator):
        """Test that >2048 texts raises error."""
        texts = ["Text"] * 2049
        with pytest.raises(ValueError, match="Too many texts"):
            mock_generator.embed_texts(texts)

    def test_cosine_similarity_identical(self, mock_generator):
        """Test cosine similarity of identical vectors."""
        vec = [0.2, 0.4, 0.6, 0.8]
        similarity = mock_generator.cosine_similarity(vec, vec)
        assert abs(similarity - 1.0) < 0.0001  # Should be 1.0

    def test_cosine_similarity_orthogonal(self, mock_generator):
        """Test cosine similarity of orthogonal vectors."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = mock_generator.cosine_similarity(vec1, vec2)
        assert abs(similarity - 0.0) < 0.0001  # Should be 0.0

    def test_cosine_similarity_opposite(self, mock_generator):
        """Test cosine similarity of opposite vectors."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [-1.0, 0.0, 0.0]
        similarity = mock_generator.cosine_similarity(vec1, vec2)
        assert abs(similarity - (-1.0)) < 0.0001  # Should be -1.0

    def test_cosine_similarity_zero_vector(self, mock_generator):
        """Test cosine similarity with zero vector."""
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = mock_generator.cosine_similarity(vec1, vec2)
        assert similarity == 0.0

    def test_embedding_dimension(self, mock_generator):
        """Test that embeddings have correct dimension."""
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.5] * 1536)]
        mock_response.usage.prompt_tokens = 10

        mock_generator.client.embeddings.create.return_value = mock_response

        embedding = mock_generator.embed_text("Test")
        assert len(embedding) == 1536
        assert mock_generator.EMBEDDING_DIMENSION == 1536

    def test_cost_tracking(self, mock_generator):
        """Test token usage and cost tracking."""
        mock_generator.reset_token_counter()

        # Mock first call with significant token count
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        mock_response.usage.prompt_tokens = 10000  # 10K tokens

        mock_generator.client.embeddings.create.return_value = mock_response

        # Generate embedding
        mock_generator.embed_text("Test text")

        cost_info = mock_generator.get_cost_estimate()
        assert cost_info["input_tokens"] == 10000
        assert cost_info["total_tokens"] == 10000
        # 10000 tokens * $0.02/1M = $0.0002
        assert cost_info["estimated_cost_usd"] >= 0.0002

    def test_cost_estimate_multiple_calls(self, mock_generator):
        """Test cost estimate with multiple API calls."""
        mock_generator.reset_token_counter()

        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]

        # First call: 100 tokens
        mock_response.usage.prompt_tokens = 100
        mock_generator.client.embeddings.create.return_value = mock_response
        mock_generator.embed_text("First text")

        # Second call: 200 tokens
        mock_response.usage.prompt_tokens = 200
        mock_generator.client.embeddings.create.return_value = mock_response
        mock_generator.embed_text("Second text")

        cost_info = mock_generator.get_cost_estimate()
        assert cost_info["input_tokens"] == 300
        assert cost_info["total_tokens"] == 300

    def test_price_calculation_accuracy(self, mock_generator):
        """Test price calculation is accurate."""
        mock_generator.reset_token_counter()

        # 1 million tokens
        cost_per_1m = mock_generator.PRICE_PER_1M_INPUT_TOKENS  # $0.02

        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        mock_response.usage.prompt_tokens = 1_000_000

        mock_generator.client.embeddings.create.return_value = mock_response
        mock_generator.embed_text("Large text")

        cost_info = mock_generator.get_cost_estimate()
        assert cost_info["estimated_cost_usd"] == cost_per_1m

    def test_token_counter_reset(self, mock_generator):
        """Test resetting token counter."""
        mock_generator.reset_token_counter()

        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        mock_response.usage.prompt_tokens = 100

        mock_generator.client.embeddings.create.return_value = mock_response
        mock_generator.embed_text("Test")

        cost_before = mock_generator.get_cost_estimate()
        assert cost_before["input_tokens"] == 100

        mock_generator.reset_token_counter()
        cost_after = mock_generator.get_cost_estimate()
        assert cost_after["input_tokens"] == 0


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings configuration."""
        mock_settings = Mock()
        mock_settings.openai_api_key = "sk-test-key"
        mock_settings.openai_embedding_model = "text-embedding-3-small"
        return mock_settings

    @patch("embeddings._embedding_generator_instance", None)
    def test_embed_text_function(self, mock_settings):
        """Test embed_text convenience function."""
        with patch("embeddings.get_settings", return_value=mock_settings):
            with patch("embeddings.OpenAI"):
                from embeddings import embed_text, get_embedding_generator

                gen = get_embedding_generator()
                gen.client = MagicMock()

                mock_response = Mock()
                mock_response.data = [Mock(embedding=[0.1] * 1536)]
                mock_response.usage.prompt_tokens = 10

                gen.client.embeddings.create.return_value = mock_response

                embedding = embed_text("Test text")
                assert len(embedding) == 1536
