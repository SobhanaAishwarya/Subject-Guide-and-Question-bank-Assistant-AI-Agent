"""
SQLite persistence.

Replaces the mock in-memory arrays from the original Next.js components with a
real, queryable store for documents, chat history, quiz attempts, flashcards and
study activity.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from config import DATABASE_PATH
from utils.logger import get_logger

logger = get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id      TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    subject     TEXT NOT NULL,
    size_bytes  INTEGER NOT NULL,
    pages       INTEGER NOT NULL,
    chunk_count INTEGER NOT NULL,
    status      TEXT NOT NULL DEFAULT 'analyzed',
    uploaded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role       TEXT NOT NULL,
    content    TEXT NOT NULL,
    sources    TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id);

CREATE TABLE IF NOT EXISTS quiz_attempts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    topic      TEXT NOT NULL,
    subject    TEXT NOT NULL DEFAULT 'General',
    score      INTEGER NOT NULL,
    total      INTEGER NOT NULL,
    wrong      TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS flashcards (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    front      TEXT NOT NULL,
    back       TEXT NOT NULL,
    topic      TEXT NOT NULL DEFAULT '',
    source     TEXT NOT NULL DEFAULT '',
    box        INTEGER NOT NULL DEFAULT 1,
    reviews    INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activity (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    icon       TEXT NOT NULL DEFAULT '✨',
    text       TEXT NOT NULL,
    kind       TEXT NOT NULL DEFAULT 'general',
    minutes    INTEGER NOT NULL DEFAULT 0,
    day        TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


class Database:
    """Small, dependency-free data access layer over SQLite."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = Path(path or DATABASE_PATH)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        """Yield a row-dict connection, committing on success."""
        connection = sqlite3.connect(self.path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _init_schema(self) -> None:
        with self.connect() as connection:
            connection.executescript(_SCHEMA)
        logger.info("Database ready at %s", self.path)

    # ------------------------------------------------------------------ #
    # Documents
    # ------------------------------------------------------------------ #
    def add_document(self, doc: Dict[str, Any]) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO documents
                   (doc_id, name, subject, size_bytes, pages, chunk_count,
                    status, uploaded_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    doc["doc_id"], doc["name"], doc["subject"], doc["size_bytes"],
                    doc["pages"], doc["chunk_count"], doc.get("status", "analyzed"),
                    doc.get("uploaded_at", datetime.utcnow().isoformat()),
                ),
            )

    def list_documents(self) -> List[Dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM documents ORDER BY uploaded_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_document(self, doc_id: str) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))

    # ------------------------------------------------------------------ #
    # Conversations
    # ------------------------------------------------------------------ #
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[List[dict]] = None,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO conversations (session_id, role, content, sources,
                                              created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (session_id, role, content, json.dumps(sources or []),
                 datetime.utcnow().isoformat()),
            )

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM conversations WHERE session_id = ? ORDER BY id",
                (session_id,),
            ).fetchall()
        messages = []
        for row in rows:
            item = dict(row)
            item["sources"] = json.loads(item["sources"])
            messages.append(item)
        return messages

    def list_sessions(self) -> List[Dict[str, Any]]:
        """Return each session with its first message and turn count."""
        with self.connect() as connection:
            rows = connection.execute(
                """SELECT session_id,
                          MIN(created_at) AS started,
                          COUNT(*)        AS turns
                   FROM conversations
                   GROUP BY session_id
                   ORDER BY started DESC"""
            ).fetchall()
        return [dict(row) for row in rows]

    def clear_session(self, session_id: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "DELETE FROM conversations WHERE session_id = ?", (session_id,)
            )

    # ------------------------------------------------------------------ #
    # Quiz attempts
    # ------------------------------------------------------------------ #
    def add_quiz_attempt(
        self,
        topic: str,
        subject: str,
        score: int,
        total: int,
        wrong: Optional[List[str]] = None,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO quiz_attempts (topic, subject, score, total, wrong,
                                              created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (topic, subject, score, total, json.dumps(wrong or []),
                 datetime.utcnow().isoformat()),
            )

    def list_quiz_attempts(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM quiz_attempts ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        attempts = []
        for row in rows:
            item = dict(row)
            item["wrong"] = json.loads(item["wrong"])
            attempts.append(item)
        return attempts

    def wrong_answers(self, limit: int = 30) -> List[str]:
        """Flatten recent incorrect questions, for the Weak Topics agent."""
        collected: List[str] = []
        for attempt in self.list_quiz_attempts(limit=20):
            collected.extend(attempt["wrong"])
        return collected[:limit]

    # ------------------------------------------------------------------ #
    # Flashcards
    # ------------------------------------------------------------------ #
    def add_flashcards(self, cards: List[Dict[str, Any]]) -> int:
        if not cards:
            return 0
        now = datetime.utcnow().isoformat()
        with self.connect() as connection:
            connection.executemany(
                """INSERT INTO flashcards (front, back, topic, source, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                [(c["front"], c["back"], c.get("topic", ""), c.get("source", ""), now)
                 for c in cards],
            )
        return len(cards)

    def list_flashcards(self, topic: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM flashcards"
        params: tuple = ()
        if topic:
            query += " WHERE topic = ?"
            params = (topic,)
        query += " ORDER BY box ASC, id DESC"
        with self.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def review_flashcard(self, card_id: int, correct: bool) -> None:
        """Leitner-style box update: promote on success, reset on failure."""
        with self.connect() as connection:
            if correct:
                connection.execute(
                    """UPDATE flashcards
                       SET box = MIN(box + 1, 5), reviews = reviews + 1
                       WHERE id = ?""",
                    (card_id,),
                )
            else:
                connection.execute(
                    "UPDATE flashcards SET box = 1, reviews = reviews + 1 WHERE id = ?",
                    (card_id,),
                )

    def delete_flashcards(self, topic: Optional[str] = None) -> None:
        with self.connect() as connection:
            if topic:
                connection.execute("DELETE FROM flashcards WHERE topic = ?", (topic,))
            else:
                connection.execute("DELETE FROM flashcards")

    # ------------------------------------------------------------------ #
    # Activity
    # ------------------------------------------------------------------ #
    def log_activity(
        self,
        text: str,
        icon: str = "✨",
        kind: str = "general",
        minutes: int = 0,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO activity (icon, text, kind, minutes, day, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (icon, text, kind, minutes, date.today().isoformat(),
                 datetime.utcnow().isoformat()),
            )

    def recent_activity(self, limit: int = 8) -> List[Dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM activity ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in rows]

    def minutes_today(self) -> int:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT COALESCE(SUM(minutes), 0) AS total FROM activity WHERE day = ?",
                (date.today().isoformat(),),
            ).fetchone()
        return int(row["total"])

    def streak(self) -> int:
        """Count consecutive days (ending today or yesterday) with activity."""
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT DISTINCT day FROM activity ORDER BY day DESC"
            ).fetchall()
        days = [datetime.fromisoformat(r["day"]).date() for r in rows]
        if not days:
            return 0

        today = date.today()
        if (today - days[0]).days > 1:
            return 0

        streak = 1
        for previous, current in zip(days, days[1:]):
            if (previous - current).days == 1:
                streak += 1
            else:
                break
        return streak

    def activity_by_day(self, days: int = 14) -> List[Dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """SELECT day, SUM(minutes) AS minutes, COUNT(*) AS events
                   FROM activity GROUP BY day ORDER BY day DESC LIMIT ?""",
                (days,),
            ).fetchall()
        return [dict(row) for row in reversed(rows)]


_db: Optional[Database] = None


def get_db() -> Database:
    """Module-level singleton accessor."""
    global _db
    if _db is None:
        _db = Database()
    return _db
