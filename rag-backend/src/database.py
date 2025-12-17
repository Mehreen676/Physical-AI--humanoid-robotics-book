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
from sqlalchemy.orm import sessionmaker, Session as SQLSession, relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
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
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth users
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    # OAuth fields (Phase 5)
    oauth_provider = Column(String(50), nullable=True, index=True)  # "github", "google", or null
    oauth_id = Column(String(255), unique=True, nullable=True, index=True)  # Provider-specific user ID
    profile_picture = Column(String(500), nullable=True)  # URL to profile picture from OAuth
    # Admin fields (Phase 5)
    role = Column(String(50), default="user", nullable=False, index=True)  # "user", "admin"
    is_admin = Column(Boolean, default=False, index=True)  # Convenience flag
    # MFA fields (Phase 6)
    mfa_enabled = Column(Boolean, default=False, index=True)  # Whether MFA is active
    mfa_method = Column(String(50), nullable=True)  # "totp", "sms" (future)
    # Session tracking (Phase 6)
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<User(email={self.email}, is_active={self.is_active}, mfa_enabled={self.mfa_enabled})>"


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


class RevokedToken(Base):
    """Stores revoked JWT tokens for logout and security (Phase 5)."""

    __tablename__ = "revoked_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_jti = Column(String(255), unique=True, nullable=False, index=True)  # JWT ID (jti claim)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    revoked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)  # When token naturally expires
    reason = Column(String(100), nullable=True)  # "user_logout", "admin_revoke", "security"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<RevokedToken(user_id={self.user_id}, reason={self.reason})>"


# ============================================================================
# PHASE 6: ENTERPRISE AUTHENTICATION & SECURITY ENHANCEMENTS
# ============================================================================

class TOTPSecret(Base):
    """Stores TOTP (Time-based One-Time Password) configuration for MFA (Phase 6)."""

    __tablename__ = "totp_secrets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    secret = Column(String(32), nullable=False)  # Base32-encoded TOTP secret
    is_verified = Column(Boolean, default=False)  # True after user confirms setup
    backup_codes = Column(JSON, nullable=False, default=[])  # List of hashed backup codes
    enabled = Column(Boolean, default=False)  # Whether MFA is active
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)  # For audit
    recovery_codes_used = Column(Integer, default=0)  # Track backup code usage

    def __repr__(self):
        return f"<TOTPSecret(user_id={self.user_id}, enabled={self.enabled})>"


class RefreshToken(Base):
    """Stores refresh tokens for long-lived session management (Phase 6)."""

    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)  # SHA256 hash of token
    device_id = Column(String(255), nullable=True, index=True)  # User agent hash for device tracking
    device_name = Column(String(255), nullable=True)  # "Chrome on Windows", etc.
    ip_address = Column(String(50), nullable=True)  # For security audit
    is_revoked = Column(Boolean, default=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)  # 7-30 days
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True, index=True)
    rotated_from = Column(UUID(as_uuid=True), nullable=True)  # Track rotation chain

    def __repr__(self):
        return f"<RefreshToken(user_id={self.user_id}, device_name={self.device_name})>"


class APIKey(Base):
    """Stores API keys for programmatic access (Phase 6)."""

    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)  # SHA256(key)
    key_prefix = Column(String(8), nullable=False)  # First 8 chars for display
    name = Column(String(255), nullable=False)  # "Laptop API Key", "CI/CD Key"
    description = Column(Text, nullable=True)
    scopes = Column(JSON, nullable=False, default=["read:queries", "read:sessions"])  # Permission list
    is_active = Column(Boolean, default=True, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)  # Optional expiry
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    created_ip = Column(String(50), nullable=True)
    last_used_ip = Column(String(50), nullable=True)

    def __repr__(self):
        return f"<APIKey(user_id={self.user_id}, name={self.name}, is_active={self.is_active})>"


class Permission(Base):
    """Defines granular permissions for RBAC (Phase 6)."""

    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)  # "read:queries", "write:sessions"
    description = Column(Text, nullable=True)
    resource = Column(String(50), nullable=False)  # "queries", "sessions", "admin"
    action = Column(String(50), nullable=False)  # "read", "write", "delete", "admin"
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Permission(name={self.name})>"


class Role(Base):
    """Roles with permission assignments for RBAC (Phase 6)."""

    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False, index=True)  # "user", "admin", "viewer"
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)  # Default role for new users
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Role(name={self.name}, is_default={self.is_default})>"


class RolePermission(Base):
    """Association table for role-permission mapping (Phase 6)."""

    __tablename__ = "role_permissions"

    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)

    def __repr__(self):
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"


class UserRole(Base):
    """Assigns roles to users - supports multiple roles per user (Phase 6)."""

    __tablename__ = "user_roles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    assigned_by = Column(UUID(as_uuid=True), nullable=True)  # Admin who assigned role

    def __repr__(self):
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"


# Create indexes for common queries
Index("idx_documents_chapter", Document.chapter)
Index("idx_documents_book_version", Document.book_version)
Index("idx_documents_content_hash", Document.content_hash)
Index("idx_sessions_user_id", ChatSession.user_id)
Index("idx_sessions_book_version", ChatSession.book_version)
Index("idx_messages_session_created", Message.session_id, Message.created_at)
# Phase 5 - OAuth and Admin indexes
Index("idx_users_oauth_provider", User.oauth_provider)
Index("idx_users_role_active", User.role, User.is_active)  # For admin queries
# Phase 5 - Analytics performance indexes
Index("idx_query_metrics_user_created", QueryMetrics.user_id, QueryMetrics.created_at)  # For cohort analysis
Index("idx_sessions_user_activity", ChatSession.user_id, ChatSession.last_activity)  # For admin dashboard
# Phase 5 - Token revocation indexes
Index("idx_revoked_tokens_expires", RevokedToken.expires_at)  # For cleanup queries
# Phase 6 - MFA indexes
Index("idx_totp_user_id", TOTPSecret.user_id)  # For MFA setup/management
Index("idx_totp_enabled", TOTPSecret.enabled)  # For finding users with MFA enabled
# Phase 6 - Refresh token indexes
Index("idx_refresh_token_user_revoked", RefreshToken.user_id, RefreshToken.is_revoked)  # For device listing
Index("idx_refresh_token_expiry", RefreshToken.expires_at)  # For cleanup/rotation
# Phase 6 - API key indexes
Index("idx_api_key_user_active", APIKey.user_id, APIKey.is_active)  # For key listing
Index("idx_api_key_expiry", APIKey.expires_at)  # For cleanup
# Phase 6 - RBAC indexes
Index("idx_role_name", Role.name)  # For role lookups
Index("idx_role_default", Role.is_default)  # For finding default role
Index("idx_permission_resource_action", Permission.resource, Permission.action)  # For permission checks
Index("idx_user_role_user_id", UserRole.user_id)  # For finding user's roles


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


# ==================== Phase 5: OAuth & Token Revocation Functions ====================


def get_user_by_oauth_id(oauth_provider: str, oauth_id: str) -> User:
    """Get user by OAuth provider and ID."""
    db = get_db()
    session = db.get_session()
    try:
        user = (
            session.query(User)
            .filter_by(oauth_provider=oauth_provider, oauth_id=oauth_id)
            .first()
        )
        return user
    finally:
        session.close()


def create_oauth_user(
    email: str,
    oauth_provider: str,
    oauth_id: str,
    full_name: str = None,
    profile_picture: str = None,
) -> User:
    """Create a new user from OAuth provider."""
    db = get_db()
    session = db.get_session()
    try:
        # Check if user already exists by email
        existing = session.query(User).filter_by(email=email).first()
        if existing:
            # Update with OAuth info if not already set
            if not existing.oauth_provider:
                existing.oauth_provider = oauth_provider
                existing.oauth_id = oauth_id
                if profile_picture:
                    existing.profile_picture = profile_picture
                session.commit()
            return existing

        # Create new OAuth user
        user = User(
            email=email,
            password_hash=None,  # OAuth users don't have passwords
            full_name=full_name,
            oauth_provider=oauth_provider,
            oauth_id=oauth_id,
            profile_picture=profile_picture,
            is_active=True,
            role="user",
            is_admin=False,
        )
        session.add(user)
        session.commit()
        logger.info(f"✅ Created OAuth user: {email} ({oauth_provider})")
        return user
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error creating OAuth user: {e}")
        raise
    finally:
        session.close()


def revoke_token(token_jti: str, user_id: str, reason: str = "user_logout", expires_at: datetime = None) -> RevokedToken:
    """Add a JWT token to the revocation blacklist."""
    db = get_db()
    session = db.get_session()
    try:
        # If no expiry time provided, assume 24 hours from now
        if expires_at is None:
            expires_at = datetime.utcnow() + timedelta(hours=24)

        revoked = RevokedToken(
            token_jti=token_jti,
            user_id=user_id,
            expires_at=expires_at,
            reason=reason,
        )
        session.add(revoked)
        session.commit()
        logger.debug(f"✅ Revoked token: {token_jti[:8]}... (reason: {reason})")
        return revoked
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error revoking token: {e}")
        raise
    finally:
        session.close()


def is_token_revoked(token_jti: str) -> bool:
    """Check if a JWT token is on the revocation blacklist."""
    db = get_db()
    session = db.get_session()
    try:
        revoked = session.query(RevokedToken).filter_by(token_jti=token_jti).first()
        return revoked is not None
    finally:
        session.close()


def cleanup_expired_revoked_tokens() -> int:
    """Remove expired tokens from revocation blacklist (maintenance task)."""
    db = get_db()
    session = db.get_session()
    try:
        now = datetime.utcnow()
        deleted = (
            session.query(RevokedToken)
            .filter(RevokedToken.expires_at < now)
            .delete()
        )
        session.commit()
        if deleted > 0:
            logger.info(f"✅ Cleaned up {deleted} expired revoked tokens")
        return deleted
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error cleaning up revoked tokens: {e}")
        raise
    finally:
        session.close()


# ==================== Wave 5: Advanced Analytics (Phase 5) ====================

def get_user_cohort_analytics(cohort_start: datetime, cohort_end: datetime) -> dict:
    """Get analytics for users who signed up in a date range (cohort analysis)."""
    db = get_db()
    session = db.get_session()
    try:
        from sqlalchemy import func
        
        # Users created in date range
        cohort_users = session.query(User).filter(
            User.created_at >= cohort_start,
            User.created_at <= cohort_end
        ).all()
        
        total_users = len(cohort_users)
        if total_users == 0:
            return {
                "cohort_start": cohort_start.isoformat(),
                "cohort_end": cohort_end.isoformat(),
                "total_users": 0,
                "active_users": 0,
                "avg_queries_per_user": 0,
                "avg_session_duration_minutes": 0,
            }
        
        user_ids = [str(u.id) for u in cohort_users]
        
        # Query metrics for cohort
        metrics = session.query(QueryMetrics).filter(
            QueryMetrics.user_id.in_(user_ids)
        ).all()
        
        total_queries = len(metrics)
        avg_queries = total_queries / total_users if total_users > 0 else 0
        
        # Active users (those who made at least 1 query)
        active_user_ids = set(str(m.user_id) for m in metrics)
        active_users = len(active_user_ids)
        
        logger.info(f"📊 Cohort analysis: {total_users} users, {total_queries} queries")
        return {
            "cohort_start": cohort_start.isoformat(),
            "cohort_end": cohort_end.isoformat(),
            "total_users": total_users,
            "active_users": active_users,
            "avg_queries_per_user": round(avg_queries, 2),
            "retention_rate": round((active_users / total_users * 100), 2) if total_users > 0 else 0,
        }
    finally:
        session.close()


def get_funnel_metrics() -> dict:
    """Get conversion funnel metrics."""
    db = get_db()
    session = db.get_session()
    try:
        from sqlalchemy import func
        
        # Total users
        total_users = session.query(func.count(User.id)).scalar() or 0
        
        # Users with at least 1 query
        users_with_queries = session.query(
            func.count(func.distinct(QueryMetrics.user_id))
        ).scalar() or 0
        
        # Users with 5+ queries
        user_query_counts = session.query(
            QueryMetrics.user_id,
            func.count(QueryMetrics.id).label('count')
        ).group_by(QueryMetrics.user_id).all()
        
        users_5plus = len([u for u in user_query_counts if u.count >= 5])
        users_10plus = len([u for u in user_query_counts if u.count >= 10])
        
        # Calculate conversion rates
        step1_rate = (users_with_queries / total_users * 100) if total_users > 0 else 0
        step2_rate = (users_5plus / total_users * 100) if total_users > 0 else 0
        step3_rate = (users_10plus / total_users * 100) if total_users > 0 else 0
        
        logger.info(f"🔝 Funnel: Signup→Query: {step1_rate:.1f}%, Query→5x: {step2_rate:.1f}%, Query→10x: {step3_rate:.1f}%")
        return {
            "total_signups": total_users,
            "users_with_1plus_query": users_with_queries,
            "users_with_5plus_queries": users_5plus,
            "users_with_10plus_queries": users_10plus,
            "signup_to_query_conversion": round(step1_rate, 2),
            "query_to_5x_conversion": round(step2_rate, 2),
            "query_to_10x_conversion": round(step3_rate, 2),
        }
    finally:
        session.close()


# ==================== Wave 6: Performance Optimization (Phase 5) ====================

def optimize_analytics_aggregations():
    """Optimize analytics queries using SQL aggregations instead of Python."""
    from sqlalchemy import func
    db = get_db()
    session = db.get_session()
    try:
        # Pre-calculate and cache common aggregations
        result = session.query(
            func.count(QueryMetrics.id).label('total_queries'),
            func.avg(QueryMetrics.response_time_ms).label('avg_response_time'),
            func.sum(QueryMetrics.input_tokens + QueryMetrics.output_tokens).label('total_tokens'),
            func.avg(func.cast(QueryMetrics.success, Integer)).label('success_rate')
        ).first()
        
        logger.info("✅ Analytics aggregations optimized with SQL")
        return {
            "total_queries": result.total_queries or 0,
            "avg_response_time_ms": float(result.avg_response_time or 0),
            "total_tokens": result.total_tokens or 0,
            "success_rate": float(result.success_rate or 0),
        }
    finally:
        session.close()
