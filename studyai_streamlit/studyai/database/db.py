"""
Persistence layer.

Uses Turso (a hosted, libSQL-compatible SQLite database) when
``TURSO_DATABASE_URL`` / ``TURSO_AUTH_TOKEN`` are configured, so accounts and
study data survive Streamlit Cloud redeploys — Cloud rebuilds the app in a
fresh container on every deploy, which silently wipes a local SQLite file.
Falls back to a local SQLite file when Turso isn't configured, which is fine
for local development.

Row access never relies on ``sqlite3.Row``/``row_factory`` so the exact same
code path works against either backend: every row is converted to a plain
dict via the cursor's ``description``, which both drivers expose.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from config import DATABASE_PATH, settings
from utils.logger import get_logger

logger = get_logger(__name__)

_SCHEMA_STATEMENTS = [
    """CREATE TABLE IF NOT EXISTS users (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        name          TEXT NOT NULL,
        email         TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        password_salt TEXT NOT NULL,
        semester      TEXT NOT NULL DEFAULT 'Semester 5',
        avatar        TEXT NOT NULL DEFAULT 'ST',
        created_at    TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS documents (
        doc_id      TEXT PRIMARY KEY,
        name        TEXT NOT NULL,
        subject     TEXT NOT NULL,
        size_bytes  INTEGER NOT NULL,
        pages       INTEGER NOT NULL,
        chunk_count INTEGER NOT NULL,
        status      TEXT NOT NULL DEFAULT 'analyzed',
        uploaded_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS conversations (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role       TEXT NOT NULL,
        content    TEXT NOT NULL,
        sources    TEXT NOT NULL DEFAULT '[]',
        created_at TEXT NOT NULL
    )""",
    "CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id)",
    """CREATE TABLE IF NOT EXISTS quiz_attempts (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        topic      TEXT NOT NULL,
        subject    TEXT NOT NULL DEFAULT 'General',
        score      INTEGER NOT NULL,
        total      INTEGER NOT NULL,
        wrong      TEXT NOT NULL DEFAULT '[]',
        created_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS flashcards (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        front      TEXT NOT NULL,
        back       TEXT NOT NULL,
        topic      TEXT NOT NULL DEFAULT '',
        source     TEXT NOT NULL DEFAULT '',
        box        INTEGER NOT NULL DEFAULT 1,
        reviews    INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS activity (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        icon       TEXT NOT NULL DEFAULT 'GN',
        text       TEXT NOT NULL,
        kind       TEXT NOT NULL DEFAULT 'general',
        minutes    INTEGER NOT NULL DEFAULT 0,
        day        TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""",
]


class Database:
    """Data access layer over either Turso (persistent) or local SQLite."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.use_turso = settings.uses_turso
        if self.use_turso:
            self.path = None
        else:
            self.path = Path(path or DATABASE_PATH)
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def connect(self) -> Iterator[Any]:
        """Yield a connection to whichever backend is configured."""
        if self.use_turso:
            import libsql

            connection = libsql.connect(
                database=settings.turso_database_url,
                auth_token=settings.turso_auth_token,
            )
        else:
            connection = sqlite3.connect(self.path, check_same_thread=False)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _one(cursor: Any, row: Any) -> Optional[Dict[str, Any]]:
        if row is None:
            return None
        columns = [d[0] for d in cursor.description]
        return dict(zip(columns, row))

    @staticmethod
    def _many(cursor: Any, rows: Any) -> List[Dict[str, Any]]:
        columns = [d[0] for d in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    def _init_schema(self) -> None:
        with self.connect() as connection:
            for statement in _SCHEMA_STATEMENTS:
                connection.execute(statement)
        logger.info(
            "Database ready (%s)", "Turso" if self.use_turso else f"local: {self.path}"
        )

    # ------------------------------------------------------------------ #
    # Users
    # ------------------------------------------------------------------ #
    def create_user(
        self,
        name: str,
        email: str,
        password_hash: str,
        password_salt: str,
        semester: str = "Semester 5",
    ) -> Dict[str, Any]:
        avatar = "".join(part[0] for part in name.split()[:2]).upper() or "ST"
        clean_email = email.lower()
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO users
                   (name, email, password_hash, password_salt, semester, avatar,
                    created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (name, clean_email, password_hash, password_salt, semester,
                 avatar, datetime.utcnow().isoformat()),
            )
        return self.get_user_by_email(clean_email)

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        with self.connect() as connection:
            cursor = connection.execute(
                "SELECT * FROM users WHERE email = ?", (email.lower(),)
            )
            return self._one(cursor, cursor.fetchone())

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        with self.connect() as connection:
            cursor = connection.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            )
            return self._one(cursor, cursor.fetchone())

    def update_user(self, user_id: int, **fields: Any) -> None:
        """Update arbitrary columns, e.g. ``update_user(1, name=..., email=...)``."""
        if not fields:
            return
        assignments = ", ".join(f"{column} = ?" for column in fields)
        with self.connect() as connection:
            connection.execute(
                f"UPDATE users SET {assignments} WHERE id = ?",
                (*fields.values(), user_id),
            )

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
            cursor = connection.execute(
                "SELECT * FROM documents ORDER BY uploaded_at DESC"
            )
            return self._many(cursor, cursor.fetchall())

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
            cursor = connection.execute(
                "SELECT * FROM conversations WHERE session_id = ? ORDER BY id",
                (session_id,),
            )
            rows = self._many(cursor, cursor.fetchall())
        for row in rows:
            row["sources"] = json.loads(row["sources"])
        return rows

    def list_sessions(self) -> List[Dict[str, Any]]:
        """Return each session with its first message and turn count."""
        with self.connect() as connection:
            cursor = connection.execute(
                """SELECT session_id,
                          MIN(created_at) AS started,
                          COUNT(*)        AS turns
                   FROM conversations
                   GROUP BY session_id
                   ORDER BY started DESC"""
            )
            return self._many(cursor, cursor.fetchall())

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
            cursor = connection.execute(
                "SELECT * FROM quiz_attempts ORDER BY id DESC LIMIT ?", (limit,)
            )
            attempts = self._many(cursor, cursor.fetchall())
        for attempt in attempts:
            attempt["wrong"] = json.loads(attempt["wrong"])
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
            for card in cards:
                connection.execute(
                    """INSERT INTO flashcards (front, back, topic, source, created_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (card["front"], card["back"], card.get("topic", ""),
                     card.get("source", ""), now),
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
            cursor = connection.execute(query, params)
            return self._many(cursor, cursor.fetchall())

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
        icon: str = "GN",
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
            cursor = connection.execute(
                "SELECT * FROM activity ORDER BY id DESC LIMIT ?", (limit,)
            )
            return self._many(cursor, cursor.fetchall())

    def minutes_today(self) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                "SELECT COALESCE(SUM(minutes), 0) AS total FROM activity WHERE day = ?",
                (date.today().isoformat(),),
            )
            row = self._one(cursor, cursor.fetchone())
        return int(row["total"]) if row else 0

    def streak(self) -> int:
        """Count consecutive days (ending today or yesterday) with activity."""
        with self.connect() as connection:
            cursor = connection.execute(
                "SELECT DISTINCT day FROM activity ORDER BY day DESC"
            )
            rows = self._many(cursor, cursor.fetchall())
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
            cursor = connection.execute(
                """SELECT day, SUM(minutes) AS minutes, COUNT(*) AS events
                   FROM activity GROUP BY day ORDER BY day DESC LIMIT ?""",
                (days,),
            )
            rows = self._many(cursor, cursor.fetchall())
        return list(reversed(rows))


_db: Optional[Database] = None


def get_db() -> Database:
    """Module-level singleton accessor."""
    global _db
    if _db is None:
        _db = Database()
    return _db
