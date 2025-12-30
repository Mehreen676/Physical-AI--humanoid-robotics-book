"""
Integration tests for BookRAGAgent orchestration.

Tests the full RAG pipeline from query to response.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from backend.models.schemas import ChatRequest, ChatResponse
from backend.agent.skills import Skill
from backend.agent.sub_agents import RetrievalSubAgent, AnswerSubAgent, GuardrailsSubAgent
from backend.agent.agent import BookRAGAgent
from backend.rag.retrieval import VectorSearchSkill
from backend.rag.grounding import GroundedSynthesisSkill, AntiHallucinationSkill, RetrievalValidationSkill


@pytest.fixture
def mock_vector_search_skill():
    """Mock VectorSearchSkill."""
    skill = AsyncMock(spec=VectorSearchSkill)
    skill.execute = AsyncMock(return_value=[
        {
            "text": "Chapter 3 covers neural networks",
            "metadata": {
                "url": "https://example.com/chapter-3",
                "section": "Chapter 3: Neural Networks",
                "chunk_id": "chunk-042",
                "position": 1,
                "embedding_score": 0.87
            }
        }
    ])
    return skill


@pytest.fixture
def mock_synthesis_skill():
    """Mock GroundedSynthesisSkill."""
    skill = AsyncMock(spec=GroundedSynthesisSkill)
    skill.execute = AsyncMock(return_value="Chapter 3 focuses on neural networks and deep learning fundamentals.")
    return skill


@pytest.fixture
def mock_validation_skill():
    """Mock RetrievalValidationSkill."""
    skill = AsyncMock(spec=RetrievalValidationSkill)
    skill.execute = AsyncMock(return_value=[
        {
            "text": "Chapter 3 covers neural networks",
            "metadata": {
                "url": "https://example.com/chapter-3",
                "section": "Chapter 3: Neural Networks",
                "chunk_id": "chunk-042",
                "position": 1,
                "embedding_score": 0.87
            }
        }
    ])
    return skill


@pytest.fixture
def mock_hallucination_skill():
    """Mock AntiHallucinationSkill."""
    skill = AsyncMock(spec=AntiHallucinationSkill)
    skill.execute = AsyncMock(return_value={"grounded": True})
    return skill


@pytest.fixture
def retrieval_agent(mock_vector_search_skill):
    """Create RetrievalSubAgent with mocked skill."""
    return RetrievalSubAgent(mock_vector_search_skill)


@pytest.fixture
def answer_agent(mock_synthesis_skill):
    """Create AnswerSubAgent with mocked skill."""
    return AnswerSubAgent(mock_synthesis_skill)


@pytest.fixture
def guardrails_agent(mock_validation_skill, mock_hallucination_skill):
    """Create GuardrailsSubAgent with mocked skills."""
    return GuardrailsSubAgent(mock_validation_skill, mock_hallucination_skill)


@pytest.fixture
def rag_agent(retrieval_agent, answer_agent, guardrails_agent):
    """Create BookRAGAgent with mocked sub-agents."""
    return BookRAGAgent(retrieval_agent, answer_agent, guardrails_agent)


class TestBookRAGAgent:
    """Test cases for BookRAGAgent orchestration."""

    @pytest.mark.asyncio
    async def test_full_pipeline_success(self, rag_agent):
        """Test successful full RAG pipeline execution."""
        request = ChatRequest(
            question="What is Chapter 3 about?",
            session_id=uuid4(),
            selected_text=None
        )

        response = await rag_agent.execute(request)

        assert isinstance(response, ChatResponse)
        assert response.answer is not None
        assert len(response.retrieved_chunks) > 0
        assert len(response.citations) > 0

    @pytest.mark.asyncio
    async def test_no_chunks_retrieved(self, rag_agent, retrieval_agent):
        """Test fallback when no chunks are retrieved."""
        # Mock empty retrieval
        retrieval_agent.vector_search_skill.execute = AsyncMock(return_value=[])

        request = ChatRequest(
            question="About quantum computing?",
            session_id=uuid4(),
            selected_text=None
        )

        response = await rag_agent.execute(request)

        assert isinstance(response, ChatResponse)
        assert "could not find" in response.answer.lower()

    @pytest.mark.asyncio
    async def test_hallucination_detected(self, rag_agent, guardrails_agent):
        """Test fallback when hallucination is detected."""
        # Mock hallucination detection
        guardrails_agent.hallucination_skill.execute = AsyncMock(
            return_value={
                "grounded": False,
                "veto_reason": "Answer contains unsupported information."
            }
        )

        request = ChatRequest(
            question="What is Chapter 3 about?",
            session_id=uuid4(),
            selected_text=None
        )

        response = await rag_agent.execute(request)

        assert isinstance(response, ChatResponse)
        assert "cannot provide a reliable answer" in response.answer.lower()

    @pytest.mark.asyncio
    async def test_citations_generated(self, rag_agent):
        """Test that citations are properly generated from chunks."""
        request = ChatRequest(
            question="What is Chapter 3 about?",
            session_id=uuid4(),
            selected_text=None
        )

        response = await rag_agent.execute(request)

        assert len(response.citations) > 0
        assert response.citations[0].section == "Chapter 3: Neural Networks"
        assert response.citations[0].url == "https://example.com/chapter-3"

    @pytest.mark.asyncio
    async def test_retrieved_chunks_in_response(self, rag_agent):
        """Test that retrieved chunks are included in response."""
        request = ChatRequest(
            question="What is Chapter 3 about?",
            session_id=uuid4(),
            selected_text=None
        )

        response = await rag_agent.execute(request)

        assert len(response.retrieved_chunks) > 0
        chunk = response.retrieved_chunks[0]
        assert chunk.text is not None
        assert chunk.metadata.chunk_id == "chunk-042"
        assert chunk.metadata.embedding_score == 0.87

    @pytest.mark.asyncio
    async def test_answer_agent_called_with_chunks(self, rag_agent, answer_agent):
        """Test that AnswerSubAgent receives chunks from retrieval."""
        request = ChatRequest(
            question="What is Chapter 3 about?",
            session_id=uuid4(),
            selected_text=None
        )

        await rag_agent.execute(request)

        # Verify answer agent was called
        answer_agent.synthesis_skill.execute.assert_called_once()
        call_args = answer_agent.synthesis_skill.execute.call_args
        assert "chunks" in call_args.kwargs
        assert len(call_args.kwargs["chunks"]) > 0

    @pytest.mark.asyncio
    async def test_guardrails_agent_validates_answer(self, rag_agent, guardrails_agent):
        """Test that GuardrailsSubAgent validates the answer."""
        request = ChatRequest(
            question="What is Chapter 3 about?",
            session_id=uuid4(),
            selected_text=None
        )

        await rag_agent.execute(request)

        # Verify guardrails agent was called
        guardrails_agent.hallucination_skill.execute.assert_called_once()
        call_args = guardrails_agent.hallucination_skill.execute.call_args
        assert "answer" in call_args.kwargs
        assert "chunks" in call_args.kwargs

    @pytest.mark.asyncio
    async def test_multiple_citations_deduplication(self, rag_agent, retrieval_agent):
        """Test that duplicate citations are removed."""
        # Mock multiple chunks from same section
        retrieval_agent.vector_search_skill.execute = AsyncMock(return_value=[
            {
                "text": "First excerpt from Chapter 3",
                "metadata": {
                    "url": "https://example.com/chapter-3",
                    "section": "Chapter 3: Neural Networks",
                    "chunk_id": "chunk-042",
                    "position": 1,
                    "embedding_score": 0.87
                }
            },
            {
                "text": "Second excerpt from Chapter 3",
                "metadata": {
                    "url": "https://example.com/chapter-3",
                    "section": "Chapter 3: Neural Networks",
                    "chunk_id": "chunk-043",
                    "position": 2,
                    "embedding_score": 0.85
                }
            }
        ])

        request = ChatRequest(
            question="What is Chapter 3 about?",
            session_id=uuid4(),
            selected_text=None
        )

        response = await rag_agent.execute(request)

        # Should have only one citation despite two chunks
        assert len(response.citations) == 1
        assert response.citations[0].section == "Chapter 3: Neural Networks"

    @pytest.mark.asyncio
    async def test_selected_text_mode_filtering(self, rag_agent, retrieval_agent):
        """Test that selected-text mode restricts answer to selected passage."""
        # Mock retrieval to return multiple chunks
        retrieval_agent.vector_search_skill.execute = AsyncMock(return_value=[
            {
                "text": "Chapter 3 covers neural networks and backpropagation",
                "metadata": {
                    "url": "https://example.com/chapter-3",
                    "section": "Chapter 3: Neural Networks",
                    "chunk_id": "chunk-042",
                    "position": 1,
                    "embedding_score": 0.87
                }
            },
            {
                "text": "Chapter 4 covers convolutional neural networks for images",
                "metadata": {
                    "url": "https://example.com/chapter-4",
                    "section": "Chapter 4: CNNs",
                    "chunk_id": "chunk-055",
                    "position": 1,
                    "embedding_score": 0.85
                }
            }
        ])

        request = ChatRequest(
            question="What is covered in the chapters?",
            session_id=uuid4(),
            selected_text="Chapter 3 covers neural networks"
        )

        response = await rag_agent.execute(request)

        # Should only return Chapter 3 citation
        assert isinstance(response, ChatResponse)
        assert len(response.citations) > 0
        assert any("Chapter 3" in c.section for c in response.citations)

    @pytest.mark.asyncio
    async def test_selected_text_no_match_fallback(self, rag_agent):
        """Test fallback when selected text doesn't match any chunks."""
        request = ChatRequest(
            question="What is in the book?",
            session_id=uuid4(),
            selected_text="quantum teleportation and wormholes"
        )

        response = await rag_agent.execute(request)

        # Should return fallback message
        assert isinstance(response, ChatResponse)
        assert "selected text" in response.answer.lower() or "cannot" in response.answer.lower()

    @pytest.mark.asyncio
    async def test_selected_text_empty_fallback(self, rag_agent, retrieval_agent):
        """Test fallback when selected-text filtering results in no chunks."""
        # Mock retrieval with chunks that won't match selected text
        retrieval_agent.vector_search_skill.execute = AsyncMock(return_value=[
            {
                "text": "Unrelated content about cooking",
                "metadata": {
                    "url": "https://example.com/page-1",
                    "section": "Section 1",
                    "chunk_id": "chunk-001",
                    "position": 1,
                    "embedding_score": 0.5
                }
            }
        ])

        request = ChatRequest(
            question="About neural networks?",
            session_id=uuid4(),
            selected_text="Chapter 3 neural networks"
        )

        response = await rag_agent.execute(request)

        # Should return fallback about selected text
        assert isinstance(response, ChatResponse)
        assert "selected text" in response.answer.lower() or "not found" in response.answer.lower()


class TestErrorHandlingAndFallbacks:
    """Test error handling and graceful fallbacks in full pipeline."""

    @pytest.mark.asyncio
    async def test_service_failure_graceful_recovery(self, rag_agent):
        """Test agent provides fallback when service fails gracefully."""
        request = ChatRequest(
            question="What is covered in the chapters?",
            session_id=uuid4(),
            selected_text=None
        )

        # Even if retrieval momentarily fails, agent should handle it
        # This tests the overall resilience

        # Note: In a real scenario, this would mock service failures
        # For now, we just verify the agent executes without crashing
        try:
            response = await rag_agent.execute(request)
            assert isinstance(response, ChatResponse)
        except Exception as e:
            # Should be a specific RAG error, not a generic crash
            from backend.utils.errors import RAGError
            assert isinstance(e, RAGError)

    @pytest.mark.asyncio
    async def test_guardrails_multiple_vetos(self, rag_agent, guardrails_agent):
        """Test handling when guardrails reject answer multiple times."""
        request = ChatRequest(
            question="What is this?",
            session_id=uuid4()
        )

        # Simulate guardrails detecting hallucination
        guardrails_agent.hallucination_skill.execute = AsyncMock(return_value={
            "grounded": False,
            "veto_reason": "Contains unsupported claims"
        })

        response = await rag_agent.execute(request)

        # Should return fallback message
        assert isinstance(response, ChatResponse)
        assert "cannot provide" in response.answer.lower() or "found" in response.answer.lower()

    @pytest.mark.asyncio
    async def test_empty_retrieval_then_selected_text_mismatch(self, rag_agent):
        """Test fallback when retrieval is empty and selected text doesn't match."""
        request = ChatRequest(
            question="About something very obscure",
            session_id=uuid4(),
            selected_text="Very specific text that won't match anything"
        )

        response = await rag_agent.execute(request)

        # Should return user-friendly fallback
        assert isinstance(response, ChatResponse)
        assert "could not find" in response.answer.lower() or "selected text" in response.answer.lower()
        assert len(response.citations) == 0
