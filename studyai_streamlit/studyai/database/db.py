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

Every table except ``users`` carries a ``user_id`` column so each account's
documents, chats, quizzes, flashcards and activity stay private to them.
``UserScopedDB`` (bottom of this file) is what pages actually use — it wraps
``Database`` and injects the signed-in user's id automatically, so callers
never have to thread it through by hand.
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
        uploaded_at TEXT NOT NULL,
        user_id     INTEGER NOT NULL DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS conversations (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role       TEXT NOT NULL,
        content    TEXT NOT NULL,
        sources    TEXT NOT NULL DEFAULT '[]',
        created_at TEXT NOT NULL,
        user_id    INTEGER NOT NULL DEFAULT 0
    )""",
    "CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id)",
    """CREATE TABLE IF NOT EXISTS quiz_attempts (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        topic      TEXT NOT NULL,
        subject    TEXT NOT NULL DEFAULT 'General',
        score      INTEGER NOT NULL,
        total      INTEGER NOT NULL,
        wrong      TEXT NOT NULL DEFAULT '[]',
        created_at TEXT NOT NULL,
        user_id    INTEGER NOT NULL DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS flashcards (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        front      TEXT NOT NULL,
        back       TEXT NOT NULL,
        topic      TEXT NOT NULL DEFAULT '',
        source     TEXT NOT NULL DEFAULT '',
        box        INTEGER NOT NULL DEFAULT 1,
        reviews    INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        user_id    INTEGER NOT NULL DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS activity (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        icon       TEXT NOT NULL DEFAULT 'GN',
        text       TEXT NOT NULL,
        kind       TEXT NOT NULL DEFAULT 'general',
        minutes    INTEGER NOT NULL DEFAULT 0,
        day        TEXT NOT NULL,
        created_at TEXT NOT NULL,
        user_id    INTEGER NOT NULL DEFAULT 0
    )""",
    # The FAISS index, chunk list and doc metadata for one user's vector
    # store, mirrored here so it survives a fresh container the same way the
    # tables above do — local disk under vectorstore/<user_id>/ is just a
    # fast-path cache of this row (see VectorStore's ``remote`` parameter).
    """CREATE TABLE IF NOT EXISTS vector_stores (
        user_id     INTEGER PRIMARY KEY,
        index_blob  BLOB NOT NULL,
        chunks_blob BLOB NOT NULL,
        meta_json   TEXT NOT NULL DEFAULT '{}',
        updated_at  TEXT NOT NULL
    )""",
]

# Tables that predate per-user scoping and may not have a user_id column yet
# on an already-initialized database (local file or existing Turso db). Their
# indexes are created separately, AFTER the migration below adds the column
# — an already-existing table won't have it yet when the CREATE TABLE IF NOT
# EXISTS statements above are no-ops.
_USER_SCOPED_TABLES = ("documents", "conversations", "quiz_attempts", "flashcards", "activity")
_USER_INDEX_STATEMENTS = [
    f"CREATE INDEX IF NOT EXISTS idx_{table}_user ON {table}(user_id)"
    for table in _USER_SCOPED_TABLES
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

    @staticmethod
    def _ensure_column(connection: Any, table: str, column: str, coldef: str) -> None:
        """Add ``column`` to ``table`` if a prior deploy created it without one."""
        try:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coldef}")
        except Exception:  # noqa: BLE001 - column already exists, nothing to do
            pass

    def _init_schema(self) -> None:
        with self.connect() as connection:
            for statement in _SCHEMA_STATEMENTS:
                connection.execute(statement)
            for table in _USER_SCOPED_TABLES:
                self._ensure_column(connection, table, "user_id",
                                     "INTEGER NOT NULL DEFAULT 0")
            for statement in _USER_INDEX_STATEMENTS:
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
    # Documents (user-scoped)
    # ------------------------------------------------------------------ #
    def add_document(self, user_id: int, doc: Dict[str, Any]) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO documents
                   (doc_id, name, subject, size_bytes, pages, chunk_count,
                    status, uploaded_at, user_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    doc["doc_id"], doc["name"], doc["subject"], doc["size_bytes"],
                    doc["pages"], doc["chunk_count"], doc.get("status", "analyzed"),
                    doc.get("uploaded_at", datetime.utcnow().isoformat()), user_id,
                ),
            )

    def list_documents(self, user_id: int) -> List[Dict[str, Any]]:
        with self.connect() as connection:
            cursor = connection.execute(
                "SELECT * FROM documents WHERE user_id = ? ORDER BY uploaded_at DESC",
                (user_id,),
            )
            return self._many(cursor, cursor.fetchall())

    def delete_document(self, user_id: int, doc_id: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "DELETE FROM documents WHERE doc_id = ? AND user_id = ?",
                (doc_id, user_id),
            )

    # ------------------------------------------------------------------ #
    # Conversations (user-scoped)
    # ------------------------------------------------------------------ #
    def add_message(
        self,
        user_id: int,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[List[dict]] = None,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO conversations (session_id, role, content, sources,
                                              created_at, user_id)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (session_id, role, content, json.dumps(sources or []),
                 datetime.utcnow().isoformat(), user_id),
            )

    def get_messages(self, user_id: int, session_id: str) -> List[Dict[str, Any]]:
        with self.connect() as connection:
            cursor = connection.execute(
                "SELECT * FROM conversations WHERE session_id = ? AND user_id = ? "
                "ORDER BY id",
                (session_id, user_id),
            )
            rows = self._many(cursor, cursor.fetchall())
        for row in rows:
            row["sources"] = json.loads(row["sources"])
        return rows

    def list_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """Return each session with its first message and turn count."""
        with self.connect() as connection:
            cursor = connection.execute(
                """SELECT session_id,
                          MIN(created_at) AS started,
                          COUNT(*)        AS turns
                   FROM conversations
                   WHERE user_id = ?
                   GROUP BY session_id
                   ORDER BY started DESC""",
                (user_id,),
            )
            return self._many(cursor, cursor.fetchall())

    def clear_session(self, user_id: int, session_id: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "DELETE FROM conversations WHERE session_id = ? AND user_id = ?",
                (session_id, user_id),
            )

    # ------------------------------------------------------------------ #
    # Quiz attempts (user-scoped)
    # ------------------------------------------------------------------ #
    def add_quiz_attempt(
        self,
        user_id: int,
        topic: str,
        subject: str,
        score: int,
        total: int,
        wrong: Optional[List[str]] = None,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO quiz_attempts (topic, subject, score, total, wrong,
                                              created_at, user_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (topic, subject, score, total, json.dumps(wrong or []),
                 datetime.utcnow().isoformat(), user_id),
            )

    def list_quiz_attempts(self, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        with self.connect() as connection:
            cursor = connection.execute(
                "SELECT * FROM quiz_attempts WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                (user_id, limit),
            )
            attempts = self._many(cursor, cursor.fetchall())
        for attempt in attempts:
            attempt["wrong"] = json.loads(attempt["wrong"])
        return attempts

    def wrong_answers(self, user_id: int, limit: int = 30) -> List[str]:
        """Flatten recent incorrect questions, for the Weak Topics agent."""
        collected: List[str] = []
        for attempt in self.list_quiz_attempts(user_id, limit=20):
            collected.extend(attempt["wrong"])
        return collected[:limit]

    # ------------------------------------------------------------------ #
    # Flashcards (user-scoped)
    # ------------------------------------------------------------------ #
    def add_flashcards(self, user_id: int, cards: List[Dict[str, Any]]) -> int:
        if not cards:
            return 0
        now = datetime.utcnow().isoformat()
        with self.connect() as connection:
            for card in cards:
                connection.execute(
                    """INSERT INTO flashcards (front, back, topic, source, created_at,
                                               user_id)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (card["front"], card["back"], card.get("topic", ""),
                     card.get("source", ""), now, user_id),
                )
        return len(cards)

    def list_flashcards(
        self, user_id: int, topic: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM flashcards WHERE user_id = ?"
        params: list = [user_id]
        if topic:
            query += " AND topic = ?"
            params.append(topic)
        query += " ORDER BY box ASC, id DESC"
        with self.connect() as connection:
            cursor = connection.execute(query, params)
            return self._many(cursor, cursor.fetchall())

    def review_flashcard(self, user_id: int, card_id: int, correct: bool) -> None:
        """Leitner-style box update: promote on success, reset on failure."""
        with self.connect() as connection:
            if correct:
                connection.execute(
                    """UPDATE flashcards
                       SET box = MIN(box + 1, 5), reviews = reviews + 1
                       WHERE id = ? AND user_id = ?""",
                    (card_id, user_id),
                )
            else:
                connection.execute(
                    "UPDATE flashcards SET box = 1, reviews = reviews + 1 "
                    "WHERE id = ? AND user_id = ?",
                    (card_id, user_id),
                )

    def delete_flashcards(self, user_id: int, topic: Optional[str] = None) -> None:
        with self.connect() as connection:
            if topic:
                connection.execute(
                    "DELETE FROM flashcards WHERE topic = ? AND user_id = ?",
                    (topic, user_id),
                )
            else:
                connection.execute(
                    "DELETE FROM flashcards WHERE user_id = ?", (user_id,)
                )

    # ------------------------------------------------------------------ #
    # Activity (user-scoped)
    # ------------------------------------------------------------------ #
    def log_activity(
        self,
        user_id: int,
        text: str,
        icon: str = "GN",
        kind: str = "general",
        minutes: int = 0,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO activity (icon, text, kind, minutes, day, created_at,
                                         user_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (icon, text, kind, minutes, date.today().isoformat(),
                 datetime.utcnow().isoformat(), user_id),
            )

    def recent_activity(self, user_id: int, limit: int = 8) -> List[Dict[str, Any]]:
        with self.connect() as connection:
            cursor = connection.execute(
                "SELECT * FROM activity WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                (user_id, limit),
            )
            return self._many(cursor, cursor.fetchall())

    def minutes_today(self, user_id: int) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                "SELECT COALESCE(SUM(minutes), 0) AS total FROM activity "
                "WHERE day = ? AND user_id = ?",
                (date.today().isoformat(), user_id),
            )
            row = self._one(cursor, cursor.fetchone())
        return int(row["total"]) if row else 0

    def streak(self, user_id: int) -> int:
        """Count consecutive days (ending today or yesterday) with activity."""
        with self.connect() as connection:
            cursor = connection.execute(
                "SELECT DISTINCT day FROM activity WHERE user_id = ? ORDER BY day DESC",
                (user_id,),
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

    def activity_by_day(self, user_id: int, days: int = 14) -> List[Dict[str, Any]]:
        with self.connect() as connection:
            cursor = connection.execute(
                """SELECT day, SUM(minutes) AS minutes, COUNT(*) AS events
                   FROM activity WHERE user_id = ? GROUP BY day ORDER BY day DESC
                   LIMIT ?""",
                (user_id, days),
            )
            rows = self._many(cursor, cursor.fetchall())
        return list(reversed(rows))

    # ------------------------------------------------------------------ #
    # Vector store (user-scoped) — remote backing for VectorStore, so the
    # FAISS index + chunks survive a fresh container the same way every
    # other table here does.
    # ------------------------------------------------------------------ #
    def save_vector_store(
        self, user_id: int, index_blob: bytes, chunks_blob: bytes, meta_json: str,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                "DELETE FROM vector_stores WHERE user_id = ?", (user_id,)
            )
            connection.execute(
                """INSERT INTO vector_stores
                   (user_id, index_blob, chunks_blob, meta_json, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, index_blob, chunks_blob, meta_json,
                 datetime.utcnow().isoformat()),
            )

    def load_vector_store(self, user_id: int) -> Optional[Dict[str, Any]]:
        with self.connect() as connection:
            cursor = connection.execute(
                "SELECT index_blob, chunks_blob, meta_json FROM vector_stores "
                "WHERE user_id = ?",
                (user_id,),
            )
            return self._one(cursor, cursor.fetchone())

    def delete_vector_store(self, user_id: int) -> None:
        with self.connect() as connection:
            connection.execute(
                "DELETE FROM vector_stores WHERE user_id = ?", (user_id,)
            )


class UserScopedDB:
    """
    Proxies a :class:`Database`, auto-injecting the signed-in user's id into
    every per-user query.

    This is what ``utils.session.get_database()`` hands to pages, so every
    existing ``db.list_documents()``-style call keeps working unchanged while
    actually only ever touching that one user's rows. Anything not
    overridden here (``get_user_by_email``, ``create_user``, ``.path``, …)
    falls straight through to the wrapped ``Database`` via ``__getattr__``.
    """

    def __init__(self, db: Database, user_id: Optional[int]) -> None:
        self._db = db
        self._user_id = user_id

    def __getattr__(self, name: str) -> Any:
        return getattr(self._db, name)

    # ---- Documents ---------------------------------------------------- #
    def add_document(self, doc: Dict[str, Any]) -> None:
        self._db.add_document(self._user_id, doc)

    def list_documents(self) -> List[Dict[str, Any]]:
        return self._db.list_documents(self._user_id)

    def delete_document(self, doc_id: str) -> None:
        self._db.delete_document(self._user_id, doc_id)

    # ---- Conversations -------------------------------------------------- #
    def add_message(
        self, session_id: str, role: str, content: str,
        sources: Optional[List[dict]] = None,
    ) -> None:
        self._db.add_message(self._user_id, session_id, role, content, sources)

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        return self._db.get_messages(self._user_id, session_id)

    def list_sessions(self) -> List[Dict[str, Any]]:
        return self._db.list_sessions(self._user_id)

    def clear_session(self, session_id: str) -> None:
        self._db.clear_session(self._user_id, session_id)

    # ---- Quiz attempts --------------------------------------------------- #
    def add_quiz_attempt(
        self, topic: str, subject: str, score: int, total: int,
        wrong: Optional[List[str]] = None,
    ) -> None:
        self._db.add_quiz_attempt(self._user_id, topic, subject, score, total, wrong)

    def list_quiz_attempts(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._db.list_quiz_attempts(self._user_id, limit)

    def wrong_answers(self, limit: int = 30) -> List[str]:
        return self._db.wrong_answers(self._user_id, limit)

    # ---- Flashcards -------------------------------------------------------- #
    def add_flashcards(self, cards: List[Dict[str, Any]]) -> int:
        return self._db.add_flashcards(self._user_id, cards)

    def list_flashcards(self, topic: Optional[str] = None) -> List[Dict[str, Any]]:
        return self._db.list_flashcards(self._user_id, topic)

    def review_flashcard(self, card_id: int, correct: bool) -> None:
        self._db.review_flashcard(self._user_id, card_id, correct)

    def delete_flashcards(self, topic: Optional[str] = None) -> None:
        self._db.delete_flashcards(self._user_id, topic)

    # ---- Activity -------------------------------------------------------- #
    def log_activity(
        self, text: str, icon: str = "GN", kind: str = "general", minutes: int = 0,
    ) -> None:
        self._db.log_activity(self._user_id, text, icon, kind, minutes)

    def recent_activity(self, limit: int = 8) -> List[Dict[str, Any]]:
        return self._db.recent_activity(self._user_id, limit)

    def minutes_today(self) -> int:
        return self._db.minutes_today(self._user_id)

    def streak(self) -> int:
        return self._db.streak(self._user_id)

    def activity_by_day(self, days: int = 14) -> List[Dict[str, Any]]:
        return self._db.activity_by_day(self._user_id, days)


class RemoteVectorBackend:
    """
    Adapts a :class:`Database` + user id into the tiny load/save/delete
    interface :class:`services.vectorstore.VectorStore` uses for optional
    remote persistence — so the FAISS index survives a fresh container
    instead of only ever living on local disk.
    """

    def __init__(self, db: Database, user_id: int) -> None:
        self._db = db
        self._user_id = user_id

    def load(self) -> Optional[Dict[str, Any]]:
        return self._db.load_vector_store(self._user_id)

    def save(self, index_blob: bytes, chunks_blob: bytes, meta_json: str) -> None:
        self._db.save_vector_store(self._user_id, index_blob, chunks_blob, meta_json)

    def delete(self) -> None:
        self._db.delete_vector_store(self._user_id)


_db: Optional[Database] = None


def get_db() -> Database:
    """Module-level singleton accessor for the raw (unscoped) database."""
    global _db
    if _db is None:
        _db = Database()
    return _db
