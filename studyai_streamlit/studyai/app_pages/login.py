"""Login page — port of ``src/components/auth/LoginPage.tsx``.

The original used a mock user object with no real auth backend. This keeps the
same behaviour (a friendly gate, no credentials verified) while letting the
student set the name shown throughout the dashboard.
"""

from __future__ import annotations

import streamlit as st


def render() -> None:
    """Render the login gate."""
    st.markdown(
        """
        <div class="login-shell">
          <div class="logo">🎓</div>
          <h1>Welcome to StudyAI</h1>
          <p>Your agentic study assistant. Upload your notes, ask anything,
             and get answers grounded in your own documents.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, middle, _ = st.columns([1, 2, 1])
    with middle:
        name = st.text_input("Your name", value="Student", key="login_name")
        email = st.text_input("Email", value="student@studyai.app", key="login_email")
        semester = st.selectbox(
            "Semester",
            [f"Semester {n}" for n in range(1, 9)],
            index=4,
            key="login_semester",
        )

        if st.button("🚀  Enter StudyAI", type="primary", use_container_width=True):
            clean_name = name.strip() or "Student"
            initials = "".join(part[0] for part in clean_name.split()[:2]).upper() or "ST"
            st.session_state.user = {
                "name": clean_name,
                "email": email.strip(),
                "avatar": initials,
                "semester": semester,
            }
            st.session_state.authenticated = True
            st.session_state.page = "dashboard"
            st.rerun()

        st.caption(
            "No password required — this is a local study workspace. "
            "Your documents never leave your Streamlit instance except as "
            "retrieved context sent to OpenRouter."
        )
