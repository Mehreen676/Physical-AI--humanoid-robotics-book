"""
Tests for /query Endpoint.
Integration tests for the full RAG query workflow.
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from main import app


class TestQueryEndpoint:
    """Test the /query endpoint."""

    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)

    @patch("main.get_retriever")
    @patch("main.get_generation_agent")
    @patch("main.get_session")
    @patch("main.add_session")
    @patch("main.add_message")
    def test_query_full_book_mode(
        self,
        mock_add_msg,
        mock_add_sess,
        mock_get_sess,
        mock_gen_agent,
        mock_retriever,
        client,
    ):
        """Test /query endpoint in full-book mode."""
        # Mock retriever
        mock_chunk = MagicMock()
        mock_chunk.doc_id = "doc_001"
        mock_chunk.chapter = "Chapter 1"
        mock_chunk.section = "Introduction"
        mock_chunk.subsection = None
        mock_chunk.content = "ROS 2 is a robotics middleware"
        mock_chunk.similarity_score = 0.95

        mock_retriever.return_value.retrieve.return_value = (
            [mock_chunk],
            {"chunks_retrieved": 1},
        )

        # Mock generation
        mock_generated = MagicMock()
        mock_generated.content = "ROS 2 is a flexible middleware for robotics."
        mock_generated.input_tokens = 200
        mock_generated.output_tokens = 50

        mock_gen_agent.return_value.generate.return_value = mock_generated

        # Mock database
        mock_get_sess.return_value = None
        mock_add_sess.return_value = MagicMock()

        # Make request
        response = client.post(
            "/query",
            json={
                "query": "What is ROS 2?",
                "mode": "full_book",
                "book_version": "v1.0",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "response" in data
        assert data["response"] == "ROS 2 is a flexible middleware for robotics."
        assert "sources" in data
        assert len(data["sources"]) == 1
        assert data["mode"] == "full_book"
        assert data["input_tokens"] == 200
        assert data["output_tokens"] == 50
        assert data["latency_ms"] > 0

    @patch("main.get_retriever")
    @patch("main.get_generation_agent")
    @patch("main.get_session")
    @patch("main.add_session")
    @patch("main.add_message")
    def test_query_selected_text_mode(
        self,
        mock_add_msg,
        mock_add_sess,
        mock_get_sess,
        mock_gen_agent,
        mock_retriever,
        client,
    ):
        """Test /query endpoint in selected-text mode."""
        # Mock retriever
        mock_chunk = MagicMock()
        mock_chunk.doc_id = "doc_001"
        mock_chunk.chapter = "Chapter 1"
        mock_chunk.section = "Intro"
        mock_chunk.subsection = "Background"
        mock_chunk.content = "Some content here"
        mock_chunk.similarity_score = 0.88

        mock_retriever.return_value.retrieve.return_value = (
            [mock_chunk],
            {"chunks_retrieved": 1},
        )

        # Mock generation
        mock_generated = MagicMock()
        mock_generated.content = "Explanation of the highlighted text."
        mock_generated.input_tokens = 150
        mock_generated.output_tokens = 40

        mock_gen_agent.return_value.generate.return_value = mock_generated

        # Mock database
        mock_get_sess.return_value = None
        mock_add_sess.return_value = MagicMock()

        # Make request
        response = client.post(
            "/query",
            json={
                "query": "Explain this more",
                "selected_text": "Some content here",
                "mode": "selected_text",
                "book_version": "v1.0",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["mode"] == "selected_text"
        assert "sources" in data
        assert len(data["sources"]) == 1
        # Verify selected-text was passed to generator
        call_kwargs = mock_gen_agent.return_value.generate.call_args.kwargs
        assert call_kwargs["selected_text"] == "Some content here"

    @patch("main.get_retriever")
    def test_query_empty_query(self, mock_retriever, client):
        """Test /query with empty query."""
        response = client.post(
            "/query",
            json={
                "query": "",
                "mode": "full_book",
            },
        )

        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    @patch("main.get_retriever")
    @patch("main.get_generation_agent")
    def test_query_no_results(
        self, mock_gen_agent, mock_retriever, client
    ):
        """Test /query when no chunks are retrieved."""
        # Return empty results
        mock_retriever.return_value.retrieve.return_value = (
            [],
            {"chunks_retrieved": 0},
        )

        response = client.post(
            "/query",
            json={
                "query": "Something obscure",
                "mode": "full_book",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "couldn't find" in data["response"].lower()
        assert len(data["sources"]) == 0

    @patch("main.get_retriever")
    @patch("main.get_generation_agent")
    @patch("main.get_session")
    @patch("main.add_session")
    @patch("main.add_message")
    def test_query_with_chapter_filter(
        self,
        mock_add_msg,
        mock_add_sess,
        mock_get_sess,
        mock_gen_agent,
        mock_retriever,
        client,
    ):
        """Test /query with chapter filter."""
        # Mock retriever
        mock_chunk = MagicMock()
        mock_chunk.doc_id = "doc_001"
        mock_chunk.chapter = "Module 1"
        mock_chunk.section = "Basics"
        mock_chunk.subsection = None
        mock_chunk.content = "Content from Module 1"
        mock_chunk.similarity_score = 0.92

        mock_retriever.return_value.retrieve.return_value = (
            [mock_chunk],
            {"chunks_retrieved": 1},
        )

        # Mock generation
        mock_generated = MagicMock()
        mock_generated.content = "Answer from Module 1"
        mock_generated.input_tokens = 100
        mock_generated.output_tokens = 30

        mock_gen_agent.return_value.generate.return_value = mock_generated

        # Mock database
        mock_get_sess.return_value = None
        mock_add_sess.return_value = MagicMock()

        # Make request with chapter filter
        response = client.post(
            "/query",
            json={
                "query": "Tell me about Module 1",
                "chapter_filter": "Module 1",
                "mode": "full_book",
            },
        )

        assert response.status_code == 200

        # Verify chapter filter was passed to retriever
        call_kwargs = mock_retriever.return_value.retrieve.call_args.kwargs
        assert call_kwargs["chapter_filter"] == "Module 1"

    @patch("main.get_retriever")
    @patch("main.get_generation_agent")
    @patch("main.get_session")
    @patch("main.add_session")
    @patch("main.add_message")
    def test_query_custom_top_k(
        self,
        mock_add_msg,
        mock_add_sess,
        mock_get_sess,
        mock_gen_agent,
        mock_retriever,
        client,
    ):
        """Test /query with custom top_k parameter."""
        # Mock retriever with multiple chunks
        chunks = []
        for i in range(10):
            chunk = MagicMock()
            chunk.doc_id = f"doc_{i:03d}"
            chunk.chapter = f"Chapter {i // 3}"
            chunk.section = f"Section {i % 3}"
            chunk.subsection = None
            chunk.content = f"Content {i}"
            chunk.similarity_score = 0.9 - (i * 0.01)
            chunks.append(chunk)

        mock_retriever.return_value.retrieve.return_value = (
            chunks,
            {"chunks_retrieved": 10},
        )

        # Mock generation
        mock_generated = MagicMock()
        mock_generated.content = "Answer with 10 sources"
        mock_generated.input_tokens = 500
        mock_generated.output_tokens = 100

        mock_gen_agent.return_value.generate.return_value = mock_generated

        # Mock database
        mock_get_sess.return_value = None
        mock_add_sess.return_value = MagicMock()

        # Make request with custom top_k
        response = client.post(
            "/query",
            json={
                "query": "Tell me everything",
                "top_k": 10,
                "mode": "full_book",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["sources"]) == 10

    @patch("main.get_retriever")
    @patch("main.get_generation_agent")
    @patch("main.get_session")
    @patch("main.add_session")
    @patch("main.add_message")
    def test_query_response_structure(
        self,
        mock_add_msg,
        mock_add_sess,
        mock_get_sess,
        mock_gen_agent,
        mock_retriever,
        client,
    ):
        """Test that /query response has correct structure."""
        # Mock retriever
        mock_chunk = MagicMock()
        mock_chunk.doc_id = "doc_001"
        mock_chunk.chapter = "Chapter 1"
        mock_chunk.section = "Section 1"
        mock_chunk.subsection = None
        mock_chunk.content = "This is a longer piece of content that should be truncated" * 50
        mock_chunk.similarity_score = 0.95

        mock_retriever.return_value.retrieve.return_value = (
            [mock_chunk],
            {"chunks_retrieved": 1},
        )

        # Mock generation
        mock_generated = MagicMock()
        mock_generated.content = "Generated response text"
        mock_generated.input_tokens = 150
        mock_generated.output_tokens = 40

        mock_gen_agent.return_value.generate.return_value = mock_generated

        # Mock database
        mock_get_sess.return_value = None
        mock_add_sess.return_value = MagicMock()

        # Make request
        response = client.post(
            "/query",
            json={
                "query": "What is this?",
                "mode": "full_book",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert isinstance(data["response"], str)
        assert isinstance(data["sources"], list)
        assert isinstance(data["latency_ms"], int)
        assert isinstance(data["mode"], str)
        assert isinstance(data["input_tokens"], int)
        assert isinstance(data["output_tokens"], int)

        # Verify source structure
        for source in data["sources"]:
            assert "doc_id" in source
            assert "chapter" in source
            assert "section" in source
            assert "similarity_score" in source
            assert "content" in source
            # Content should be truncated to 200 chars
            assert len(source["content"]) <= 200

    @patch("main.get_retriever")
    @patch("main.get_generation_agent")
    def test_query_database_failure_handling(
        self,
        mock_gen_agent,
        mock_retriever,
        client,
    ):
        """Test that /query continues even if database storage fails."""
        # Mock retriever
        mock_chunk = MagicMock()
        mock_chunk.doc_id = "doc_001"
        mock_chunk.chapter = "Chapter 1"
        mock_chunk.section = "Section 1"
        mock_chunk.subsection = None
        mock_chunk.content = "Content"
        mock_chunk.similarity_score = 0.95

        mock_retriever.return_value.retrieve.return_value = (
            [mock_chunk],
            {"chunks_retrieved": 1},
        )

        # Mock generation
        mock_generated = MagicMock()
        mock_generated.content = "Response"
        mock_generated.input_tokens = 100
        mock_generated.output_tokens = 30

        mock_gen_agent.return_value.generate.return_value = mock_generated

        with patch("main.get_session") as mock_get_sess:
            with patch("main.add_session") as mock_add_sess:
                with patch("main.add_message") as mock_add_msg:
                    # Make database calls fail
                    mock_add_msg.side_effect = Exception("Database error")

                    # Request should still succeed
                    response = client.post(
                        "/query",
                        json={
                            "query": "Test",
                            "mode": "full_book",
                        },
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["response"] == "Response"
