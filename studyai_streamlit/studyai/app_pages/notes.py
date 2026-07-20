"""
Notes Agent — port of ``src/components/agents/NotesPage.tsx``.

Bundles the document-derived writing features: notes, summarisation, chapter and
topic explanation, question bank, important questions and previous-paper analysis.
"""

from __future__ import annotations

import streamlit as st

from components.ui import hero, render_sources, require_documents, source_selector
from utils.session import active_sources, get_agents, get_database, get_vector_store


def _run(label: str, generator, icon: str, minutes: int = 5) -> None:
    """Execute an agent call, render the result and log the activity."""
    with st.spinner(f"{label}…"):
        try:
            text, sources = generator()
        except Exception as exc:  # noqa: BLE001
            st.error(f"Generation failed: {exc}")
            return

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(text)
    st.markdown("</div>", unsafe_allow_html=True)

    render_sources(sources)
    get_database().log_activity(label, icon=icon, kind="notes", minutes=minutes)

    st.download_button(
        "Download as Markdown",
        data=text,
        file_name=f"{label.replace(' ', '_').lower()}.md",
        mime="text/markdown",
    )


def render() -> None:
    """Render the Notes Agent page."""
    store = get_vector_store()
    agents = get_agents()

    hero(
        "Notes Agent",
        "Turn your uploaded material into structured notes, summaries, "
        "explanations and question banks — all cited.",
        eyebrow="NOTES",
    )

    if not require_documents(store):
        return

    source_selector(store)
    sources = active_sources()

    notes_tab, summary_tab, explain_tab, bank_tab, paper_tab = st.tabs(
        ["Notes", "Summary", "Explain", "Question Bank", "Previous Papers"]
    )

    # ---- Notes -------------------------------------------------------- #
    with notes_tab:
        topic = st.text_input("Topic or chapter", key="notes_topic",
                              placeholder="e.g. Normalization, Deadlock, TCP Congestion")
        style = st.selectbox(
            "Style", ["Detailed", "Concise", "Exam-focused", "Bullet points"],
            key="notes_style"
        )
        if st.button("Generate Notes", type="primary", key="btn_notes") and topic:
            _run(
                f"Notes on {topic}",
                lambda: agents.generate_notes(topic, style, sources),
                icon="NT",
            )

    # ---- Summary ------------------------------------------------------ #
    with summary_tab:
        subject = st.text_input("What should I summarise?", key="sum_topic",
                                placeholder="e.g. Chapter 4, or the whole document")
        length = st.radio("Length", ["Short", "Medium", "Long"], index=1,
                          horizontal=True, key="sum_length")
        if st.button("Summarise", type="primary", key="btn_sum") and subject:
            _run(
                f"Summary of {subject}",
                lambda: agents.summarise(subject, length, sources),
                icon="SM",
            )

    # ---- Explain ------------------------------------------------------ #
    with explain_tab:
        topic = st.text_input("Topic or chapter to explain", key="exp_topic")
        level = st.selectbox(
            "Explain at this level",
            ["Beginner", "Undergraduate", "Advanced", "Explain like I'm 5"],
            index=1,
            key="exp_level",
        )
        if st.button("Explain", type="primary", key="btn_exp") and topic:
            _run(
                f"Explanation of {topic}",
                lambda: agents.explain_topic(topic, level, sources),
                icon="EX",
            )

    # ---- Question bank ------------------------------------------------ #
    with bank_tab:
        topic = st.text_input("Topic for the question bank", key="bank_topic")
        mode = st.radio(
            "Mode", ["Full question bank", "Important questions only"],
            horizontal=True, key="bank_mode"
        )
        if st.button("Generate", type="primary", key="btn_bank") and topic:
            if mode == "Full question bank":
                _run(f"Question bank for {topic}",
                     lambda: agents.question_bank(topic, sources), icon="QB")
            else:
                _run(f"Important questions for {topic}",
                     lambda: agents.important_questions(topic, sources), icon="IQ")

    # ---- Previous papers ---------------------------------------------- #
    with paper_tab:
        subject = st.text_input("Subject", key="paper_subject",
                                placeholder="e.g. Operating Systems")
        pasted = st.text_area(
            "Paste a previous question paper (optional)",
            key="paper_text",
            height=150,
            help="Leave empty to analyse whatever papers you uploaded.",
        )
        if st.button("Analyse Papers", type="primary", key="btn_paper") and subject:
            _run(
                f"Previous paper analysis for {subject}",
                lambda: agents.analyse_previous_paper(subject, pasted, sources),
                icon="PP",
            )
