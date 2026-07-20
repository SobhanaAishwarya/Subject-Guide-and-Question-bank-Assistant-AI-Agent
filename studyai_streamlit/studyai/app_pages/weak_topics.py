"""
Weak Topics — port of ``src/components/agents/WeakTopicsPage.tsx``.

The original showed four hardcoded topics with fixed scores. This version
derives weak areas from real quiz history plus an LLM analysis of the material.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from components.ui import (
    empty_state,
    hero,
    progress_row,
    render_sources,
    require_documents,
    source_selector,
    tone_for_score,
)
from config import SUBJECTS
from utils.session import active_sources, get_agents, get_database, get_vector_store


def render() -> None:
    """Render the Weak Topics page."""
    store = get_vector_store()
    agents = get_agents()
    db = get_database()

    hero(
        "Weak Topics",
        "Where you're losing marks, and exactly what to do about it — inferred "
        "from your quiz history and your own notes.",
        eyebrow="DIAGNOSTICS",
    )

    if not require_documents(store):
        return

    # ---- Measured weakness from quiz history -------------------------- #
    attempts = db.list_quiz_attempts()
    if attempts:
        st.markdown('<div class="card"><h3>Measured from your quizzes</h3>',
                    unsafe_allow_html=True)
        by_topic: dict[str, list[int]] = {}
        for attempt in attempts:
            percentage = int(round(attempt["score"] / max(attempt["total"], 1) * 100))
            by_topic.setdefault(attempt["topic"], []).append(percentage)

        rows = sorted(
            ((topic, sum(scores) // len(scores)) for topic, scores in by_topic.items()),
            key=lambda kv: kv[1],
        )
        for topic, average in rows:
            progress_row(topic, average, tone=tone_for_score(average))
        st.markdown("</div>", unsafe_allow_html=True)

        if len(rows) > 1:
            frame = pd.DataFrame(rows, columns=["Topic", "Average %"])
            figure = px.bar(
                frame, x="Average %", y="Topic", orientation="h",
                color="Average %", color_continuous_scale=["#CC0C39", "#FF9F00", "#388E3C"],
                range_color=[0, 100],
            )
            figure.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                height=max(240, 42 * len(rows)), margin=dict(l=8, r=8, t=24, b=8),
                coloraxis_showscale=False,
            )
            st.plotly_chart(figure, use_container_width=True)
    else:
        empty_state("No quiz history yet",
                    "Take a quiz and your measured weak spots will appear here.")

    st.divider()

    # ---- AI analysis -------------------------------------------------- #
    st.markdown("### AI analysis of your material")
    source_selector(store)
    subject = st.selectbox("Subject", SUBJECTS + ["Other"], key="weak_subject")
    if subject == "Other":
        subject = st.text_input("Custom subject", key="weak_custom") or "General"

    if st.button("Analyse Weak Topics", type="primary", use_container_width=True):
        with st.spinner("Cross-referencing your misses against your notes…"):
            try:
                topics, sources = agents.analyse_weak_topics(
                    subject, db.wrong_answers(), active_sources()
                )
            except Exception as exc:  # noqa: BLE001
                st.error(f"Analysis failed: {exc}")
                return

        if not topics:
            empty_state("Nothing conclusive",
                        "Not enough material on that subject to analyse.")
            return

        for topic in topics:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            progress_row(topic["name"], topic["score"],
                         tone=tone_for_score(topic["score"]))
            if topic.get("reason"):
                st.markdown(f"**Why it's hard:** {topic['reason']}")
            if topic.get("action"):
                st.info(f"**Next step:** {topic['action']}")
            st.markdown("</div>", unsafe_allow_html=True)

        render_sources(sources)
        db.log_activity(f"Analysed weak topics in {subject}", icon="WT",
                        kind="analysis", minutes=4)
