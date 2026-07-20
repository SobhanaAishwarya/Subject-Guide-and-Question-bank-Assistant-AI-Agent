"""
Quiz Agent — port of ``src/components/agents/QuizPage.tsx``.

Generates MCQs from the indexed documents, grades them, records the attempt in
SQLite and feeds wrong answers to the Weak Topics agent.
"""

from __future__ import annotations

import streamlit as st

from components.ui import (
    empty_state,
    hero,
    render_sources,
    require_documents,
    source_selector,
    tone_for_score,
)
from utils.session import active_sources, get_agents, get_database, get_vector_store


def _reset_quiz() -> None:
    """Clear the quiz and the per-question radio widgets it created."""
    for key in [k for k in st.session_state if k.startswith("q_")]:
        del st.session_state[key]
    st.session_state.quiz = None
    st.session_state.quiz_answers = {}
    st.session_state.quiz_submitted = False


def render() -> None:
    """Render the Quiz Agent page."""
    store = get_vector_store()
    agents = get_agents()
    db = get_database()

    hero(
        "Quiz Agent",
        "Adaptive multiple-choice questions generated from your own notes — "
        "every option traceable to a source.",
        eyebrow="QUIZ",
    )

    if not require_documents(store):
        return

    # ---- Setup --------------------------------------------------------- #
    if st.session_state.quiz is None:
        source_selector(store)

        setup_left, setup_middle, setup_right = st.columns([2, 1, 1])
        with setup_left:
            topic = st.text_input("Topic", key="quiz_topic",
                                  placeholder="e.g. Normalization")
        with setup_middle:
            count = st.number_input("Questions", 3, 20, 5, key="quiz_count")
        with setup_right:
            difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"],
                                      index=1, key="quiz_difficulty")

        if st.button("Generate Quiz", type="primary", use_container_width=True):
            if not topic:
                st.warning("Enter a topic first.")
                return
            with st.spinner("Writing questions from your documents…"):
                try:
                    questions, sources = agents.generate_quiz(
                        topic, int(count), difficulty, active_sources()
                    )
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Quiz generation failed: {exc}")
                    return

            if not questions:
                empty_state(
                    "QZ",
                    "Couldn't build a quiz on that topic",
                    "The uploaded documents don't seem to cover it. Try another topic.",
                )
                return

            st.session_state.quiz = {
                "topic": topic,
                "difficulty": difficulty,
                "questions": [q.__dict__ for q in questions],
                "sources": [s.to_dict() for s in sources],
            }
            for key in [k for k in st.session_state if k.startswith("q_")]:
                del st.session_state[key]
            st.session_state.quiz_answers = {}
            st.session_state.quiz_submitted = False
            st.rerun()
        return

    # ---- Active quiz ---------------------------------------------------- #
    quiz = st.session_state.quiz
    questions = quiz["questions"]

    header_left, header_right = st.columns([4, 1])
    with header_left:
        st.markdown(f"### {quiz['topic']} · {quiz['difficulty']} · "
                    f"{len(questions)} questions")
    with header_right:
        if st.button("New quiz", use_container_width=True):
            _reset_quiz()
            st.rerun()

    if not st.session_state.quiz_submitted:
        answered = len(st.session_state.quiz_answers)
        st.progress(answered / len(questions),
                    text=f"{answered} of {len(questions)} answered")

    # ---- Questions ------------------------------------------------------ #
    for index, question in enumerate(questions):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"**Q{index + 1}. {question['question']}**")

        submitted = st.session_state.quiz_submitted
        choice = st.radio(
            "Select an answer",
            options=list(range(len(question["options"]))),
            format_func=lambda i, q=question: q["options"][i],
            key=f"q_{index}",
            index=None,
            disabled=submitted,
            label_visibility="collapsed",
        )
        if choice is not None and not submitted:
            st.session_state.quiz_answers[index] = choice

        if submitted:
            given = st.session_state.quiz_answers.get(index)
            correct = question["answer_index"]
            if given == correct:
                st.success(f"Correct — {question['options'][correct]}")
            else:
                given_text = (question["options"][given]
                              if given is not None else "no answer")
                st.error(f"You chose: {given_text}  \n"
                         f"Correct: {question['options'][correct]}")
            if question.get("explanation"):
                st.info(question["explanation"])
            if question.get("source"):
                st.caption(f"Source: {question['source']}")

        st.markdown("</div>", unsafe_allow_html=True)

    # ---- Submit / results ------------------------------------------------ #
    if not st.session_state.quiz_submitted:
        if st.button("Submit Answers", type="primary", use_container_width=True):
            if len(st.session_state.quiz_answers) < len(questions):
                st.warning("Answer every question before submitting.")
            else:
                st.session_state.quiz_submitted = True

                score = sum(
                    1 for i, q in enumerate(questions)
                    if st.session_state.quiz_answers.get(i) == q["answer_index"]
                )
                wrong = [
                    q["question"] for i, q in enumerate(questions)
                    if st.session_state.quiz_answers.get(i) != q["answer_index"]
                ]
                db.add_quiz_attempt(quiz["topic"], quiz["topic"], score,
                                    len(questions), wrong)
                db.log_activity(
                    f"Quiz: {quiz['topic']} — {score}/{len(questions)}",
                    icon="QZ", kind="quiz", minutes=len(questions) * 2,
                )
                st.rerun()
    else:
        score = sum(
            1 for i, q in enumerate(questions)
            if st.session_state.quiz_answers.get(i) == q["answer_index"]
        )
        percentage = int(round(score / len(questions) * 100))
        tone = tone_for_score(percentage)

        result_label = (
            "TOP SCORE" if percentage >= 80 else
            "GOOD EFFORT" if percentage >= 50 else
            "KEEP PRACTISING"
        )
        st.markdown(
            f"""
            <div class="card" style="text-align:center;">
              <div class="pill{' green' if percentage >= 80 else ''}" style="font-size:12px;">
                {result_label}
              </div>
              <div style="font-size:33px;font-weight:800;margin-top:8px;">{score}/{len(questions)}</div>
              <div style="font-size:15px;color:var(--ink-soft);">{percentage}% correct</div>
              <div class="bar-track" style="margin-top:14px;">
                <div class="bar-fill {tone}" style="width:{percentage}%"></div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if percentage < 70:
            st.info("Below 70% — the Weak Topics agent can turn these misses "
                    "into a focused revision plan.")
            if st.button("Analyse my weak topics"):
                st.session_state.page = "weak-topics"
                st.rerun()

        st.caption("Sources used to build this quiz:")
        with st.expander(f"Sources ({len(quiz['sources'])})"):
            for position, item in enumerate(quiz["sources"], start=1):
                chunk = item["chunk"]
                citation = chunk["source"] + (
                    f", p. {chunk['page']}" if chunk.get("page") else ""
                )
                st.markdown(f"**[{position}]** {citation}")
