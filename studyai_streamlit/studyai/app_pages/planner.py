"""
Planner Agent — port of ``src/components/agents/PlannerPage.tsx``.

Builds a day-by-day study schedule from the topics that actually appear in the
uploaded documents.
"""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from components.ui import hero, render_sources, require_documents, source_selector
from config import SUBJECTS
from utils.session import active_sources, get_agents, get_database, get_vector_store


def render() -> None:
    """Render the Planner Agent page."""
    store = get_vector_store()
    agents = get_agents()

    hero(
        "Planner Agent",
        "A realistic study schedule built around your exam date and the topics "
        "in your own documents.",
        eyebrow="PLANNER",
    )

    if not require_documents(store):
        return

    source_selector(store)

    subject_column, days_column, hours_column = st.columns([2, 1, 1])
    with subject_column:
        subject = st.selectbox("Subject", SUBJECTS + ["Other"], key="plan_subject")
        if subject == "Other":
            subject = st.text_input("Custom subject", key="plan_custom") or "General"
    with days_column:
        days = st.number_input("Days available", 1, 90, 14, key="plan_days")
    with hours_column:
        hours = st.number_input("Hours/day", 0.5, 14.0, 3.0, step=0.5, key="plan_hours")

    exam_date = st.date_input(
        "Exam date",
        value=date.today() + timedelta(days=int(days)),
        key="plan_exam",
    )

    if st.button("Build My Study Plan", type="primary", use_container_width=True):
        with st.spinner("Mapping your syllabus onto a calendar…"):
            try:
                plan, sources = agents.generate_study_plan(
                    subject, int(days), float(hours),
                    exam_date.isoformat(), active_sources(),
                )
            except Exception as exc:  # noqa: BLE001
                st.error(f"Planning failed: {exc}")
                return

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(plan)
        st.markdown("</div>", unsafe_allow_html=True)

        render_sources(sources)
        get_database().log_activity(f"Built a {days}-day plan for {subject}",
                                    icon="PL", kind="planner", minutes=5)
        st.download_button(
            "Download plan",
            data=plan,
            file_name=f"study_plan_{subject.replace(' ', '_').lower()}.md",
            mime="text/markdown",
        )
