"""
Analytics — port of ``src/components/analytics/AnalyticsPage.tsx``.

Every chart here is built from real SQLite data rather than the mock arrays the
original component used.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.ui import empty_state, hero, metric_row
from utils.session import get_database, get_vector_store

_TRANSPARENT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=34, b=10),
    font=dict(color="#6B6A62"),
)


def render() -> None:
    """Render the Analytics page."""
    db = get_database()
    store = get_vector_store()

    hero(
        "Analytics",
        "Your study patterns, quiz accuracy and document coverage at a glance.",
        eyebrow="📊 ANALYTICS",
    )

    documents = db.list_documents()
    attempts = db.list_quiz_attempts()
    cards = db.list_flashcards()

    accuracy = 0
    if attempts:
        scored = sum(a["score"] for a in attempts)
        total = sum(a["total"] for a in attempts) or 1
        accuracy = int(round(scored / total * 100))

    metric_row([
        {"icon": "❓", "value": len(attempts), "label": "Quizzes Taken"},
        {"icon": "🎯", "value": f"{accuracy}%", "label": "Overall Accuracy"},
        {"icon": "🃏", "value": len(cards), "label": "Flashcards"},
        {"icon": "🧩", "value": store.size, "label": "Indexed Chunks"},
    ])

    st.write("")

    # ---- Study minutes over time --------------------------------------- #
    activity = db.activity_by_day(days=14)
    if activity:
        st.markdown('<div class="card"><h3>⏱️ Study minutes (last 14 days)</h3>',
                    unsafe_allow_html=True)
        frame = pd.DataFrame(activity)
        figure = go.Figure(
            go.Scatter(
                x=frame["day"], y=frame["minutes"],
                mode="lines+markers", fill="tozeroy",
                line=dict(color="#F2A900", width=3),
                fillcolor="rgba(242,169,0,0.18)",
                marker=dict(size=8, color="#FFE08A",
                            line=dict(color="#F2A900", width=2)),
            )
        )
        figure.update_layout(height=280, **_TRANSPARENT)
        figure.update_xaxes(showgrid=False)
        figure.update_yaxes(gridcolor="rgba(43,42,38,0.07)", title="minutes")
        st.plotly_chart(figure, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        empty_state("📈", "No activity recorded yet",
                    "Use the agents and your study time will be tracked here.")

    left_column, right_column = st.columns(2)

    # ---- Quiz accuracy trend -------------------------------------------- #
    with left_column:
        st.markdown('<div class="card"><h3>🎯 Quiz accuracy over time</h3>',
                    unsafe_allow_html=True)
        if attempts:
            frame = pd.DataFrame([
                {
                    "Attempt": index + 1,
                    "Topic": a["topic"],
                    "Score %": int(round(a["score"] / max(a["total"], 1) * 100)),
                }
                for index, a in enumerate(reversed(attempts))
            ])
            figure = px.line(frame, x="Attempt", y="Score %", markers=True,
                             hover_data=["Topic"])
            figure.update_traces(line=dict(color="#F2A900", width=3),
                                 marker=dict(size=9, color="#FFE08A"))
            figure.update_layout(height=280, yaxis_range=[0, 100], **_TRANSPARENT)
            figure.update_yaxes(gridcolor="rgba(43,42,38,0.07)")
            st.plotly_chart(figure, use_container_width=True)
        else:
            st.caption("Take a quiz to populate this chart.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ---- Document coverage ---------------------------------------------- #
    with right_column:
        st.markdown('<div class="card"><h3>📚 Coverage by subject</h3>',
                    unsafe_allow_html=True)
        if documents:
            by_subject: dict[str, int] = {}
            for document in documents:
                by_subject[document["subject"]] = (
                    by_subject.get(document["subject"], 0) + document["chunk_count"]
                )
            frame = pd.DataFrame(
                {"Subject": list(by_subject), "Chunks": list(by_subject.values())}
            )
            figure = px.pie(
                frame, names="Subject", values="Chunks", hole=0.55,
                color_discrete_sequence=["#F2A900", "#FFE08A", "#FFD166",
                                         "#E9B949", "#C98600", "#FFF3C4"],
            )
            figure.update_layout(height=280, **_TRANSPARENT)
            st.plotly_chart(figure, use_container_width=True)
        else:
            st.caption("Upload documents to populate this chart.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ---- Flashcard mastery ------------------------------------------------ #
    if cards:
        st.markdown('<div class="card"><h3>🃏 Flashcard mastery (Leitner boxes)</h3>',
                    unsafe_allow_html=True)
        distribution = {box: 0 for box in range(1, 6)}
        for card in cards:
            distribution[card["box"]] = distribution.get(card["box"], 0) + 1
        frame = pd.DataFrame({
            "Box": [f"Box {b}" for b in distribution],
            "Cards": list(distribution.values()),
        })
        figure = px.bar(frame, x="Box", y="Cards",
                        color_discrete_sequence=["#F2A900"])
        figure.update_layout(height=250, **_TRANSPARENT)
        figure.update_yaxes(gridcolor="rgba(43,42,38,0.07)")
        st.plotly_chart(figure, use_container_width=True)
        st.caption("Box 1 = needs work · Box 5 = mastered")
        st.markdown("</div>", unsafe_allow_html=True)

    # ---- Attempts table ---------------------------------------------------- #
    if attempts:
        st.markdown("##### 📋 Quiz history")
        st.dataframe(
            pd.DataFrame([
                {
                    "Topic": a["topic"],
                    "Score": f"{a['score']}/{a['total']}",
                    "Percent": f"{int(round(a['score'] / max(a['total'], 1) * 100))}%",
                    "Date": a["created_at"][:16].replace("T", " "),
                }
                for a in attempts
            ]),
            use_container_width=True,
            hide_index=True,
        )
