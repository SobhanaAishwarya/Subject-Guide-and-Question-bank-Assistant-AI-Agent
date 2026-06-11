import streamlit as st


def logout_user():

    st.session_state.logged_in = False

    st.session_state.user_id = None

    st.session_state.user_name = None

    st.rerun()