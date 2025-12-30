"""
Pytest configuration and fixtures for BookRAGAgent tests.

This file contains global fixtures and pytest configuration for all tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import MagicMock, AsyncMock
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure asyncio for pytest
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Mock fixtures for external services
@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client."""
    mock = AsyncMock()
    mock.search = AsyncMock(return_value=[
        {
            "id": "chunk-001",
            "score": 0.85,
            "payload": {
                "text": "Sample chunk content",
                "url": "https://example.com/chapter-1",
                "section": "Chapter 1: Introduction",
                "chunk_id": "chunk-001",
                "position": 1
            }
        }
    ])
    mock.health = AsyncMock(return_value={"status": "ok"})
    return mock


@pytest.fixture
def mock_openrouter_client():
    """Mock OpenRouter LLM client."""
    mock = AsyncMock()
    mock.create_completion = AsyncMock(return_value={
        "choices": [{
            "message": {
                "content": "Sample response from LLM"
            }
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    })
    return mock


@pytest.fixture
def mock_database():
    """Mock database connection."""
    mock = MagicMock()
    mock.execute = MagicMock()
    mock.fetchone = MagicMock(return_value=(1,))
    mock.fetchall = MagicMock(return_value=[(1,), (2,)])
    mock.commit = MagicMock()
    mock.close = MagicMock()
    return mock


@pytest.fixture
def mock_embeddings_service():
    """Mock embeddings service."""
    mock = AsyncMock()
    mock.embed = AsyncMock(return_value=[0.1, 0.2, 0.3, 0.4, 0.5] * 256)  # 1280-dimensional vector
    mock.embed_batch = AsyncMock(return_value=[
        [0.1, 0.2, 0.3, 0.4, 0.5] * 256,
        [0.2, 0.3, 0.4, 0.5, 0.6] * 256,
    ])
    return mock


# Sample data fixtures
@pytest.fixture
def sample_query():
    """Sample query for testing."""
    return "What is the main topic of Chapter 3?"


@pytest.fixture
def sample_chunks():
    """Sample retrieved chunks."""
    return [
        {
            "text": "Chapter 3 covers neural networks and deep learning fundamentals.",
            "metadata": {
                "url": "https://example.com/chapter-3",
                "section": "Chapter 3: Neural Networks",
                "chunk_id": "chunk-042",
                "position": 1,
                "embedding_score": 0.87
            }
        },
        {
            "text": "Perceptrons are the basic building blocks of neural networks.",
            "metadata": {
                "url": "https://example.com/chapter-3",
                "section": "Chapter 3: Neural Networks",
                "chunk_id": "chunk-043",
                "position": 2,
                "embedding_score": 0.85
            }
        }
    ]


@pytest.fixture
def sample_session_id():
    """Sample session ID for testing."""
    return "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing."""
    return "user-001"


# Markers for test categorization
def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "async: mark test as async"
    )
