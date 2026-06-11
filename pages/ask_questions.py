import streamlit as st

from rag.vectorstore import (
    load_vectorstore
)

from rag.retrieval import (
    retrieve_context
)

from agents.qa_agent import (
    ask_question
)


def show_qa_page():

    st.title(
        "🤖 Ask Questions"
    )

    question = st.text_input(
        "Enter your question"
    )

    if st.button(
        "Ask"
    ):

        try:

            vectorstore = load_vectorstore()

            context = retrieve_context(
                vectorstore,
                question
            )

            answer = ask_question(
                question,
                context
            )

            st.markdown(answer)

        except Exception:

            st.error(
                "Upload documents first."
            )