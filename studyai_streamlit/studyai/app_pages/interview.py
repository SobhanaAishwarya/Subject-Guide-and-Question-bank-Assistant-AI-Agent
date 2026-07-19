"""
Interview Mode — port of ``src/components/agents/InterviewPage.tsx``.

An AI interviewer asks questions drawn from the uploaded material, then grades
the student's answers against that same material.
"""

from __future__ import annotations

import streamlit as st

from components.ui import hero, render_sources, require_documents, source_selector
from utils.session import active_sources, get_agents, get_database, get_vector_store


def render() -> None:
    """Render Interview Mode."""
    store = get_vector_store()
    agents = get_agents()
    db = get_database()

    hero(
        "Interview Mode",
        "A mock technical interview built from your notes. Answer out loud, type "
        "it in, and get graded against the source.",
        eyebrow="🎤 INTERVIEW",
    )

    if not require_documents(store):
        return

    state = st.session_state.interview

    # ---- Setup --------------------------------------------------------- #
    if not state["topic"]:
        source_selector(store)
        topic = st.text_input("Interview topic", key="int_topic",
                              placeholder="e.g. Operating Systems, DBMS, Networks")
        if st.button("🎤  Start Interview", type="primary",
                     use_container_width=True) and topic:
            state["topic"] = topic
            state["asked"] = []
            state["turns"] = []
            st.rerun()
        return

    # ---- Header -------------------------------------------------------- #
    header_left, header_right = st.columns([4, 1])
    with header_left:
        st.markdown(f"### 🎤 Interview: {state['topic']}  ·  "
                    f"Question {len(state['asked']) + 1}")
    with header_right:
        if st.button("🔚  End", use_container_width=True):
            st.session_state.interview = {"topic": "", "asked": [], "turns": []}
            st.rerun()

    # ---- Transcript ----------------------------------------------------- #
    for turn in state["turns"]:
        with st.chat_message("assistant", avatar="👔"):
            st.markdown(f"**{turn['question']}**")
        with st.chat_message("user", avatar="🧑‍🎓"):
            st.markdown(turn["answer"])
        with st.chat_message("assistant", avatar="📝"):
            st.markdown(turn["feedback"])

    # ---- Current question ------------------------------------------------ #
    if "current" not in state or not state.get("current"):
        with st.spinner("🤖 Thinking of a question…"):
            try:
                question, _ = agents.interview_question(
                    state["topic"], state["asked"], active_sources()
                )
            except Exception as exc:  # noqa: BLE001
                st.error(f"Could not generate a question: {exc}")
                return
        state["current"] = question
        st.rerun()

    with st.chat_message("assistant", avatar="👔"):
        st.markdown(f"**{state['current']}**")

    answer = st.text_area("Your answer", key=f"int_answer_{len(state['asked'])}",
                          height=140)

    submit_column, skip_column = st.columns([3, 1])
    with submit_column:
        if st.button("✅  Submit Answer", type="primary",
                     use_container_width=True) and answer.strip():
            with st.spinner("🤖 Evaluating against your notes…"):
                try:
                    feedback, sources = agents.evaluate_answer(
                        state["current"], answer, active_sources()
                    )
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Evaluation failed: {exc}")
                    return

            state["turns"].append({
                "question": state["current"],
                "answer": answer,
                "feedback": feedback,
            })
            state["asked"].append(state["current"])
            state["current"] = ""
            db.log_activity(f"Interview practice: {state['topic']}",
                            icon="🎤", kind="interview", minutes=5)
            render_sources(sources)
            st.rerun()

    with skip_column:
        if st.button("⏭️  Skip", use_container_width=True):
            state["asked"].append(state["current"])
            state["current"] = ""
            st.rerun()
