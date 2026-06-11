import streamlit as st

from pages.upload import show_upload_page
from pages.ask_questions import show_qa_page
from auth.signup import create_user
from auth.login import login_user
from auth.logout import logout_user

from auth.session_manager import (
    initialize_session
)

from database.init_db import (
    initialize_database
)

from pages.dashboard import (
    show_dashboard
)

from pages.upload import (
    show_upload_page
)

from pages.ask_questions import (
    show_qa_page
)

# -----------------------------
# INITIALIZATION
# -----------------------------

initialize_database()

initialize_session()

st.set_page_config(
    page_title="Subject Guide AI",
    page_icon="🎓",
    layout="wide"
)

# -----------------------------
# LOAD CSS
# -----------------------------

try:

    with open(
        "assets/styles.css",
        encoding="utf-8"
    ) as f:

        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )

except Exception:
    pass


# -----------------------------
# AUTHENTICATION SCREEN
# -----------------------------

if not st.session_state.logged_in:

    st.title("🎓 Subject Guide AI")

    st.markdown(
        """
        Upload notes, generate quizzes,
        prepare for viva, and build your
        personalized study assistant.
        """
    )

    tab1, tab2 = st.tabs(
        [
            "🔑 Login",
            "📝 Signup"
        ]
    )

    # -----------------------------
    # LOGIN TAB
    # -----------------------------

    with tab1:

        st.subheader("Login")

        email = st.text_input(
            "Email",
            key="login_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "Login",
            use_container_width=True
        ):

            user = login_user(
                email,
                password
            )

            if user:

                st.session_state.logged_in = True

                st.session_state.user_id = user["id"]

                st.session_state.user_name = user["name"]

                st.success(
                    "Login Successful"
                )

                st.rerun()

            else:

                st.error(
                    "Invalid Credentials"
                )

    # -----------------------------
    # SIGNUP TAB
    # -----------------------------

    with tab2:

        st.subheader("Create Account")

        name = st.text_input(
            "Full Name",
            key="signup_name"
        )

        email = st.text_input(
            "Email",
            key="signup_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="signup_password"
        )

        if st.button(
            "Create Account",
            use_container_width=True
        ):

            success, msg = create_user(
                name,
                email,
                password
            )

            if success:

                st.success(msg)

            else:

                st.error(msg)

# -----------------------------
# MAIN APPLICATION
# -----------------------------

else:

    with st.sidebar:

        st.title("🎓 Subject Guide AI")

        st.write(
            f"Welcome, **{st.session_state.user_name}**"
        )

        st.divider()

        menu = st.radio(
            "Navigation",
            [
                "Dashboard",
                "Upload",
                "Ask Questions"
            ]
        )

        st.divider()

        if st.button(
            "🚪 Logout",
            use_container_width=True
        ):
            logout_user()

    # -----------------------------
    # PAGE ROUTING
    # -----------------------------

    if menu == "Dashboard":

        show_dashboard()

    elif menu == "Upload":

        show_upload_page()

    elif menu == "Ask Questions":

        show_qa_page()