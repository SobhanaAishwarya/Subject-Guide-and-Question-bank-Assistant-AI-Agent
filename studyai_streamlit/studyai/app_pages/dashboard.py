"""
Dashboard — port of ``src/components/dashboard/Dashboard.tsx``.

The original rendered hardcoded arrays (mock streak, mock subjects, mock
activity). Every one of those is now driven by real data from SQLite and the
FAISS index.
"""

from __future__ import annotations

import html
from collections import Counter

import streamlit as st

from components.ui import (
    empty_state,
    hero,
    metric_row,
    progress_row,
    tone_for_score,
)
from utils.session import get_database, get_vector_store

# The eight agent tiles from the original dashboard grid.
AGENT_TILES = [
    {"id": "notes", "icon": "NT", "label": "Notes Agent", "desc": "Generate smart notes"},
    {"id": "quiz", "icon": "QZ", "label": "Quiz Agent", "desc": "MCQ & adaptive quizzes"},
    {"id": "flashcards", "icon": "FC", "label": "Flashcard Agent", "desc": "Spaced repetition"},
    {"id": "planner", "icon": "PL", "label": "Planner Agent", "desc": "AI study schedule"},
    {"id": "revision", "icon": "RV", "label": "Revision Agent", "desc": "Rapid revision sheets"},
    {"id": "weak-topics", "icon": "WT", "label": "Weak Topics", "desc": "Track weak areas"},
    {"id": "interview", "icon": "IV", "label": "Interview Mode", "desc": "AI mock interviews"},
    {"id": "cross-subject", "icon": "CS", "label": "Cross Subject", "desc": "Multi-doc reasoning"},
]

ACHIEVEMENTS = [
    {"icon": "07", "label": "7 Day Streak", "test": lambda s: s["streak"] >= 7},
    {"icon": "QM", "label": "Quiz Master", "test": lambda s: s["quizzes"] >= 5},
    {"icon": "RH", "label": "Revision Hero", "test": lambda s: s["minutes"] >= 60},
    {"icon": "50", "label": "50 Flashcards", "test": lambda s: s["cards"] >= 50},
    {"icon": "UP", "label": "First Upload", "test": lambda s: s["docs"] >= 1},
    {"icon": "03", "label": "3 Subjects", "test": lambda s: s["subjects"] >= 3},
]


def _exam_readiness(attempts: list, docs: list) -> int:
    """Estimate readiness from quiz accuracy and how much material is indexed."""
    if not attempts and not docs:
        return 0
    accuracy = 0.0
    if attempts:
        scored = sum(a["score"] for a in attempts)
        total = sum(a["total"] for a in attempts) or 1
        accuracy = scored / total
    coverage = min(len(docs) / 4, 1.0)
    return int(round((accuracy * 0.7 + coverage * 0.3) * 100))


def render() -> None:
    """Render the dashboard."""
    db = get_database()
    store = get_vector_store()
    user = st.session_state.user

    documents = db.list_documents()
    attempts = db.list_quiz_attempts()
    cards = db.list_flashcards()
    streak = db.streak()
    minutes = db.minutes_today()
    readiness = _exam_readiness(attempts, documents)
    subject_counts = Counter(d["subject"] for d in documents)

    first_name = user["name"].split()[0]
    hero(
        f"Good to see you, {first_name}!",
        "Everything below is generated from the documents you upload — "
        "no invented facts, always with citations.",
        eyebrow="AI STUDY COACH",
    )

    # ---- Quick actions --------------------------------------------- #
    action_columns = st.columns(4)
    quick_actions = [
        ("Chat with Docs", "chat"),
        ("Flashcards", "flashcards"),
        ("Quiz", "quiz"),
        ("Notes", "notes"),
    ]
    for column, (label, target) in zip(action_columns, quick_actions):
        with column:
            if st.button(label, key=f"qa_{target}", use_container_width=True):
                st.session_state.page = target
                st.rerun()

    st.write("")

    # ---- Metrics ---------------------------------------------------- #
    metric_row(
        [
            {"icon": "ST", "value": streak, "label": "Day Streak",
             "note": "Keep it up!" if streak else "Start today"},
            {"icon": "XR", "value": f"{readiness}%", "label": "Exam Readiness",
             "note": "Based on your quizzes"},
            {"icon": "MT", "value": minutes, "label": "Min Today",
             "note": "Study time logged"},
            {"icon": "SB", "value": len(subject_counts) or 0, "label": "Subjects",
             "note": user["semester"]},
        ]
    )

    st.write("")
    left, right = st.columns([2, 1])

    # ---- Subject progress ------------------------------------------- #
    with left:
        st.markdown('<div class="card"><h3>Subject Coverage</h3>',
                    unsafe_allow_html=True)
        if not documents:
            st.caption("Upload documents to see per-subject coverage here.")
        else:
            total_chunks = sum(d["chunk_count"] for d in documents) or 1
            by_subject: dict[str, int] = {}
            for document in documents:
                by_subject[document["subject"]] = (
                    by_subject.get(document["subject"], 0) + document["chunk_count"]
                )
            for subject, chunk_count in sorted(
                by_subject.items(), key=lambda kv: kv[1], reverse=True
            ):
                share = int(round(chunk_count / total_chunks * 100))
                progress_row(subject, share, tone="good" if share >= 30 else "")
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Upload more documents", key="dash_upload"):
            st.session_state.page = "upload"
            st.rerun()

    # ---- Recent quiz scores ----------------------------------------- #
    with right:
        st.markdown('<div class="card"><h3>Recent Quiz Scores</h3>',
                    unsafe_allow_html=True)
        if not attempts:
            st.caption("No quizzes taken yet.")
        else:
            for attempt in attempts[:5]:
                percentage = int(round(attempt["score"] / max(attempt["total"], 1) * 100))
                progress_row(
                    attempt["topic"][:26],
                    percentage,
                    tone=tone_for_score(percentage),
                )
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Analyse weak topics", key="dash_weak"):
            st.session_state.page = "weak-topics"
            st.rerun()

    # ---- Agent grid -------------------------------------------------- #
    st.markdown("### AI Agents")
    for row_start in range(0, len(AGENT_TILES), 4):
        row = AGENT_TILES[row_start : row_start + 4]
        columns = st.columns(4)
        for column, tile in zip(columns, row):
            with column:
                st.markdown(
                    f"""
                    <div class="agent-tile">
                      <div class="emoji">{tile['icon']}</div>
                      <div class="title">{html.escape(tile['label'])}</div>
                      <div class="desc">{html.escape(tile['desc'])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Open", key=f"tile_{tile['id']}", use_container_width=True):
                    st.session_state.page = tile["id"]
                    st.rerun()

    st.write("")
    bottom_left, bottom_right = st.columns(2)

    # ---- Recent activity --------------------------------------------- #
    with bottom_left:
        st.markdown('<div class="card"><h3>Recent Activity</h3>',
                    unsafe_allow_html=True)
        activity = db.recent_activity(limit=6)
        if not activity:
            st.caption("Your actions will show up here.")
        else:
            for entry in activity:
                st.markdown(
                    f"<div style='display:flex;gap:10px;margin-bottom:9px;'>"
                    f"<span style='font-size:17px;'>{entry['icon']}</span>"
                    f"<span style='font-size:13px;'>{html.escape(entry['text'])}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

    # ---- Achievements ------------------------------------------------ #
    with bottom_right:
        st.markdown('<div class="card"><h3>Achievements</h3>',
                    unsafe_allow_html=True)
        stats = {
            "streak": streak,
            "quizzes": len(attempts),
            "minutes": minutes,
            "cards": len(cards),
            "docs": len(documents),
            "subjects": len(subject_counts),
        }
        badge_columns = st.columns(3)
        for position, achievement in enumerate(ACHIEVEMENTS):
            earned = achievement["test"](stats)
            with badge_columns[position % 3]:
                st.markdown(
                    f"""
                    <div style="text-align:center;padding:11px 6px;border-radius:14px;
                                border:1px solid var(--line);margin-bottom:8px;
                                opacity:{'1' if earned else '0.4'};
                                background:{'var(--primary-soft)' if earned else 'transparent'};">
                      <div style="font-size:15px;font-weight:800;color:var(--primary);">
                        {achievement['icon']}
                      </div>
                      <div style="font-size:10.5px;line-height:1.25;">
                        {html.escape(achievement['label'])}
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

    if store.is_empty:
        st.write("")
        empty_state(
            "GO",
            "Nothing indexed yet",
            "Upload your first PDF to unlock every agent on this dashboard.",
        )
