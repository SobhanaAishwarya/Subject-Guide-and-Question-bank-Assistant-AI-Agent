"""
Chat with Documents — the core RAG surface.

ChatGPT-style UI with streaming (typing animation), inline citations, related
follow-up questions, conversation history and session memory.
"""

from __future__ import annotations

import streamlit as st

from components.ui import (
    hero,
    render_source_dicts,
    render_sources,
    require_documents,
    source_selector,
)
from models.schemas import Message
from utils.logger import get_logger
from utils.session import (
    active_sources,
    add_message,
    get_database,
    get_rag,
    get_vector_store,
    reset_chat,
)

logger = get_logger(__name__)


def _ask(question: str) -> None:
    """Run one RAG turn and stream the answer."""
    rag = get_rag()
    db = get_database()

    add_message(Message(role="user", content=question))
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown('<span class="typing">Searching your documents…</span>',
                             unsafe_allow_html=True)

        try:
            generator, sources = rag.answer_stream(
                question,
                history=st.session_state.messages[:-1],
                sources=active_sources(),
            )
            placeholder.empty()
            answer_text = st.write_stream(generator)
        except Exception as exc:  # noqa: BLE001 - surface the failure to the user
            logger.exception("Chat turn failed")
            placeholder.empty()
            st.error(f"Something went wrong: {exc}")
            return

        render_sources(sources)

        related = []
        if sources:
            related = rag.related_questions(question, rag.build_context(sources))

    add_message(
        Message(
            role="assistant",
            content=answer_text,
            sources=[s.to_dict() for s in sources],
            related=related,
        )
    )
    db.log_activity(f"Asked: {question[:60]}", icon="CH", kind="chat", minutes=2)
    st.rerun()


def render() -> None:
    """Render the chat page."""
    store = get_vector_store()

    hero(
        "Chat with your Documents",
        "Ask anything. Answers come only from your uploaded material, with page "
        "citations — and an honest 'not found' when the material doesn't cover it.",
        eyebrow="RAG CHAT",
    )

    if not require_documents(store):
        return

    controls_left, controls_right = st.columns([3, 1])
    with controls_left:
        source_selector(store)
    with controls_right:
        st.write("")
        if st.button("New chat", use_container_width=True):
            reset_chat()
            st.rerun()

    # ---- Replay conversation history --------------------------------- #
    for message in st.session_state.messages:
        with st.chat_message(message.role):
            st.markdown(message.content)
            if message.role == "assistant":
                render_source_dicts(message.sources)

    # ---- Related-question shortcuts ---------------------------------- #
    if st.session_state.messages:
        last = st.session_state.messages[-1]
        if last.role == "assistant" and last.related:
            st.caption("Related questions")
            for position, suggestion in enumerate(last.related):
                if st.button(suggestion, key=f"rel_{len(st.session_state.messages)}_{position}"):
                    _ask(suggestion)

    # ---- Input -------------------------------------------------------- #
    question = st.chat_input("Ask a question about your documents…")
    if question:
        _ask(question)
