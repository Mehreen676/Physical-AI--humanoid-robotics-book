"""
Unit tests for SessionManager.

Tests session creation, message addition, and message retrieval.
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4, UUID
from datetime import datetime

from backend.storage.sessions import SessionManager
from backend.storage.models import Session, ChatMessage, User


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return MagicMock()


@pytest.fixture
def session_manager(mock_db_session):
    """Create SessionManager with mocked database."""
    return SessionManager(mock_db_session)


class TestSessionManager:
    """Test cases for SessionManager."""

    def test_create_session_new_user(self, session_manager, mock_db_session):
        """Test creating a new session with auto-generated user."""
        # Mock successful database operations
        mock_db_session.query().filter().first.return_value = None
        mock_db_session.add = MagicMock()
        mock_db_session.flush = MagicMock()
        mock_db_session.commit = MagicMock()

        # Create session
        session_id = session_manager.create_session(user_id=None)

        # Verify
        assert session_id is not None
        assert isinstance(UUID(session_id), UUID)
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()

    def test_create_session_existing_user(self, session_manager, mock_db_session):
        """Test creating a session for existing user."""
        user_id = uuid4()

        # Mock existing user
        mock_user = MagicMock(spec=User)
        mock_user.user_id = user_id
        mock_db_session.query().filter().first.return_value = mock_user

        # Create session
        session_id = session_manager.create_session(user_id=user_id)

        # Verify
        assert session_id is not None
        mock_db_session.commit.assert_called()

    def test_add_message_success(self, session_manager, mock_db_session):
        """Test adding a message to a session."""
        session_id = uuid4()

        # Mock existing session
        mock_session = MagicMock(spec=Session)
        mock_session.session_id = session_id
        mock_session.updated_at = datetime.utcnow()
        mock_db_session.query().filter().first.return_value = mock_session

        # Add message
        message_id = session_manager.add_message(
            session_id=session_id,
            role="user",
            content="What is Chapter 3 about?"
        )

        # Verify
        assert message_id is not None
        assert isinstance(UUID(message_id), UUID)
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()

    def test_add_message_session_not_found(self, session_manager, mock_db_session):
        """Test adding message to non-existent session."""
        session_id = uuid4()

        # Mock missing session
        mock_db_session.query().filter().first.return_value = None

        # Add message
        message_id = session_manager.add_message(
            session_id=session_id,
            role="user",
            content="Test message"
        )

        # Verify
        assert message_id is None
        mock_db_session.rollback.assert_called()

    def test_get_session_found(self, session_manager, mock_db_session):
        """Test retrieving an existing session."""
        session_id = uuid4()

        # Mock existing session
        mock_session = MagicMock(spec=Session)
        mock_session.session_id = session_id
        mock_db_session.query().filter().first.return_value = mock_session

        # Get session
        result = session_manager.get_session(session_id=session_id)

        # Verify
        assert result == mock_session

    def test_get_session_not_found(self, session_manager, mock_db_session):
        """Test retrieving non-existent session."""
        session_id = uuid4()

        # Mock missing session
        mock_db_session.query().filter().first.return_value = None

        # Get session
        result = session_manager.get_session(session_id=session_id)

        # Verify
        assert result is None

    def test_get_messages_success(self, session_manager, mock_db_session):
        """Test retrieving messages from a session."""
        session_id = uuid4()

        # Mock messages
        mock_messages = [
            MagicMock(spec=ChatMessage, role="user", content="Question 1"),
            MagicMock(spec=ChatMessage, role="assistant", content="Answer 1"),
        ]
        mock_db_session.query().filter().order_by().offset().limit().all.return_value = mock_messages

        # Get messages
        messages = session_manager.get_messages(session_id=session_id, limit=5)

        # Verify
        assert len(messages) == 2
        assert messages == mock_messages

    def test_get_all_messages(self, session_manager, mock_db_session):
        """Test retrieving all messages from a session."""
        session_id = uuid4()

        # Mock messages
        mock_messages = [
            MagicMock(spec=ChatMessage, role="user", created_at=datetime.utcnow()),
            MagicMock(spec=ChatMessage, role="assistant", created_at=datetime.utcnow()),
        ]
        mock_db_session.query().filter().order_by().all.return_value = mock_messages

        # Get all messages
        messages = session_manager.get_all_messages(session_id=session_id)

        # Verify
        assert len(messages) == 2
        assert messages == mock_messages
