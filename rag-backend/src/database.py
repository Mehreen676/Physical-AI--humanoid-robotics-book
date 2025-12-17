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
import bcrypt

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


class User(Base):
    """Stores user accounts for authentication and session ownership."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<User(email={self.email}, is_active={self.is_active})>"


class QueryMetrics(Base):
    """Stores query metrics for analytics and performance tracking."""

    __tablename__ = "query_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    session_id = Column(String(255), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    query_text = Column(Text, nullable=False)
    response_time_ms = Column(Integer, nullable=False)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    model_used = Column(String(100), nullable=False)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<QueryMetrics(user_id={self.user_id}, response_time_ms={self.response_time_ms})>"


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


# Password hashing utilities (Phase 4)

def hash_password(password: str) -> str:
    """Hash a password using bcrypt (12 rounds)."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


# User management functions (Phase 4)

def add_user(email: str, password: str, full_name: str = None) -> User:
    """Create a new user account."""
    db = get_db()
    session = db.get_session()
    try:
        # Check if user already exists
        existing = session.query(User).filter_by(email=email).first()
        if existing:
            logger.warning(f"⚠️ User already exists: {email}")
            raise ValueError("Email already registered")

        password_hash = hash_password(password)
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
        )
        session.add(user)
        session.commit()
        logger.info(f"✅ Created user: {email}")
        return user
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error creating user: {e}")
        raise
    finally:
        session.close()


def get_user_by_email(email: str) -> User:
    """Retrieve a user by email."""
    db = get_db()
    session = db.get_session()
    try:
        user = session.query(User).filter_by(email=email).first()
        return user
    finally:
        session.close()


def get_user_by_id(user_id: str) -> User:
    """Retrieve a user by ID."""
    db = get_db()
    session = db.get_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        return user
    finally:
        session.close()


def get_user_sessions(user_id: str, limit: int = 50, offset: int = 0) -> list:
    """Get all sessions for a user."""
    db = get_db()
    session = db.get_session()
    try:
        sessions = (
            session.query(ChatSession)
            .filter_by(user_id=str(user_id))
            .order_by(ChatSession.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return sessions
    finally:
        session.close()


def add_query_metric(
    session_id: str,
    query_text: str,
    response_time_ms: int,
    model_used: str = "gpt-4o",
    input_tokens: int = None,
    output_tokens: int = None,
    user_id: str = None,
    success: bool = True,
    error_message: str = None,
) -> QueryMetrics:
    """Record a query metric for analytics."""
    db = get_db()
    session = db.get_session()
    try:
        metric = QueryMetrics(
            user_id=user_id,
            session_id=session_id,
            query_text=query_text,
            response_time_ms=response_time_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_used=model_used,
            success=success,
            error_message=error_message,
        )
        session.add(metric)
        session.commit()
        logger.debug(f"✅ Recorded query metric: {session_id} ({response_time_ms}ms)")
        return metric
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error recording query metric: {e}")
        raise
    finally:
        session.close()


def get_user_analytics(user_id: str) -> dict:
    """Get aggregate analytics for a user."""
    db = get_db()
    session = db.get_session()
    try:
        metrics = session.query(QueryMetrics).filter_by(user_id=user_id).all()

        if not metrics:
            return {
                "total_queries": 0,
                "avg_response_time_ms": 0,
                "total_tokens_used": 0,
                "success_rate": 0.0,
            }

        total_queries = len(metrics)
        avg_response_time = sum(m.response_time_ms for m in metrics) / total_queries
        total_tokens = sum((m.input_tokens or 0) + (m.output_tokens or 0) for m in metrics)
        successful = sum(1 for m in metrics if m.success)
        success_rate = (successful / total_queries * 100) if total_queries > 0 else 0

        return {
            "total_queries": total_queries,
            "avg_response_time_ms": round(avg_response_time, 2),
            "total_tokens_used": total_tokens,
            "success_rate": round(success_rate, 2),
        }
    finally:
        session.close()
