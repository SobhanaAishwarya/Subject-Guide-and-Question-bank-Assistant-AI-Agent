"""Typed data structures shared across services and UI components."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


@dataclass
class User:
    """An account holder. Never carries the password hash/salt — those stay
    in the database layer and are only touched by ``services.auth``."""

    name: str
    email: str
    semester: str = "Semester 5"
    avatar: str = "ST"
    id: Optional[int] = None
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Chunk:
    """A single retrievable slice of a document."""

    text: str
    source: str
    page: Optional[int] = None
    chunk_index: int = 0
    subject: str = "General"
    doc_id: str = field(default_factory=_new_id)

    @property
    def citation(self) -> str:
        """Human readable citation label, e.g. ``OS_Unit1.pdf, p. 12``."""
        return f"{self.source}, p. {self.page}" if self.page else self.source

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Chunk":
        return Chunk(**data)


@dataclass
class RetrievedChunk:
    """A chunk returned by semantic search, with its similarity score."""

    chunk: Chunk
    score: float

    def to_dict(self) -> Dict[str, Any]:
        return {"chunk": self.chunk.to_dict(), "score": self.score}


@dataclass
class Document:
    """Metadata for an uploaded and indexed document."""

    name: str
    subject: str
    size_bytes: int
    pages: int
    chunk_count: int
    status: str = "analyzed"          # pending | analyzing | analyzed | failed
    doc_id: str = field(default_factory=_new_id)
    uploaded_at: str = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Message:
    """One turn of a chat conversation."""

    role: str                          # "user" | "assistant"
    content: str
    sources: List[Dict[str, Any]] = field(default_factory=list)
    related: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Answer:
    """The result of a RAG query."""

    text: str
    sources: List[RetrievedChunk] = field(default_factory=list)
    related_questions: List[str] = field(default_factory=list)
    grounded: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "sources": [s.to_dict() for s in self.sources],
            "related_questions": self.related_questions,
            "grounded": self.grounded,
        }


@dataclass
class QuizQuestion:
    """A single multiple-choice question."""

    question: str
    options: List[str]
    answer_index: int
    explanation: str = ""
    source: str = ""
    difficulty: str = "medium"


@dataclass
class Flashcard:
    """A single spaced-repetition flashcard."""

    front: str
    back: str
    source: str = ""
    topic: str = ""
