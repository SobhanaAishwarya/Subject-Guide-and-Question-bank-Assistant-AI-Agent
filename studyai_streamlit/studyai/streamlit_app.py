"""
StudyAI — Agentic Study Assistant
=================================

Streamlit entry point. Run with::

    streamlit run app.py

This is the Python port of the original Next.js/TypeScript project. Every page
of the React app is reimplemented here as a Streamlit view, and the mock data
has been replaced with a working RAG pipeline:

    upload → extract → clean → chunk → embed (all-MiniLM-L6-v2)
           → FAISS → semantic search → retrieved context → OpenRouter → answer

The only outbound LLM provider is OpenRouter (https://openrouter.ai/api/v1).
"""

from __future__ import annotations

import streamlit as st

# --------------------------------------------------------------------------- #
# Page config MUST be the first Streamlit call.
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="StudyAI — Agentic Study Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "StudyAI — RAG-powered study assistant built on Streamlit "
                         "and OpenRouter."},
)

from app_pages import (  # noqa: E402 - must come after set_page_config
    analytics,
    chat,
    cross_subject,
    dashboard,
    flashcards,
    interview,
    login,
    notes,
    planner,
    profile,
    quiz,
    revision,
    upload_center,
    weak_topics,
)
from components.sidebar import render_sidebar  # noqa: E402
from components.ui import load_css  # noqa: E402
from config import settings  # noqa: E402
from utils.logger import get_logger  # noqa: E402
from utils.session import init_session  # noqa: E402

logger = get_logger(__name__)

# Page id → render function. Mirrors ``Page`` in the original src/app/page.tsx.
ROUTES = {
    "dashboard": dashboard.render,
    "upload": upload_center.render,
    "chat": chat.render,
    "notes": notes.render,
    "quiz": quiz.render,
    "flashcards": flashcards.render,
    "planner": planner.render,
    "revision": revision.render,
    "weak-topics": weak_topics.render,
    "interview": interview.render,
    "cross-subject": cross_subject.render,
    "analytics": analytics.render,
    "profile": profile.render,
}


def main() -> None:
    """Boot the application and dispatch to the active page."""
    init_session()
    load_css()

    # Auth gate (mirrors the LoginPage gate in the original app).
    if not st.session_state.authenticated:
        login.render()
        return

    active_page = render_sidebar()

    if not settings.is_configured:
        st.warning(
            "**No OpenRouter API key configured.** Uploading and indexing will "
            "still work, but no answers can be generated. Add "
            "`OPENROUTER_API_KEY` to your `.env` file, or to **Settings → "
            "Secrets** in Streamlit Cloud."
        )

    render = ROUTES.get(active_page)
    if render is None:
        logger.warning("Unknown page '%s', falling back to dashboard", active_page)
        st.session_state.page = "dashboard"
        render = dashboard.render

    try:
        render()
    except Exception as exc:  # noqa: BLE001 - never show a raw traceback to a student
        logger.exception("Page '%s' crashed", active_page)
        st.error(f"Something went wrong on this page: {exc}")
        with st.expander("Technical details"):
            st.exception(exc)


if __name__ == "__main__":
    main()
