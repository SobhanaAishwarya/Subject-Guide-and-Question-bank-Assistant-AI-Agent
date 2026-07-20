"""
Revision Agent — port of ``src/components/agents/RevisionPage.tsx``.

Produces dense, scannable revision sheets from the indexed material.
"""

from __future__ import annotations

import streamlit as st

from components.ui import hero, render_sources, require_documents, source_selector
from utils.session import active_sources, get_agents, get_database, get_vector_store


def render() -> None:
    """Render the Revision Agent page."""
    store = get_vector_store()
    agents = get_agents()

    hero(
        "Revision Agent",
        "Last-mile revision sheets: definitions, formulas, mnemonics and the "
        "mistakes people usually make.",
        eyebrow="REVISION",
    )

    if not require_documents(store):
        return

    source_selector(store)

    # Quick picks drawn from the documents actually indexed.
    # These must be rendered BEFORE the text input: Streamlit forbids writing to
    # session_state for a key whose widget has already been instantiated.
    st.caption("Jump straight into one of your documents:")
    quick_columns = st.columns(min(4, max(1, len(store.sources))))
    for column, source_name in zip(quick_columns, store.sources[:4]):
        with column:
            if st.button(source_name[:22], key=f"rev_quick_{source_name}",
                         use_container_width=True):
                st.session_state.rev_topic = source_name
                st.rerun()

    topic = st.text_input("Topic to revise", key="rev_topic",
                          placeholder="e.g. Deadlock, Indexing, OSI Model")

    if st.button("Generate Revision Sheet", type="primary",
                 use_container_width=True) and topic:
        with st.spinner("Condensing your material…"):
            try:
                sheet, sources = agents.generate_revision(topic, active_sources())
            except Exception as exc:  # noqa: BLE001
                st.error(f"Generation failed: {exc}")
                return

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(sheet)
        st.markdown("</div>", unsafe_allow_html=True)

        render_sources(sources)
        get_database().log_activity(f"Revised {topic}", icon="RV",
                                    kind="revision", minutes=10)
        st.download_button(
            "Download sheet",
            data=sheet,
            file_name=f"revision_{topic.replace(' ', '_').lower()}.md",
            mime="text/markdown",
        )
