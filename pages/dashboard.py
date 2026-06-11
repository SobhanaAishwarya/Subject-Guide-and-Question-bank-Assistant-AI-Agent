import streamlit as st


def show_dashboard():

    st.title("🎓 Subject Guide AI")

    st.success(
        f"Welcome {st.session_state.user_name}"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Documents",
            "0"
        )

    with col2:
        st.metric(
            "Questions Asked",
            "0"
        )

    with col3:
        st.metric(
            "Quiz Score",
            "0%"
        )

    st.divider()

    st.subheader(
        "Recent Activity"
    )

    st.info(
        "No activity yet."
    )