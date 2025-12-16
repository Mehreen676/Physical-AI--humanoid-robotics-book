"""
Database ORM Models and Session Management.
Uses SQLAlchemy with Neon PostgreSQL backend.
"""

from sqlalchemy import (
    create_engine,
    Column,
    String,
    Text,
    DateTime,
    Integer,
    Boolean,
    ForeignKey,
    Index,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session as SQLSession
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timedelta
import logging
from config import get_settings

logger = logging.getLogger(__name__)

# SQLAlchemy base for model declarations
Base = declarative_base()


class Document(Base):
    """Stores document metadata (chapters, sections, chunks)."""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_id = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    chapter = Column(String(255), nullable=True, index=True)
    section = Column(String(255), nullable=True)
    chunk_index = Column(Integer, nullable=True)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), unique=True, nullable=False)  # SHA256
    vector_id = Column(String(255), nullable=True)  # Reference to Qdrant
    book_version = Column(String(50), default="v1.0", index=True)
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<Document(doc_id={self.doc_id}, chapter={self.chapter})>"


class ChatSession(Base):
    """Stores chat session information."""

    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    title = Column(String(255), nullable=True)
    book_version = Column(String(50), default="v1.0")
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_activity = Column(DateTime, default=datetime.utcnow)
    extra_metadata = Column(Text, nullable=True)  # JSON blob for extra data

    def __repr__(self):
        return f"<ChatSession(session_id={self.session_id}, messages={self.message_count})>"


class Message(Base):
    """Stores chat messages (user queries and assistant responses)."""

    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        String(255),
        ForeignKey(
            "chat_sessions.session_id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    user_message = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=True)
    mode = Column(
        String(50), default="full_book", nullable=False
    )  # full_book or selected_text
    selected_text = Column(Text, nullable=True)  # For selected-text mode
    source_chunk_ids = Column(Text, nullable=True)  # JSON list of chunk IDs
    in_selected_text = Column(Boolean, default=True)  # Validation result
    latency_ms = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<Message(session_id={self.session_id}, mode={self.mode})>"


# Create indexes for common queries
Index("idx_documents_chapter", Document.chapter)
Index("idx_documents_book_version", Document.book_version)
Index("idx_documents_content_hash", Document.content_hash)
Index("idx_sessions_user_id", ChatSession.user_id)
Index("idx_sessions_book_version", ChatSession.book_version)
Index("idx_messages_session_created", Message.session_id, Message.created_at)


class DatabaseSession:
    """Database session manager."""

    def __init__(self):
        """Initialize database connection."""
        settings = get_settings()
        self.engine = create_engine(
            settings.database_url,
            echo=settings.debug,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Verify connections before using
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        logger.info("✅ Database engine initialized")

    def create_tables(self):
        """Create all tables in database."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("✅ Database tables created successfully")
        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")
            raise

    def get_session(self) -> SQLSession:
        """Get a new database session."""
        return self.SessionLocal()

    def close(self):
        """Close database connection."""
        self.engine.dispose()
        logger.info("✅ Database connection closed")


# Singleton instance
_db_instance: DatabaseSession = None


def get_db() -> DatabaseSession:
    """Get or create database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseSession()
    return _db_instance


def get_db_session() -> SQLSession:
    """Get a new database session (dependency for FastAPI routes)."""
    db = get_db()
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()


# Helper functions for common database operations

def add_session(session_id: str, user_id: str = None, title: str = None, book_version: str = "v1.0") -> ChatSession:
    """Create a new chat session."""
    db = get_db()
    session = db.get_session()
    try:
        chat_session = ChatSession(
            session_id=session_id,
            user_id=user_id,
            title=title,
            book_version=book_version,
        )
        session.add(chat_session)
        session.commit()
        logger.info(f"✅ Created session: {session_id}")
        return chat_session
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error creating session: {e}")
        raise
    finally:
        session.close()


def get_session(session_id: str) -> ChatSession:
    """Retrieve a chat session. Returns None if session expired (>30 days inactive)."""
    db = get_db()
    session = db.get_session()
    try:
        chat_session = session.query(ChatSession).filter_by(
            session_id=session_id
        ).first()

        # Check expiry: sessions inactive for >30 days are expired
        if chat_session:
            last_activity = chat_session.last_activity or chat_session.created_at
            if datetime.utcnow() - last_activity > timedelta(days=30):
                logger.info(f"⏰ Session {session_id} expired (inactive >30 days)")
                return None

        return chat_session
    finally:
        session.close()


def update_session(session_id: str, **kwargs) -> ChatSession:
    """Update session metadata (title, book_version, etc.)."""
    db = get_db()
    session = db.get_session()
    try:
        chat_session = session.query(ChatSession).filter_by(
            session_id=session_id
        ).first()

        if not chat_session:
            logger.warning(f"⚠️ Session {session_id} not found for update")
            return None

        # Update allowed fields
        for key, value in kwargs.items():
            if hasattr(chat_session, key) and key not in ["id", "session_id", "created_at"]:
                setattr(chat_session, key, value)
                logger.debug(f"📝 Updated session {session_id}: {key}={value}")

        # Always update last_activity
        chat_session.last_activity = datetime.utcnow()
        session.commit()
        logger.info(f"✅ Updated session: {session_id}")
        return chat_session
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error updating session: {e}")
        raise
    finally:
        session.close()


def add_message(
    session_id: str,
    user_message: str,
    assistant_response: str = None,
    mode: str = "full_book",
    selected_text: str = None,
    source_chunk_ids: str = None,
    in_selected_text: bool = True,
    latency_ms: int = None,
) -> Message:
    """Add a message to a chat session."""
    db = get_db()
    session = db.get_session()
    try:
        message = Message(
            session_id=session_id,
            user_message=user_message,
            assistant_response=assistant_response,
            mode=mode,
            selected_text=selected_text,
            source_chunk_ids=source_chunk_ids,
            in_selected_text=in_selected_text,
            latency_ms=latency_ms,
        )
        session.add(message)

        # Update session stats
        chat_session = session.query(ChatSession).filter_by(
            session_id=session_id
        ).first()
        if chat_session:
            chat_session.message_count += 1
            chat_session.last_activity = datetime.utcnow()

        session.commit()
        logger.debug(f"✅ Added message to session: {session_id}")
        return message
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error adding message: {e}")
        raise
    finally:
        session.close()


def get_session_history(session_id: str, limit: int = 50, offset: int = 0) -> list:
    """Get chat history for a session with pagination support."""
    db = get_db()
    session = db.get_session()
    try:
        messages = (
            session.query(Message)
            .filter_by(session_id=session_id)
            .order_by(Message.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return list(reversed(messages))  # Reverse to get chronological order
    finally:
        session.close()


def add_document(
    doc_id: str,
    title: str,
    chapter: str,
    section: str,
    content: str,
    content_hash: str,
    vector_id: str = None,
) -> Document:
    """Add a document chunk to the database."""
    db = get_db()
    session = db.get_session()
    try:
        document = Document(
            doc_id=doc_id,
            title=title,
            chapter=chapter,
            section=section,
            content=content,
            content_hash=content_hash,
            vector_id=vector_id,
        )
        session.add(document)
        session.commit()
        logger.debug(f"✅ Added document: {doc_id}")
        return document
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error adding document: {e}")
        raise
    finally:
        session.close()
