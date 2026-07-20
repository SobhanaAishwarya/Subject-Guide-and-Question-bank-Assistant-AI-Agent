"""
Streamlit session-state helpers.

Centralises every ``st.session_state`` key so pages never have to guess whether
a key exists, and wires up the shared singletons (vector store, RAG engine,
agents, database).
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List

import streamlit as st

from config import settings
from database.db import Database, get_db
from models.schemas import Message
from services.agents import AgentService
from services.openrouter_client import OpenRouterClient
from services.rag_engine import RAGEngine
from services.vectorstore import VectorStore
from utils.logger import get_logger

logger = get_logger(__name__)

_DEFAULTS: Dict[str, Any] = {
    "authenticated": False,
    "page": "dashboard",
    "user": {
        "id": None,
        "name": "Student",
        "email": "",
        "avatar": "ST",
        "semester": "Semester 5",
    },
    "session_id": "",
    "messages": [],          # List[Message] — in-memory conversation
    "model": settings.openrouter_model,
    "source_filter": [],     # selected document filenames, [] = all
    "quiz": None,
    "quiz_answers": {},
    "quiz_submitted": False,
    "flash_index": 0,
    "flash_flipped": False,
    "interview": {"topic": "", "asked": [], "turns": []},
    "store_loaded": False,
    "top_k": settings.top_k,
    "min_similarity": settings.min_similarity,
}


def init_session() -> None:
    """Ensure every expected key exists in ``st.session_state``."""
    for key, value in _DEFAULTS.items():
        if key not in st.session_state:
            # Copy mutables so sessions never share the same object.
            st.session_state[key] = (
                value.copy() if isinstance(value, (dict, list)) else value
            )
    if not st.session_state.session_id:
        st.session_state.session_id = uuid.uuid4().hex[:12]


# --------------------------------------------------------------------------- #
# Cached singletons
# --------------------------------------------------------------------------- #
@st.cache_resource(show_spinner=False)
def get_vector_store() -> VectorStore:
    """Shared FAISS store, restored from disk on first access."""
    store = VectorStore()
    store.load()
    return store


@st.cache_resource(show_spinner=False)
def get_database() -> Database:
    """Shared SQLite handle."""
    return get_db()


def get_llm() -> OpenRouterClient:
    """LLM client honouring the model selected in the sidebar."""
    return OpenRouterClient(model=st.session_state.get("model"))


def get_rag() -> RAGEngine:
    """RAG engine bound to the current store, model and retrieval settings."""
    return RAGEngine(
        get_vector_store(),
        llm=get_llm(),
        top_k=st.session_state.get("top_k", settings.top_k),
        min_similarity=st.session_state.get("min_similarity", settings.min_similarity),
    )


def get_agents() -> AgentService:
    """Agent service bound to the current RAG engine."""
    return AgentService(get_rag())


# --------------------------------------------------------------------------- #
# Convenience accessors
# --------------------------------------------------------------------------- #
def navigate(page: str) -> None:
    """Switch the active page and rerun."""
    st.session_state.page = page
    st.rerun()


def active_sources() -> List[str] | None:
    """The document filter to apply, or ``None`` when searching everything."""
    selected = st.session_state.get("source_filter") or []
    return selected or None


def add_message(message: Message, persist: bool = True) -> None:
    """Append a chat turn to session memory and (optionally) to SQLite."""
    st.session_state.messages.append(message)
    if persist:
        try:
            get_database().add_message(
                st.session_state.session_id,
                message.role,
                message.content,
                message.sources,
            )
        except Exception as exc:  # noqa: BLE001 - history is non-critical
            logger.warning("Could not persist message: %s", exc)


def reset_chat() -> None:
    """Start a fresh conversation."""
    st.session_state.messages = []
    st.session_state.session_id = uuid.uuid4().hex[:12]


def log_in(user: Dict[str, Any]) -> None:
    """Persist a signed-in user and drop the caller at the dashboard."""
    st.session_state.user = user
    st.session_state.authenticated = True
    st.session_state.page = "dashboard"
    st.rerun()


def sign_out() -> None:
    """Fully clear the session and return to the Sign In / Sign Up gate."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
