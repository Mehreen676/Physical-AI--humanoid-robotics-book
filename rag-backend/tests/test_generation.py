"""
Tests for Content Generation Service.
Tests LLM integration and prompt templates (with mocked OpenAI client).
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from generation_service import (
    PromptTemplates,
    GeneratedResponse,
    GenerationAgent,
    get_generation_agent,
)


class TestPromptTemplates:
    """Test prompt template generation."""

    def test_rag_prompt_format(self):
        """Test RAG prompt formatting."""
        query = "What is ROS 2?"
        context = "ROS 2 is a robotics middleware..."

        prompt = PromptTemplates.rag_prompt(query, context)

        assert "ROS 2 is a robotics middleware..." in prompt
        assert "What is ROS 2?" in prompt
        assert "User Question:" in prompt
        assert "Answer:" in prompt

    def test_system_message(self):
        """Test system message generation."""
        msg = PromptTemplates.system_message()

        assert "expert educational assistant" in msg.lower()
        assert "robotics" in msg.lower()
        assert "ROS 2" in msg
        assert len(msg) > 100

    def test_selected_text_prompt_format(self):
        """Test selected-text mode prompt."""
        query = "Explain this more"
        context = "Additional context here"
        selected_text = "User highlighted this"

        prompt = PromptTemplates.selected_text_prompt(query, context, selected_text)

        assert "User highlighted this" in prompt
        assert "Additional context here" in prompt
        assert "Explain this more" in prompt

    def test_clarification_prompt_format(self):
        """Test clarification prompt when no context available."""
        query = "What is quantum computing?"

        prompt = PromptTemplates.clarification_prompt(query)

        assert "quantum computing" in prompt.lower()
        assert "general knowledge" in prompt.lower()
        assert "course materials" in prompt.lower()


class TestGeneratedResponse:
    """Test GeneratedResponse dataclass."""

    def test_generated_response_creation(self):
        """Test creating a generated response."""
        response = GeneratedResponse(
            content="This is the answer.",
            model="gpt-4o",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
        )

        assert response.content == "This is the answer."
        assert response.model == "gpt-4o"
        assert response.total_tokens == 150

    def test_generated_response_to_dict(self):
        """Test converting response to dictionary."""
        response = GeneratedResponse(
            content="Answer",
            model="gpt-4o",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
        )

        response_dict = response.to_dict()

        assert response_dict["content"] == "Answer"
        assert response_dict["model"] == "gpt-4o"
        assert response_dict["input_tokens"] == 100
        assert response_dict["output_tokens"] == 50


class TestGenerationAgent:
    """Test generation agent functionality."""

    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client."""
        mock_client = MagicMock()

        # Setup response mock
        mock_choice = MagicMock()
        mock_choice.message.content = "This is the generated answer."

        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 50
        mock_usage.total_tokens = 150

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        mock_client.chat.completions.create.return_value = mock_response

        return mock_client

    @patch("generation_service.get_settings")
    @patch("generation_service.OpenAI")
    def test_generate_rag_response(self, mock_openai, mock_settings, mock_openai_client):
        """Test generating RAG response."""
        # Setup mocks
        mock_settings.return_value.openai_api_key = "test-key"
        mock_openai.return_value = mock_openai_client

        agent = GenerationAgent(model="gpt-4o", temperature=0.3)
        agent.client = mock_openai_client

        response = agent.generate(
            query="What is ROS 2?",
            context="ROS 2 is a robotics middleware...",
            mode="full_book",
        )

        assert response.content == "This is the generated answer."
        assert response.model == "gpt-4o"
        assert response.input_tokens == 100
        assert response.output_tokens == 50

    @patch("generation_service.get_settings")
    @patch("generation_service.OpenAI")
    def test_generate_selected_text_response(
        self, mock_openai, mock_settings, mock_openai_client
    ):
        """Test generating response in selected-text mode."""
        mock_settings.return_value.openai_api_key = "test-key"
        mock_openai.return_value = mock_openai_client

        agent = GenerationAgent(model="gpt-4o")
        agent.client = mock_openai_client

        response = agent.generate(
            query="Explain more about this",
            context="Context here",
            mode="selected_text",
            selected_text="User highlighted text",
        )

        assert response.content == "This is the generated answer."
        # Verify that selected-text prompt was used (it would contain our highlighted text)
        call_args = mock_openai_client.chat.completions.create.call_args
        assert call_args is not None

    @patch("generation_service.get_settings")
    @patch("generation_service.OpenAI")
    def test_token_usage_tracking(self, mock_openai, mock_settings, mock_openai_client):
        """Test token usage tracking."""
        mock_settings.return_value.openai_api_key = "test-key"
        mock_openai.return_value = mock_openai_client

        agent = GenerationAgent(model="gpt-4o")
        agent.client = mock_openai_client

        # Make first request
        agent.generate(query="Question 1", context="Context 1")

        assert agent.token_usage["input"] == 100
        assert agent.token_usage["output"] == 50
        assert agent.token_usage["total"] == 150

        # Make second request
        agent.generate(query="Question 2", context="Context 2")

        assert agent.token_usage["input"] == 200
        assert agent.token_usage["output"] == 100
        assert agent.token_usage["total"] == 300

    @patch("generation_service.get_settings")
    @patch("generation_service.OpenAI")
    def test_cost_estimation_gpt4o(self, mock_openai, mock_settings, mock_openai_client):
        """Test cost estimation for GPT-4o."""
        mock_settings.return_value.openai_api_key = "test-key"
        mock_openai.return_value = mock_openai_client

        agent = GenerationAgent(model="gpt-4o")
        agent.client = mock_openai_client

        # Manually set token usage
        agent.token_usage = {"input": 1000, "output": 500, "total": 1500}

        cost = agent.get_cost_estimate()

        # GPT-4o: $0.005 per 1K input, $0.015 per 1K output
        expected_input_cost = 1000 / 1000 * 0.005  # $0.005
        expected_output_cost = 500 / 1000 * 0.015  # $0.0075
        expected_total = expected_input_cost + expected_output_cost

        assert cost["input_tokens"] == 1000
        assert cost["output_tokens"] == 500
        assert cost["input_cost_usd"] == pytest.approx(0.005, abs=0.0001)
        assert cost["output_cost_usd"] == pytest.approx(0.0075, abs=0.0001)

    @patch("generation_service.get_settings")
    @patch("generation_service.OpenAI")
    def test_cost_estimation_gpt35(self, mock_openai, mock_settings, mock_openai_client):
        """Test cost estimation for GPT-3.5-turbo."""
        mock_settings.return_value.openai_api_key = "test-key"
        mock_openai.return_value = mock_openai_client

        agent = GenerationAgent(model="gpt-3.5-turbo")
        agent.client = mock_openai_client

        # Manually set token usage
        agent.token_usage = {"input": 1000, "output": 1000, "total": 2000}

        cost = agent.get_cost_estimate()

        # GPT-3.5-turbo: $0.0005 per 1K input, $0.0015 per 1K output
        # With 1000 input tokens: 1 * 0.0005 = 0.0005
        # With 1000 output tokens: 1 * 0.0015 = 0.0015

        assert cost["input_cost_usd"] == pytest.approx(0.0005, abs=0.00001)
        assert cost["output_cost_usd"] == pytest.approx(0.0015, abs=0.00001)

    @patch("generation_service.get_settings")
    @patch("generation_service.OpenAI")
    def test_token_counter_reset(self, mock_openai, mock_settings, mock_openai_client):
        """Test resetting token counter."""
        mock_settings.return_value.openai_api_key = "test-key"
        mock_openai.return_value = mock_openai_client

        agent = GenerationAgent(model="gpt-4o")
        agent.client = mock_openai_client

        # Generate a response
        agent.generate(query="Test", context="Context")

        assert agent.token_usage["total"] == 150

        # Reset
        agent.reset_token_counter()

        assert agent.token_usage["input"] == 0
        assert agent.token_usage["output"] == 0
        assert agent.token_usage["total"] == 0


class TestGenerationIntegration:
    """Integration tests for generation."""

    @patch("generation_service.get_settings")
    @patch("generation_service.OpenAI")
    def test_full_rag_generation_workflow(
        self, mock_openai, mock_settings
    ):
        """Test complete RAG generation workflow."""
        # Setup
        mock_settings.return_value.openai_api_key = "test-key"
        mock_client = MagicMock()

        # Mock response
        mock_choice = MagicMock()
        mock_choice.message.content = """ROS 2 is a flexible middleware for robotics that provides:
1. A modular architecture
2. Real-time capabilities
3. Secure communications

It's designed for production systems with emphasis on reliability and security."""

        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 250
        mock_usage.completion_tokens = 100
        mock_usage.total_tokens = 350

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        agent = GenerationAgent(model="gpt-4o", temperature=0.3, max_tokens=500)
        agent.client = mock_client

        # Simulate retrieved context
        context = """[Source 1: Module 1 > Introduction (sim: 0.95)]
ROS 2 is a robotics middleware providing modular architecture.

[Source 2: Module 1 > Architecture (sim: 0.87)]
ROS 2 emphasizes real-time capabilities and secure communications."""

        response = agent.generate(
            query="What is ROS 2 and what are its key features?",
            context=context,
            mode="full_book",
        )

        assert "ROS 2" in response.content
        assert "middleware" in response.content.lower()
        assert response.model == "gpt-4o"
        assert response.input_tokens > 0
        assert response.output_tokens > 0

    @patch("generation_service.get_settings")
    @patch("generation_service.OpenAI")
    def test_temperature_configuration(
        self, mock_openai, mock_settings
    ):
        """Test temperature configuration."""
        mock_settings.return_value.openai_api_key = "test-key"
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Setup response mock
        mock_choice = MagicMock()
        mock_choice.message.content = "Test response"
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 5
        mock_usage.total_tokens = 15
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        mock_client.chat.completions.create.return_value = mock_response

        # Create agent with specific temperature
        agent = GenerationAgent(model="gpt-4o", temperature=0.7)
        agent.client = mock_client

        agent.generate(query="Test", context="Context")

        # Verify temperature was passed to API
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["temperature"] == 0.7

    @patch("generation_service.get_settings")
    @patch("generation_service.OpenAI")
    def test_max_tokens_configuration(
        self, mock_openai, mock_settings
    ):
        """Test max tokens configuration."""
        mock_settings.return_value.openai_api_key = "test-key"
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Setup response mock
        mock_choice = MagicMock()
        mock_choice.message.content = "Test response"
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 5
        mock_usage.total_tokens = 15
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        mock_client.chat.completions.create.return_value = mock_response

        agent = GenerationAgent(model="gpt-4o", max_tokens=300)
        agent.client = mock_client

        agent.generate(query="Test", context="Context")

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["max_tokens"] == 300


class TestGenerationSingleton:
    """Test generation agent singleton."""

    @patch("generation_service.get_settings")
    @patch("generation_service.OpenAI")
    def test_get_generation_agent_singleton(self, mock_openai, mock_settings):
        """Test singleton pattern for generation agent."""
        mock_settings.return_value.openai_api_key = "test-key"
        mock_openai.return_value = MagicMock()

        agent1 = get_generation_agent(model="gpt-4o")
        agent2 = get_generation_agent(model="gpt-3.5-turbo")

        # Should return same instance
        assert agent1 is agent2
