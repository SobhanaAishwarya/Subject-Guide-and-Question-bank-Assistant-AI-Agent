import streamlit as st
import os

from config.settings import VECTORSTORE_DIR

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

    st.title("🤖 Ask Questions")

    # DEBUG INFO
    kb_path = os.path.join(
        VECTORSTORE_DIR,
        "knowledge_base"
    )

    st.write(
        "Vectorstore Path:",
        kb_path
    )

    st.write(
        "Knowledge Base Exists:",
        os.path.exists(kb_path)
    )

    question = st.text_input(
        "Enter your question"
    )

    if st.button("Ask"):

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

        except Exception as e:

            st.error(
                f"Error: {str(e)}"
            )