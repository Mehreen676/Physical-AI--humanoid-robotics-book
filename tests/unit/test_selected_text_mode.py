"""
Unit tests for Selected-Text Mode (Phase 4).

Tests the filtering and restriction of answers to user-selected passages.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from backend.models.schemas import ChatRequest, ChatResponse
from backend.agent.sub_agents import SelectionModeSubAgent
from backend.rag.grounding import SelectedTextOverrideSkill
from backend.agent.agent import BookRAGAgent


@pytest.fixture
def selected_text_skill():
    """Create SelectedTextOverrideSkill instance."""
    return SelectedTextOverrideSkill()


@pytest.fixture
def selection_mode_agent():
    """Create SelectionModeSubAgent instance."""
    return SelectionModeSubAgent()


@pytest.fixture
def sample_chunks():
    """Sample chunks for testing."""
    return [
        {
            "text": "Chapter 3 covers neural networks and deep learning fundamentals including backpropagation.",
            "metadata": {
                "url": "https://example.com/chapter-3",
                "section": "Chapter 3: Neural Networks",
                "chunk_id": "chunk-042",
                "position": 1,
                "embedding_score": 0.87
            }
        },
        {
            "text": "Chapter 4 discusses convolutional neural networks for image processing applications.",
            "metadata": {
                "url": "https://example.com/chapter-4",
                "section": "Chapter 4: CNNs",
                "chunk_id": "chunk-055",
                "position": 1,
                "embedding_score": 0.82
            }
        },
        {
            "text": "Chapter 5 explores recurrent neural networks for sequence modeling tasks.",
            "metadata": {
                "url": "https://example.com/chapter-5",
                "section": "Chapter 5: RNNs",
                "chunk_id": "chunk-068",
                "position": 1,
                "embedding_score": 0.79
            }
        }
    ]


class TestSelectedTextOverrideSkill:
    """Test cases for SelectedTextOverrideSkill."""

    @pytest.mark.asyncio
    async def test_filter_chunks_with_matching_text(self, selected_text_skill, sample_chunks):
        """Test filtering chunks when selected text matches."""
        selected_text = "neural networks and deep learning fundamentals"

        result = await selected_text_skill.execute(
            chunks=sample_chunks,
            selected_text=selected_text
        )

        # Should return only chunk 042 which contains the selected text
        assert len(result) > 0
        assert any(chunk["metadata"]["chunk_id"] == "chunk-042" for chunk in result)

    @pytest.mark.asyncio
    async def test_filter_chunks_no_match(self, selected_text_skill, sample_chunks):
        """Test filtering fails when selected text doesn't match any chunks."""
        selected_text = "quantum computing and quantum entanglement"

        with pytest.raises(ValueError, match="The selected text does not match"):
            await selected_text_skill.execute(
                chunks=sample_chunks,
                selected_text=selected_text
            )

    @pytest.mark.asyncio
    async def test_filter_chunks_empty_selected_text(self, selected_text_skill, sample_chunks):
        """Test that empty selected text returns all chunks."""
        result = await selected_text_skill.execute(
            chunks=sample_chunks,
            selected_text=""
        )

        # Should return all chunks when selected_text is empty
        assert len(result) == len(sample_chunks)

    @pytest.mark.asyncio
    async def test_filter_chunks_empty_chunks_list(self, selected_text_skill):
        """Test filtering with empty chunks list."""
        result = await selected_text_skill.execute(
            chunks=[],
            selected_text="some text"
        )

        # Should return empty list
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_filter_chunks_partial_match(self, selected_text_skill, sample_chunks):
        """Test filtering with partial word matches."""
        selected_text = "neural networks"

        result = await selected_text_skill.execute(
            chunks=sample_chunks,
            selected_text=selected_text
        )

        # Should match multiple chunks that contain "neural" or "networks"
        assert len(result) > 0


class TestSelectionModeSubAgent:
    """Test cases for SelectionModeSubAgent."""

    @pytest.mark.asyncio
    async def test_execute_with_selected_text(self, selection_mode_agent, sample_chunks):
        """Test sub-agent filters chunks when selected text provided."""
        selected_text = "neural networks"

        result = await selection_mode_agent.execute(
            chunks=sample_chunks,
            selected_text=selected_text
        )

        # Should return filtered chunks
        assert len(result) > 0
        assert len(result) <= len(sample_chunks)

    @pytest.mark.asyncio
    async def test_execute_without_selected_text(self, selection_mode_agent, sample_chunks):
        """Test sub-agent returns all chunks when no selected text."""
        result = await selection_mode_agent.execute(
            chunks=sample_chunks,
            selected_text=None
        )

        # Should return all chunks
        assert len(result) == len(sample_chunks)

    @pytest.mark.asyncio
    async def test_execute_empty_selected_text(self, selection_mode_agent, sample_chunks):
        """Test sub-agent returns all chunks when selected text is empty."""
        result = await selection_mode_agent.execute(
            chunks=sample_chunks,
            selected_text=""
        )

        # Should return all chunks
        assert len(result) == len(sample_chunks)

    @pytest.mark.asyncio
    async def test_execute_no_matching_chunks(self, selection_mode_agent, sample_chunks):
        """Test sub-agent raises error when no chunks match selected text."""
        with pytest.raises(ValueError):
            await selection_mode_agent.execute(
                chunks=sample_chunks,
                selected_text="completely unrelated text that won't match"
            )


class TestSelectedTextModeIntegration:
    """Integration tests for selected-text mode with BookRAGAgent."""

    @pytest.mark.asyncio
    async def test_agent_with_selected_text_mode(self):
        """Test BookRAGAgent with selected-text mode enabled."""
        # Mock sub-agents
        retrieval_agent = AsyncMock()
        answer_agent = AsyncMock()
        guardrails_agent = AsyncMock()

        # Setup mock responses
        sample_chunks = [
            {
                "text": "Chapter 3 covers neural networks",
                "metadata": {
                    "url": "https://example.com/chapter-3",
                    "section": "Chapter 3",
                    "chunk_id": "chunk-042",
                    "position": 1,
                    "embedding_score": 0.87
                }
            }
        ]

        retrieval_agent.execute = AsyncMock(return_value=sample_chunks)
        answer_agent.execute = AsyncMock(return_value="Chapter 3 covers neural networks and deep learning.")
        guardrails_agent.execute = AsyncMock(return_value={
            "approved": True,
            "answer": "Chapter 3 covers neural networks and deep learning.",
            "chunks": sample_chunks
        })

        # Create agent with real SelectionModeSubAgent
        agent = BookRAGAgent(
            retrieval_agent=retrieval_agent,
            answer_agent=answer_agent,
            guardrails_agent=guardrails_agent
        )

        # Create request with selected text
        request = ChatRequest(
            question="What is covered in Chapter 3?",
            session_id=uuid4(),
            selected_text="Chapter 3 covers neural networks"
        )

        # Execute
        response = await agent.execute(request)

        # Verify response
        assert isinstance(response, ChatResponse)
        assert response.answer is not None
        assert len(response.citations) > 0

    @pytest.mark.asyncio
    async def test_agent_without_selected_text(self):
        """Test BookRAGAgent without selected-text mode."""
        # Mock sub-agents
        retrieval_agent = AsyncMock()
        answer_agent = AsyncMock()
        guardrails_agent = AsyncMock()

        sample_chunks = [
            {
                "text": "Chapter 3 covers neural networks",
                "metadata": {
                    "url": "https://example.com/chapter-3",
                    "section": "Chapter 3",
                    "chunk_id": "chunk-042",
                    "position": 1,
                    "embedding_score": 0.87
                }
            }
        ]

        retrieval_agent.execute = AsyncMock(return_value=sample_chunks)
        answer_agent.execute = AsyncMock(return_value="Chapter 3 covers neural networks and deep learning.")
        guardrails_agent.execute = AsyncMock(return_value={
            "approved": True,
            "answer": "Chapter 3 covers neural networks and deep learning.",
            "chunks": sample_chunks
        })

        agent = BookRAGAgent(
            retrieval_agent=retrieval_agent,
            answer_agent=answer_agent,
            guardrails_agent=guardrails_agent
        )

        # Create request WITHOUT selected text
        request = ChatRequest(
            question="What is covered in Chapter 3?",
            session_id=uuid4(),
            selected_text=None
        )

        # Execute
        response = await agent.execute(request)

        # Verify response
        assert isinstance(response, ChatResponse)
        assert response.answer is not None

    @pytest.mark.asyncio
    async def test_agent_selected_text_no_match_fallback(self):
        """Test BookRAGAgent fallback when selected text doesn't match chunks."""
        # Mock sub-agents
        retrieval_agent = AsyncMock()
        answer_agent = AsyncMock()
        guardrails_agent = AsyncMock()

        sample_chunks = [
            {
                "text": "Chapter 3 covers neural networks",
                "metadata": {
                    "url": "https://example.com/chapter-3",
                    "section": "Chapter 3",
                    "chunk_id": "chunk-042",
                    "position": 1,
                    "embedding_score": 0.87
                }
            }
        ]

        retrieval_agent.execute = AsyncMock(return_value=sample_chunks)

        agent = BookRAGAgent(
            retrieval_agent=retrieval_agent,
            answer_agent=answer_agent,
            guardrails_agent=guardrails_agent
        )

        # Create request with non-matching selected text
        request = ChatRequest(
            question="What is in the book?",
            session_id=uuid4(),
            selected_text="quantum computing and photosynthesis"
        )

        # Execute
        response = await agent.execute(request)

        # Should return fallback response
        assert isinstance(response, ChatResponse)
        assert "selected text" in response.answer.lower()
        assert len(response.citations) == 0
