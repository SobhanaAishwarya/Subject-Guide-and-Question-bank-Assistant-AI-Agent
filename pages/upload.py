import streamlit as st
import os

from rag.document_loader import (
    load_document
)

from rag.chunking import (
    create_chunks
)

from rag.vectorstore import (
    create_vectorstore,
    save_vectorstore
)

from config.settings import (
    UPLOAD_DIR
)


def show_upload_page():

    st.title("📚 Upload Documents")

    uploaded_file = st.file_uploader(
        "Upload PDF or DOCX",
        type=["pdf", "docx"]
    )

    if uploaded_file:

        file_path = os.path.join(
            UPLOAD_DIR,
            uploaded_file.name
        )

        with open(
            file_path,
            "wb"
        ) as f:

            f.write(
                uploaded_file.getbuffer()
            )

        with st.spinner(
            "Processing..."
        ):

            text = load_document(
                file_path
            )

            chunks = create_chunks(
                text
            )

            vectorstore = create_vectorstore(
                chunks
            )

            save_vectorstore(
                vectorstore
            )

        st.success(
            "Knowledge Base Created Successfully"
        )