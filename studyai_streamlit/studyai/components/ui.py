"""Reusable Streamlit UI components rendered with the custom butter-yellow CSS."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

import streamlit as st

from config import CSS_DIR
from models.schemas import RetrievedChunk
from utils.text_utils import truncate


# --------------------------------------------------------------------------- #
# Styling
# --------------------------------------------------------------------------- #
def load_css() -> None:
    """Inject the project stylesheet once per rerun."""
    css_path = Path(CSS_DIR) / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>",
                    unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Layout blocks
# --------------------------------------------------------------------------- #
def hero(title: str, subtitle: str, eyebrow: str = "STUDYAI") -> None:
    """Render the page hero banner."""
    st.markdown(
        f"""
        <div class="hero">
          <div class="eyebrow">{html.escape(eyebrow)}</div>
          <h1>{html.escape(title)}</h1>
          <p>{html.escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(value: str, label: str, note: str = "") -> None:
    """Render a single stat card: bold value, label, optional note."""
    st.markdown(
        f"""
        <div class="metric">
          <div class="value">{html.escape(str(value))}</div>
          <div class="label">{html.escape(label)}</div>
          {f'<div class="note">{html.escape(note)}</div>' if note else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_row(cards: Sequence[dict]) -> None:
    """Render a responsive row of metric cards."""
    columns = st.columns(len(cards))
    for column, card in zip(columns, cards):
        with column:
            metric_card(
                card.get("value", "—"),
                card.get("label", ""),
                card.get("note", ""),
            )


def progress_row(name: str, value: int, suffix: str = "%", tone: str = "") -> None:
    """Render a labelled progress bar."""
    width = max(0, min(int(value), 100))
    st.markdown(
        f"""
        <div style="margin-bottom:14px;">
          <div class="row-label">
            <span class="name">{html.escape(name)}</span>
            <span class="val">{width}{suffix}</span>
          </div>
          <div class="bar-track"><div class="bar-fill {tone}" style="width:{width}%"></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def tone_for_score(score: int) -> str:
    """Pick a progress-bar colour class from a mastery score."""
    if score < 50:
        return "danger"
    if score < 70:
        return "warn"
    return "good"


def card_open(title: str = "") -> None:
    """Open a glass card container (pair with :func:`card_close`)."""
    heading = f"<h3>{html.escape(title)}</h3>" if title else ""
    st.markdown(f'<div class="card">{heading}', unsafe_allow_html=True)


def card_close() -> None:
    """Close a card opened by :func:`card_open`."""
    st.markdown("</div>", unsafe_allow_html=True)


def empty_state(title: str, subtitle: str) -> None:
    """Render a friendly placeholder when there is nothing to show."""
    st.markdown(
        f"""
        <div class="empty-state">
          <div class="title">{html.escape(title)}</div>
          <div class="sub">{html.escape(subtitle)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def pill(text: str, tone: str = "") -> str:
    """Return the HTML for an inline status pill."""
    return f'<span class="pill {tone}">{html.escape(text)}</span>'


# --------------------------------------------------------------------------- #
# Sources / citations
# --------------------------------------------------------------------------- #
def render_sources(sources: Sequence[RetrievedChunk], expanded: bool = False) -> None:
    """Render the citation panel for a grounded answer."""
    if not sources:
        return

    with st.expander(f"Sources ({len(sources)})", expanded=expanded):
        for position, item in enumerate(sources, start=1):
            chunk = item.chunk
            st.markdown(
                f"""
                <div class="source-card">
                  <div class="src-head">
                    <span>[{position}] {html.escape(chunk.citation)}</span>
                    <span>relevance {item.score:.0%}</span>
                  </div>
                  <div class="src-body">{html.escape(truncate(chunk.text, 420))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_source_dicts(sources: Iterable[dict]) -> None:
    """Render citations that were restored from persisted chat history."""
    items = list(sources)
    if not items:
        return
    with st.expander(f"Sources ({len(items)})"):
        for position, item in enumerate(items, start=1):
            chunk = item.get("chunk", item)
            citation = chunk.get("source", "document")
            if chunk.get("page"):
                citation += f", p. {chunk['page']}"
            st.markdown(
                f"""
                <div class="source-card">
                  <div class="src-head"><span>[{position}] {html.escape(citation)}</span></div>
                  <div class="src-body">{html.escape(truncate(chunk.get('text', ''), 420))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# --------------------------------------------------------------------------- #
# Guards
# --------------------------------------------------------------------------- #
def require_documents(store) -> bool:
    """
    Block a page when nothing is indexed.

    Returns True when documents exist, otherwise renders a prompt and False.
    """
    if not store.is_empty:
        return True
    empty_state(
        "No documents indexed yet",
        "Head to the Upload Center and add a PDF, DOCX, PPTX or TXT file first.",
    )
    if st.button("Go to Upload Center", type="primary"):
        st.session_state.page = "upload"
        st.rerun()
    return False


def source_selector(store, key: str = "source_filter") -> Optional[List[str]]:
    """Render the multiselect that restricts retrieval to chosen documents."""
    available = store.sources
    if not available:
        return None
    # Only `key` is passed — supplying `default` as well makes Streamlit warn
    # about a widget whose value is also set through the Session State API.
    # Stale entries are pruned so deleting a document cannot break the filter.
    st.session_state[key] = [s for s in st.session_state.get(key, []) if s in available]
    selected = st.multiselect(
        "Search within",
        options=available,
        key=key,
        help="Leave empty to search across every uploaded document.",
    )
    return selected or None
