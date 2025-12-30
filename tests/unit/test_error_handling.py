"""
Unit tests for Error Handling and Graceful Fallbacks (Phase 6).

Tests error scenarios, service failures, and graceful degradation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from backend.models.schemas import ChatRequest, ChatResponse
from backend.utils.errors import (
    RAGError, HallucinationDetectedException, RetrievalFailedException,
    ServiceUnavailableException, InvalidInputException, SessionNotFoundException,
    ConfigurationException, build_error_response, get_http_status_code
)
from backend.agent.agent import BookRAGAgent


class TestErrorClasses:
    """Test custom error classes."""

    def test_rag_error_initialization(self):
        """Test RAGError initialization and properties."""
        error = RAGError("Test error", http_status=500)
        assert error.message == "Test error"
        assert error.http_status == 500
        assert str(error) == "Test error"

    def test_hallucination_detected_error(self):
        """Test HallucinationDetectedException."""
        error = HallucinationDetectedException()
        assert error.http_status == 400
        assert "hallucination" in str(error).lower()

    def test_retrieval_failed_error(self):
        """Test RetrievalFailedException."""
        error = RetrievalFailedException()
        assert error.http_status == 503
        assert "retrieval" in str(error).lower()

    def test_service_unavailable_error(self):
        """Test ServiceUnavailableException."""
        error = ServiceUnavailableException("Qdrant")
        assert error.http_status == 503
        assert "Qdrant" in str(error)

    def test_invalid_input_error(self):
        """Test InvalidInputException."""
        error = InvalidInputException("Empty question")
        assert error.http_status == 400
        assert "Empty question" in str(error)

    def test_session_not_found_error(self):
        """Test SessionNotFoundException."""
        session_id = str(uuid4())
        error = SessionNotFoundException(session_id)
        assert error.http_status == 404
        assert session_id in str(error)

    def test_configuration_error(self):
        """Test ConfigurationException."""
        error = ConfigurationException("Missing API key")
        assert error.http_status == 500
        assert "Missing API key" in str(error)


class TestErrorResponseBuilding:
    """Test error response construction."""

    def test_build_error_response_rag_error(self):
        """Test building response from RAGError."""
        error = RAGError("Test error", http_status=500)
        response = build_error_response(error)
        assert "error" in response
        assert "message" in response
        assert response["message"] == "Test error"

    def test_build_error_response_generic_exception(self):
        """Test building response from generic exception."""
        error = ValueError("Invalid value")
        response = build_error_response(error)
        assert "error" in response
        assert "message" in response

    def test_get_http_status_code_rag_error(self):
        """Test getting HTTP status from RAGError."""
        error = RetrievalFailedException()
        status = get_http_status_code(error)
        assert status == 503

    def test_get_http_status_code_generic(self):
        """Test getting HTTP status from generic exception."""
        error = ValueError("Test")
        status = get_http_status_code(error)
        assert status == 500


class TestAgentErrorRecovery:
    """Test agent error handling and recovery."""

    @pytest.mark.asyncio
    async def test_agent_retrieval_failure_fallback(self):
        """Test agent returns fallback when retrieval fails."""
        retrieval_agent = AsyncMock()
        answer_agent = AsyncMock()
        guardrails_agent = AsyncMock()

        retrieval_agent.execute = AsyncMock(side_effect=RetrievalFailedException())

        agent = BookRAGAgent(
            retrieval_agent=retrieval_agent,
            answer_agent=answer_agent,
            guardrails_agent=guardrails_agent
        )

        request = ChatRequest(
            question="What is this?",
            session_id=uuid4()
        )

        with pytest.raises(RetrievalFailedException):
            await agent.execute(request)

    @pytest.mark.asyncio
    async def test_agent_hallucination_detected_fallback(self):
        """Test agent returns fallback when hallucination detected."""
        retrieval_agent = AsyncMock()
        answer_agent = AsyncMock()
        guardrails_agent = AsyncMock()

        sample_chunks = [
            {
                "text": "Chapter 1 content",
                "metadata": {
                    "url": "https://example.com/1",
                    "section": "Chapter 1",
                    "chunk_id": "chunk-001",
                    "position": 1,
                    "embedding_score": 0.85
                }
            }
        ]

        retrieval_agent.execute = AsyncMock(return_value=sample_chunks)
        answer_agent.execute = AsyncMock(return_value="Made-up information")
        guardrails_agent.execute = AsyncMock(return_value={
            "approved": False,
            "answer": "Made-up information",
            "veto_reason": "Contains information not in source",
            "chunks": sample_chunks
        })

        agent = BookRAGAgent(
            retrieval_agent=retrieval_agent,
            answer_agent=answer_agent,
            guardrails_agent=guardrails_agent
        )

        request = ChatRequest(
            question="What is this?",
            session_id=uuid4()
        )

        response = await agent.execute(request)

        assert isinstance(response, ChatResponse)
        assert "cannot provide" in response.answer.lower()
        assert len(response.citations) == 0

    @pytest.mark.asyncio
    async def test_agent_empty_chunks_fallback(self):
        """Test agent returns fallback when no chunks retrieved."""
        retrieval_agent = AsyncMock()
        answer_agent = AsyncMock()
        guardrails_agent = AsyncMock()

        retrieval_agent.execute = AsyncMock(return_value=[])

        agent = BookRAGAgent(
            retrieval_agent=retrieval_agent,
            answer_agent=answer_agent,
            guardrails_agent=guardrails_agent
        )

        request = ChatRequest(
            question="What is something very obscure?",
            session_id=uuid4()
        )

        response = await agent.execute(request)

        assert isinstance(response, ChatResponse)
        assert "could not find" in response.answer.lower()
        assert len(response.citations) == 0

    @pytest.mark.asyncio
    async def test_agent_selected_text_mismatch_fallback(self):
        """Test fallback when selected text doesn't match chunks."""
        retrieval_agent = AsyncMock()
        answer_agent = AsyncMock()
        guardrails_agent = AsyncMock()

        sample_chunks = [
            {
                "text": "Neural networks content",
                "metadata": {
                    "url": "https://example.com/nn",
                    "section": "Neural Networks",
                    "chunk_id": "chunk-100",
                    "position": 1,
                    "embedding_score": 0.85
                }
            }
        ]

        retrieval_agent.execute = AsyncMock(return_value=sample_chunks)

        agent = BookRAGAgent(
            retrieval_agent=retrieval_agent,
            answer_agent=answer_agent,
            guardrails_agent=guardrails_agent
        )

        request = ChatRequest(
            question="What about RNNs?",
            session_id=uuid4(),
            selected_text="Something about quantum computers"
        )

        response = await agent.execute(request)

        assert isinstance(response, ChatResponse)
        assert "selected text" in response.answer.lower()


class TestServiceFailureHandling:
    """Test handling of service failures."""

    @pytest.mark.asyncio
    async def test_service_unavailable_during_retrieval(self):
        """Test handling when Qdrant is unavailable."""
        retrieval_agent = AsyncMock()
        answer_agent = AsyncMock()
        guardrails_agent = AsyncMock()

        retrieval_agent.execute = AsyncMock(
            side_effect=ServiceUnavailableException("Qdrant")
        )

        agent = BookRAGAgent(
            retrieval_agent=retrieval_agent,
            answer_agent=answer_agent,
            guardrails_agent=guardrails_agent
        )

        request = ChatRequest(
            question="What is this?",
            session_id=uuid4()
        )

        with pytest.raises(ServiceUnavailableException):
            await agent.execute(request)

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test handling of timeout scenarios."""
        retrieval_agent = AsyncMock()
        answer_agent = AsyncMock()
        guardrails_agent = AsyncMock()

        retrieval_agent.execute = AsyncMock(
            side_effect=TimeoutError("Request timed out")
        )

        agent = BookRAGAgent(
            retrieval_agent=retrieval_agent,
            answer_agent=answer_agent,
            guardrails_agent=guardrails_agent
        )

        request = ChatRequest(
            question="What is this?",
            session_id=uuid4()
        )

        with pytest.raises(TimeoutError):
            await agent.execute(request)


class TestInputValidationAndBounds:
    """Test input validation and boundary checking."""

    @pytest.mark.asyncio
    async def test_oversized_question_handling(self):
        """Test handling of excessively long questions."""
        retrieval_agent = AsyncMock()
        answer_agent = AsyncMock()
        guardrails_agent = AsyncMock()

        agent = BookRAGAgent(
            retrieval_agent=retrieval_agent,
            answer_agent=answer_agent,
            guardrails_agent=guardrails_agent
        )

        # Question is too long (> 500 chars)
        long_question = "a" * 600

        with pytest.raises(Exception):  # Should fail validation
            request = ChatRequest(
                question=long_question,
                session_id=uuid4()
            )

    @pytest.mark.asyncio
    async def test_empty_question_handling(self):
        """Test handling of empty questions."""
        with pytest.raises(Exception):  # Should fail validation
            ChatRequest(
                question="",
                session_id=uuid4()
            )

    @pytest.mark.asyncio
    async def test_whitespace_only_question(self):
        """Test handling of whitespace-only questions."""
        with pytest.raises(Exception):  # Should fail validation
            ChatRequest(
                question="   ",
                session_id=uuid4()
            )


class TestGracefulDegradation:
    """Test graceful degradation when services fail."""

    @pytest.mark.asyncio
    async def test_memory_agent_failure_continues(self):
        """Test that memory agent failure doesn't break pipeline."""
        retrieval_agent = AsyncMock()
        answer_agent = AsyncMock()
        guardrails_agent = AsyncMock()
        memory_agent = AsyncMock()

        # Memory agent fails
        memory_agent.execute = AsyncMock(
            side_effect=Exception("Memory retrieval failed")
        )

        sample_chunks = [
            {
                "text": "Chapter 1 content",
                "metadata": {
                    "url": "https://example.com/1",
                    "section": "Chapter 1",
                    "chunk_id": "chunk-001",
                    "position": 1,
                    "embedding_score": 0.85
                }
            }
        ]

        retrieval_agent.execute = AsyncMock(return_value=sample_chunks)
        answer_agent.execute = AsyncMock(return_value="Answer from Chapter 1")
        guardrails_agent.execute = AsyncMock(return_value={
            "approved": True,
            "answer": "Answer from Chapter 1",
            "chunks": sample_chunks
        })

        agent = BookRAGAgent(
            retrieval_agent=retrieval_agent,
            answer_agent=answer_agent,
            guardrails_agent=guardrails_agent,
            memory_agent=memory_agent
        )

        from backend.agent.sub_agents import SelectionModeSubAgent
        request = ChatRequest(
            question="What is this?",
            session_id=uuid4()
        )

        # Should still work even though memory failed
        # This test verifies the agent catches and handles the error
        response = await agent.execute(request)
        assert isinstance(response, ChatResponse)
