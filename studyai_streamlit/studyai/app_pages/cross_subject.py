"""
Cross Subject — port of ``src/components/agents/CrossSubjectPage.tsx``.

Reasons across every indexed document at once to surface connections, contrasts
and unified explanations.
"""

from __future__ import annotations

import streamlit as st

from components.ui import (
    empty_state,
    hero,
    render_sources,
    require_documents,
    source_selector,
)
from utils.session import active_sources, get_agents, get_database, get_vector_store


EXAMPLE_QUERIES = [
    "How do concepts in these documents connect?",
    "Where do these documents disagree or use different terminology?",
    "Which topics appear across more than one document?",
]


def render() -> None:
    """Render the Cross Subject page."""
    store = get_vector_store()
    agents = get_agents()

    hero(
        "Cross Subject",
        "Multi-document reasoning: find the threads that run across everything "
        "you've uploaded.",
        eyebrow="🔗 SYNTHESIS",
    )

    if not require_documents(store):
        return

    if len(store.sources) < 2:
        st.info("💡 This agent shines with two or more documents. "
                "Upload another one for richer connections.")

    st.caption(f"📚 Indexed documents: {', '.join(store.sources)}")
    source_selector(store)

    # Rendered before the text area on purpose: session_state for a widget key
    # cannot be written after that widget has been instantiated.
    st.caption("Try one of these:")
    example_columns = st.columns(len(EXAMPLE_QUERIES))
    for position, (column, example) in enumerate(zip(example_columns, EXAMPLE_QUERIES)):
        with column:
            if st.button(example[:34] + "…", key=f"cross_ex_{position}",
                         use_container_width=True):
                st.session_state.cross_query = example
                st.rerun()

    query = st.text_area(
        "What should I look for across your documents?",
        key="cross_query",
        height=90,
        placeholder="e.g. How does memory management relate to database buffering?",
    )

    if st.button("🔗  Analyse Across Documents", type="primary",
                 use_container_width=True) and query.strip():
        with st.spinner("🤖 Reading across every document…"):
            try:
                analysis, sources = agents.cross_subject_analysis(
                    query, active_sources()
                )
            except Exception as exc:  # noqa: BLE001
                st.error(f"Analysis failed: {exc}")
                return

        if not sources:
            empty_state("🤔", "Nothing relevant found",
                        "Your documents don't seem to cover that.")
            return

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(analysis)
        st.markdown("</div>", unsafe_allow_html=True)

        render_sources(sources)
        get_database().log_activity("Cross-subject analysis", icon="🔗",
                                    kind="analysis", minutes=6)
        st.download_button(
            "⬇️  Download analysis",
            data=analysis,
            file_name="cross_subject_analysis.md",
            mime="text/markdown",
        )
