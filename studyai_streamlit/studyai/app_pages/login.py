"""Login page — real email/password Sign In and Sign Up.

Replaces the original mock gate (any name, no password) with actual account
creation and verification, backed by ``services.auth`` and the ``users``
table in SQLite.
"""

from __future__ import annotations

import streamlit as st

from services import auth
from utils.session import get_database, log_in


def render() -> None:
    """Render the Sign In / Sign Up gate."""
    st.markdown(
        """
        <div class="login-shell">
          <div class="login-brand">
            <div class="logo">S</div>
            <div class="name">StudyAI</div>
          </div>
          <p class="tagline">Every answer, traced back to your own notes.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    db = get_database()
    _, middle, _ = st.columns([1, 2, 1])
    with middle:
        signin_tab, signup_tab = st.tabs(["Sign In", "Sign Up"])

        # ---- Sign In ----------------------------------------------------- #
        with signin_tab:
            with st.form("signin_form"):
                email = st.text_input(
                    "Email", key="signin_email", placeholder="abhi@gmail.com"
                )
                password = st.text_input(
                    "Password", type="password", key="signin_password",
                    placeholder="Your password",
                )
                submitted = st.form_submit_button(
                    "Sign In", type="primary", use_container_width=True
                )
            if submitted:
                user, error = auth.sign_in(db, email, password)
                if error:
                    st.error(error)
                else:
                    log_in(user)

        # ---- Sign Up ------------------------------------------------------- #
        with signup_tab:
            with st.form("signup_form"):
                name = st.text_input(
                    "Your name", key="signup_name", placeholder="Abhishek Kumar"
                )
                email = st.text_input(
                    "Email", key="signup_email", placeholder="abhi@gmail.com"
                )
                semester = st.selectbox(
                    "Semester",
                    [f"Semester {n}" for n in range(1, 9)],
                    index=4,
                    key="signup_semester",
                )
                password = st.text_input(
                    "Password", type="password", key="signup_password",
                    placeholder="At least 8 characters",
                )
                confirm = st.text_input(
                    "Confirm password", type="password", key="signup_confirm",
                    placeholder="Re-enter your password",
                )
                submitted = st.form_submit_button(
                    "Create account", type="primary", use_container_width=True
                )
            if submitted:
                user, error = auth.sign_up(db, name, email, password, confirm, semester)
                if error:
                    st.error(error)
                else:
                    st.success("Account created — signing you in…")
                    log_in(user)
