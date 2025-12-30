"""
Session management for multi-turn conversations.

Provides SessionManager class for creating, retrieving, and managing chat sessions.
"""

from sqlalchemy.orm import Session as SASession
from sqlalchemy import desc
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, List
import logging

from storage.models import User, Session, ChatMessage

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages conversation sessions and messages."""

    def __init__(self, db_session: SASession):
        """Initialize SessionManager with database session."""
        self.db = db_session

    def create_session(self, user_id: Optional[UUID] = None) -> str:
        """
        Create a new conversation session.

        Args:
            user_id: Optional user ID. If None, creates a new anonymous user.

        Returns:
            Session ID (UUID string)
        """
        try:
            # Create user if needed
            if user_id is None:
                user = User(user_id=uuid4())
                self.db.add(user)
                self.db.flush()
                user_id = user.user_id
            else:
                # Verify user exists
                user = self.db.query(User).filter(User.user_id == user_id).first()
                if not user:
                    user = User(user_id=user_id)
                    self.db.add(user)
                    self.db.flush()

            # Create session
            session = Session(
                session_id=uuid4(),
                user_id=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                metadata={}
            )
            self.db.add(session)
            self.db.commit()

            logger.info(f"Created session {session.session_id} for user {user_id}")
            return str(session.session_id)
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            self.db.rollback()
            raise

    def get_session(self, session_id: UUID) -> Optional[Session]:
        """
        Retrieve a session by ID.

        Args:
            session_id: UUID of the session

        Returns:
            Session object or None if not found
        """
        try:
            session = self.db.query(Session).filter(Session.session_id == session_id).first()
            return session
        except Exception as e:
            logger.error(f"Failed to retrieve session {session_id}: {e}")
            return None

    def add_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        metadata: dict = None
    ) -> Optional[str]:
        """
        Add a message to a session.

        Args:
            session_id: UUID of the session
            role: 'user' or 'assistant'
            content: Message content
            metadata: Optional metadata dictionary

        Returns:
            Message ID (UUID string) or None if failed
        """
        try:
            # Verify session exists
            session = self.db.query(Session).filter(Session.session_id == session_id).first()
            if not session:
                logger.error(f"Session {session_id} not found")
                return None

            # Create message
            message = ChatMessage(
                message_id=uuid4(),
                session_id=session_id,
                role=role,
                content=content,
                metadata=metadata or {},
                created_at=datetime.utcnow()
            )
            self.db.add(message)

            # Update session's updated_at
            session.updated_at = datetime.utcnow()

            self.db.commit()
            logger.info(f"Added {role} message to session {session_id}")
            return str(message.message_id)
        except Exception as e:
            logger.error(f"Failed to add message to session {session_id}: {e}")
            self.db.rollback()
            return None

    def get_messages(
        self,
        session_id: UUID,
        limit: int = 5,
        offset: int = 0
    ) -> List[ChatMessage]:
        """
        Retrieve messages from a session.

        Args:
            session_id: UUID of the session
            limit: Maximum number of messages to retrieve
            offset: Number of messages to skip

        Returns:
            List of ChatMessage objects
        """
        try:
            messages = (
                self.db.query(ChatMessage)
                .filter(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at.asc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return messages
        except Exception as e:
            logger.error(f"Failed to retrieve messages for session {session_id}: {e}")
            return []

    def get_all_messages(self, session_id: UUID) -> List[ChatMessage]:
        """
        Retrieve all messages from a session (ordered by creation time).

        Args:
            session_id: UUID of the session

        Returns:
            List of all ChatMessage objects
        """
        try:
            messages = (
                self.db.query(ChatMessage)
                .filter(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at.asc())
                .all()
            )
            return messages
        except Exception as e:
            logger.error(f"Failed to retrieve all messages for session {session_id}: {e}")
            return []
