"""
Profile — port of ``src/components/profile/ProfilePage.tsx``.

Adds real settings the original mock lacked: OpenRouter connection testing,
retrieval tuning, conversation history and data management.
"""

from __future__ import annotations

import streamlit as st

from components.ui import hero, metric_row
from config import AVAILABLE_MODELS, settings
from utils.session import get_database, get_llm, get_vector_store, reset_chat


def render() -> None:
    """Render the Profile page."""
    db = get_database()
    store = get_vector_store()
    user = st.session_state.user

    hero(
        f"{user['name']}",
        f"{user['email']} · {user['semester']}",
        eyebrow="👤 PROFILE",
    )

    metric_row([
        {"icon": "🔥", "value": db.streak(), "label": "Day Streak"},
        {"icon": "📄", "value": len(db.list_documents()), "label": "Documents"},
        {"icon": "❓", "value": len(db.list_quiz_attempts()), "label": "Quizzes"},
        {"icon": "🃏", "value": len(db.list_flashcards()), "label": "Flashcards"},
    ])

    st.write("")
    profile_tab, ai_tab, data_tab, history_tab = st.tabs(
        ["👤 Profile", "🤖 AI Settings", "💾 Data", "💬 History"]
    )

    # ---- Profile --------------------------------------------------------- #
    with profile_tab:
        name = st.text_input("Name", value=user["name"], key="prof_name")
        email = st.text_input("Email", value=user["email"], key="prof_email")
        semesters = [f"Semester {n}" for n in range(1, 9)]
        semester = st.selectbox(
            "Semester",
            semesters,
            index=semesters.index(user["semester"]) if user["semester"] in semesters else 4,
            key="prof_sem",
        )
        if st.button("💾  Save profile", type="primary"):
            clean = name.strip() or "Student"
            st.session_state.user = {
                "name": clean,
                "email": email.strip(),
                "avatar": "".join(p[0] for p in clean.split()[:2]).upper() or "ST",
                "semester": semester,
            }
            st.success("Profile updated.")
            st.rerun()

    # ---- AI settings ------------------------------------------------------ #
    with ai_tab:
        st.markdown("##### 🔌 OpenRouter connection")
        if settings.is_configured:
            st.success("API key detected.")
        else:
            st.error(
                "No API key found. Add `OPENROUTER_API_KEY` to `.env` locally, "
                "or to **Settings → Secrets** on Streamlit Cloud."
            )

        if st.button("🩺  Test connection"):
            with st.spinner("Pinging OpenRouter…"):
                ok, message = get_llm().health_check()
            (st.success if ok else st.error)(message)

        st.divider()
        st.markdown("##### 🤖 Model")
        current = st.session_state.get("model", settings.openrouter_model)
        options = list(dict.fromkeys([current] + AVAILABLE_MODELS))
        # NOTE: a different key from the sidebar picker — the sidebar renders on
        # every page, so reusing "model" here would be a duplicate widget id.
        chosen = st.selectbox("Active model", options, index=options.index(current),
                              key="profile_model")
        if chosen != current:
            st.session_state.model = chosen
            st.rerun()
        st.caption("Every model above is served through https://openrouter.ai/api/v1")

        st.divider()
        st.markdown("##### 🔍 Retrieval")
        st.slider(
            "Chunks retrieved per question (top-k)", 3, 15,
            st.session_state.get("top_k", settings.top_k), key="top_k",
            help="Higher = more context, slower and more tokens.",
        )
        st.slider(
            "Minimum similarity", 0.0, 0.8,
            st.session_state.get("min_similarity", settings.min_similarity), 0.05,
            key="min_similarity",
            help="Chunks below this are ignored, which is what triggers the "
                 "'not found in your documents' response.",
        )
        st.caption(
            f"Embeddings: `{settings.embedding_model}` · "
            f"chunk size {settings.chunk_size} · overlap {settings.chunk_overlap}"
        )

    # ---- Data -------------------------------------------------------------- #
    with data_tab:
        st.markdown("##### 📊 Storage")
        st.write(f"- **{store.size}** indexed chunks across "
                 f"**{len(store.sources)}** document(s)")
        st.write(f"- Vector store: `{store.store_dir}`")
        st.write(f"- Database: `{db.path}`")

        st.divider()
        st.markdown("##### ⚠️ Danger zone")
        danger_left, danger_middle, danger_right = st.columns(3)
        with danger_left:
            if st.button("🗑️  Clear chat history", use_container_width=True):
                db.clear_session(st.session_state.session_id)
                reset_chat()
                st.success("Chat history cleared.")
        with danger_middle:
            if st.button("🗑️  Clear flashcards", use_container_width=True):
                db.delete_flashcards()
                st.success("Flashcards cleared.")
        with danger_right:
            if st.button("🗑️  Clear vector index", use_container_width=True):
                for document in db.list_documents():
                    db.delete_document(document["doc_id"])
                store.clear()
                st.success("Index cleared.")
                st.rerun()

    # ---- History ----------------------------------------------------------- #
    with history_tab:
        sessions = db.list_sessions()
        if not sessions:
            st.caption("No saved conversations yet.")
        else:
            for session in sessions[:20]:
                messages = db.get_messages(session["session_id"])
                first = next((m["content"] for m in messages if m["role"] == "user"), "…")
                label = (
                    f"💬 {first[:64]} · {session['turns']} turns · "
                    f"{session['started'][:10]}"
                )
                with st.expander(label):
                    for message in messages:
                        who = "🧑‍🎓 You" if message["role"] == "user" else "🎓 StudyAI"
                        st.markdown(f"**{who}:** {message['content'][:900]}")
                    if st.button("🗑️ Delete", key=f"del_sess_{session['session_id']}"):
                        db.clear_session(session["session_id"])
                        st.rerun()
