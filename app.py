import streamlit as st
from document_processing import load_pdf, load_docx, split_text
from vector_store import create_vector_store
from agent import generate_answer

st.title("📚 Agentic AI Academic Assistant")

uploaded_file = st.file_uploader("Upload your study material (PDF or DOCX)")

if uploaded_file:

    # Extract text
    if uploaded_file.name.endswith(".pdf"):
        text = load_pdf(uploaded_file)
        st.write("Text length:", len(text))

    elif uploaded_file.name.endswith(".docx"):
        text = load_docx(uploaded_file)

    else:
        st.error("Unsupported file type")
        st.stop()

    st.success("Document loaded successfully!")

    # Split text
    chunks = split_text(text)
    st.write("Chunks created:", len(chunks))

    # Create vector database
    vectorstore = create_vector_store(chunks)

    # User question
    query = st.text_input("Ask your question")

    if query:
        answer = generate_answer(query, vectorstore)

        st.subheader("📌 Answer:")
        st.write(answer)