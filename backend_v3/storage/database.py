"""Database layer supporting both Neon Postgres and SQLite."""

import os
import uuid
from typing import List, Dict, Optional
from datetime import datetime


class Database:
    """Abstract database interface."""

    def create_session(self, user_id: Optional[str] = None) -> str:
        """Create new conversation session."""
        raise NotImplementedError

    def add_turn(
        self,
        session_id: str,
        question: str,
        retrieval_mode: str,
        context_chunk_ids: List[str],
        answer: str,
        grounded: bool
    ) -> None:
        """Add chat turn to session."""
        raise NotImplementedError

    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for session."""
        raise NotImplementedError

    def session_exists(self, session_id: str) -> bool:
        """Check if session exists."""
        raise NotImplementedError


class SQLiteDatabase(Database):
    """SQLite database for local development."""

    def __init__(self, db_path: str = "chatbot.db"):
        """
        Initialize SQLite database.

        Args:
            db_path: Path to SQLite database file
        """
        import sqlite3
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        """Initialize database schema."""
        cursor = self.conn.cursor()

        # Create sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create chat_turns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_turns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                question TEXT NOT NULL,
                retrieval_mode TEXT NOT NULL,
                context_chunk_ids TEXT,
                answer TEXT NOT NULL,
                grounded INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)

        # Create index
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_turns
            ON chat_turns(session_id, created_at)
        """)

        self.conn.commit()

    def create_session(self, user_id: Optional[str] = None) -> str:
        """Create new conversation session."""
        session_id = str(uuid.uuid4())
        cursor = self.conn.cursor()

        cursor.execute(
            "INSERT INTO sessions (id, user_id) VALUES (?, ?)",
            (session_id, user_id)
        )
        self.conn.commit()

        return session_id

    def add_turn(
        self,
        session_id: str,
        question: str,
        retrieval_mode: str,
        context_chunk_ids: List[str],
        answer: str,
        grounded: bool
    ) -> None:
        """Add chat turn to session."""
        cursor = self.conn.cursor()

        # Convert list to JSON string
        import json
        chunk_ids_json = json.dumps(context_chunk_ids)

        cursor.execute("""
            INSERT INTO chat_turns
            (session_id, question, retrieval_mode, context_chunk_ids, answer, grounded)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, question, retrieval_mode, chunk_ids_json, answer, int(grounded)))

        self.conn.commit()

    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for session."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT question, answer, retrieval_mode, grounded, created_at
            FROM chat_turns
            WHERE session_id = ?
            ORDER BY created_at ASC
        """, (session_id,))

        rows = cursor.fetchall()

        return [
            {
                "question": row["question"],
                "answer": row["answer"],
                "retrieval_mode": row["retrieval_mode"],
                "grounded": bool(row["grounded"]),
                "created_at": row["created_at"]
            }
            for row in rows
        ]

    def session_exists(self, session_id: str) -> bool:
        """Check if session exists."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM sessions WHERE id = ?", (session_id,))
        return cursor.fetchone() is not None


class NeonDatabase(Database):
    """Neon Serverless Postgres database."""

    def __init__(self, database_url: str):
        """
        Initialize Neon database.

        Args:
            database_url: Neon database connection URL
        """
        import psycopg2
        from psycopg2.extras import RealDictCursor

        self.database_url = database_url
        self.conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        self._init_schema()

    def _init_schema(self):
        """Initialize database schema."""
        cursor = self.conn.cursor()

        # Create sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id UUID PRIMARY KEY,
                user_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Create chat_turns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_turns (
                id SERIAL PRIMARY KEY,
                session_id UUID REFERENCES sessions(id),
                question TEXT NOT NULL,
                retrieval_mode VARCHAR(20) NOT NULL,
                context_chunk_ids TEXT[],
                answer TEXT NOT NULL,
                grounded BOOLEAN NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Create index
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_turns
            ON chat_turns(session_id, created_at)
        """)

        self.conn.commit()

    def create_session(self, user_id: Optional[str] = None) -> str:
        """Create new conversation session."""
        session_id = str(uuid.uuid4())
        cursor = self.conn.cursor()

        cursor.execute(
            "INSERT INTO sessions (id, user_id) VALUES (%s, %s)",
            (session_id, user_id)
        )
        self.conn.commit()

        return session_id

    def add_turn(
        self,
        session_id: str,
        question: str,
        retrieval_mode: str,
        context_chunk_ids: List[str],
        answer: str,
        grounded: bool
    ) -> None:
        """Add chat turn to session."""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO chat_turns
            (session_id, question, retrieval_mode, context_chunk_ids, answer, grounded)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (session_id, question, retrieval_mode, context_chunk_ids, answer, grounded))

        self.conn.commit()

    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for session."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT question, answer, retrieval_mode, grounded, created_at
            FROM chat_turns
            WHERE session_id = %s
            ORDER BY created_at ASC
        """, (session_id,))

        return cursor.fetchall()

    def session_exists(self, session_id: str) -> bool:
        """Check if session exists."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM sessions WHERE id = %s", (session_id,))
        return cursor.fetchone() is not None


def get_database() -> Database:
    """
    Get database instance based on configuration.

    Returns:
        Database instance (Neon or SQLite)
    """
    database_url = os.getenv("DATABASE_URL")

    if database_url and database_url.startswith("postgres"):
        # Use Neon Postgres
        return NeonDatabase(database_url)
    else:
        # Use SQLite for local development
        db_path = os.getenv("SQLITE_DB_PATH", "chatbot.db")
        return SQLiteDatabase(db_path)
