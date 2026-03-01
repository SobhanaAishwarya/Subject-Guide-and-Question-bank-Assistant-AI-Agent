# app.py

import streamlit as st
from document_processing import load_pdf, load_docx, split_text
from vector_store import create_vector_store
from agent import generate_answer


st.title("📚 Agentic AI Academic Assistant")

# Upload file
uploaded_file = st.file_uploader("Upload your study material (PDF or DOCX)")

if uploaded_file:
    
    # 1️ Extract text
    if uploaded_file.name.endswith(".pdf"):
        text = load_pdf(uploaded_file)
    
    elif uploaded_file.name.endswith(".docx"):
        text = load_docx(uploaded_file)
    
    else:
        st.error("Unsupported file type")
        st.stop()
    
    st.success("Document loaded successfully!")
    
    # 2️ Split into chunks
    chunks = split_text(text)
    
    # 3️ Create vector store
    vectorstore = create_vector_store(chunks)
    
    # 4️ User Query
    query = st.text_input("Ask your question")
    
    if query:
        answer = generate_answer(query, vectorstore)
        
        st.subheader("📌 Answer:")
        st.write(answer)