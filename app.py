import streamlit as st

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

initialize_database()

initialize_session()

st.set_page_config(
    page_title="Subject Guide AI",
    page_icon="🎓",
    layout="wide"
)

try:

    with open(
        "assets/styles.css"
    ) as f:

        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )

except:
    pass


if not st.session_state.logged_in:

    st.title("🎓 Subject Guide AI")

    tab1, tab2 = st.tabs(
        [
            "Login",
            "Signup"
        ]
    )

    with tab1:

        email = st.text_input(
            "Email"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button("Login"):

            user = login_user(
                email,
                password
            )

            if user:

                st.session_state.logged_in = True

                st.session_state.user_id = user["id"]

                st.session_state.user_name = user["name"]

                st.rerun()

            else:

                st.error(
                    "Invalid Credentials"
                )

    with tab2:

        name = st.text_input(
            "Full Name"
        )

        email = st.text_input(
            "Signup Email"
        )

        password = st.text_input(
            "Signup Password",
            type="password"
        )

        if st.button("Create Account"):

            success, msg = create_user(
                name,
                email,
                password
            )

            if success:

                st.success(msg)

            else:

                st.error(msg)

else:

    with st.sidebar:

        st.write(
            f"👋 {st.session_state.user_name}"
        )

        if st.button("Logout"):

            logout_user()

    show_dashboard()