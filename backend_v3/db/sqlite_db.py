from __future__ import annotations

import sqlite3
from typing import List, Dict


class SQLiteDB:
    """
    Simple SQLite persistence for chat sessions + turns.

    Tables:
      - sessions(id TEXT PRIMARY KEY, created_at TEXT)
      - turns(id INTEGER PK, session_id TEXT, question TEXT, answer TEXT, created_at TEXT)
    """

    def __init__(self, db_path: str = "chatbot.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                )
                """
            )
            conn.commit()

    def ensure_session(self, session_id: str) -> None:
        with self._connect() as conn:
            conn.execute("INSERT OR IGNORE INTO sessions(id) VALUES(?)", (session_id,))
            conn.commit()

    def save_turn(self, session_id: str, question: str, answer: str) -> None:
        self.ensure_session(session_id)
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO turns(session_id, question, answer) VALUES(?,?,?)",
                (session_id, question, answer),
            )
            conn.commit()

    def get_history(self, session_id: str, limit: int = 6) -> List[Dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT question, answer
                FROM turns
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()

        rows = list(reversed(rows))
        return [{"question": r["question"], "answer": r["answer"]} for r in rows]
