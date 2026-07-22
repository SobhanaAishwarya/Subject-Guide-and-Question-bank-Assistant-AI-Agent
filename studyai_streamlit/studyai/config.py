"""
Central configuration for the StudyAI Streamlit application.

All tunable constants, paths and credentials live here so that no other
module needs to know about environment variables or the filesystem layout.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, List

from dotenv import load_dotenv

# Load .env once, at import time.
load_dotenv()

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
BASE_DIR: Final[Path] = Path(__file__).resolve().parent

ASSETS_DIR: Final[Path] = BASE_DIR / "assets"
CSS_DIR: Final[Path] = ASSETS_DIR / "css"
UPLOADS_DIR: Final[Path] = BASE_DIR / "uploads"
VECTORSTORE_DIR: Final[Path] = BASE_DIR / "vectorstore"
CHAT_HISTORY_DIR: Final[Path] = BASE_DIR / "chat_history"
DATABASE_PATH: Final[Path] = BASE_DIR / "database" / "studyai.db"

for _directory in (UPLOADS_DIR, VECTORSTORE_DIR, CHAT_HISTORY_DIR, CSS_DIR):
    _directory.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# Credentials helper
# --------------------------------------------------------------------------- #
def _read_secret(key: str, default: str = "") -> str:
    """
    Resolve a secret from Streamlit Cloud secrets first, then the environment.

    Streamlit's ``st.secrets`` raises if no secrets file exists, so the lookup
    is wrapped defensively to keep local development friction-free.
    """
    try:
        import streamlit as st  # imported lazily: config is also used by scripts

        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:  # noqa: BLE001 - any secrets failure falls through to env
        pass
    return os.getenv(key, default)


# --------------------------------------------------------------------------- #
# Application settings
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Settings:
    """Immutable application settings."""

    # --- OpenRouter (the ONLY LLM provider used by this project) ---
    openrouter_api_key: str = field(default_factory=lambda: _read_secret("OPENROUTER_API_KEY"))
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = field(
        default_factory=lambda: _read_secret("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    )
    openrouter_referer: str = field(
        default_factory=lambda: _read_secret("OPENROUTER_SITE_URL", "https://streamlit.io")
    )
    openrouter_title: str = "StudyAI"
    request_timeout: int = 120
    max_retries: int = 3

    # --- Embeddings / RAG ---
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    chunk_size: int = 900
    chunk_overlap: int = 150
    top_k: int = 5
    # Cosine similarity floor. Chunks below this are treated as irrelevant,
    # which is what powers the "not in your documents" guardrail.
    min_similarity: float = 0.25

    # --- Generation ---
    temperature: float = 0.2
    max_tokens: int = 2000

    # --- Uploads ---
    max_upload_mb: int = 50
    supported_extensions: tuple[str, ...] = ("pdf", "docx", "pptx", "txt")

    # --- Persistence (Turso) ---
    # Streamlit Cloud rebuilds the app in a fresh container on every deploy,
    # which wipes any local SQLite file. Turso is a hosted, libSQL-compatible
    # SQLite database, so accounts and study data survive redeploys. When
    # these aren't set, the app falls back to a local SQLite file (fine for
    # local development, but not for a Cloud deployment that needs persistence).
    turso_database_url: str = field(default_factory=lambda: _read_secret("TURSO_DATABASE_URL"))
    turso_auth_token: str = field(default_factory=lambda: _read_secret("TURSO_AUTH_TOKEN"))

    @property
    def is_configured(self) -> bool:
        """True when an OpenRouter key is available."""
        return bool(self.openrouter_api_key and self.openrouter_api_key.startswith("sk-"))

    @property
    def uses_turso(self) -> bool:
        """True when Turso credentials are available for persistent storage."""
        return bool(self.turso_database_url and self.turso_auth_token)


settings = Settings()


# --------------------------------------------------------------------------- #
# Model catalogue offered in the UI (all served through OpenRouter)
# --------------------------------------------------------------------------- #
AVAILABLE_MODELS: Final[List[str]] = [
    "openai/gpt-4o-mini",
    "openai/gpt-4o",
    "anthropic/claude-3.5-sonnet",
    "google/gemini-flash-1.5",
    "meta-llama/llama-3.1-70b-instruct",
    "mistralai/mistral-large",
    "deepseek/deepseek-chat",
    "qwen/qwen-2.5-72b-instruct",
]

# --------------------------------------------------------------------------- #
# Subjects (ported from the original Next.js UploadCenter component)
# --------------------------------------------------------------------------- #
SUBJECTS: Final[List[str]] = [
    "Operating Systems",
    "Database Management",
    "Computer Networks",
    "Artificial Intelligence",
    "Java Programming",
    "Python",
]

# --------------------------------------------------------------------------- #
# Navigation (1:1 port of src/components/layout/Sidebar.tsx)
# --------------------------------------------------------------------------- #
NAV_ITEMS: Final[List[dict]] = [
    {"id": "dashboard", "label": "Dashboard"},
    {"id": "upload", "label": "Upload Center"},
    {"id": "chat", "label": "Chat with Docs"},
    {"id": "notes", "label": "Notes Agent"},
    {"id": "quiz", "label": "Quiz Agent"},
    {"id": "flashcards", "label": "Flashcard Agent"},
    {"id": "planner", "label": "Planner Agent"},
    {"id": "revision", "label": "Revision Agent"},
    {"id": "weak-topics", "label": "Weak Topics"},
    {"id": "interview", "label": "Interview Mode"},
    {"id": "cross-subject", "label": "Cross Subject"},
    {"id": "analytics", "label": "Analytics"},
    {"id": "profile", "label": "Profile"},
]

# The exact refusal string required by the project specification.
NO_ANSWER_MESSAGE: Final[str] = (
    "I couldn't find this information in the uploaded documents."
)
