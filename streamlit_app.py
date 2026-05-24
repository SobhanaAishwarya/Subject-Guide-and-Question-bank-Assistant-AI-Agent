import streamlit as st
from document_processing import load_pdf, load_docx, split_text
from vector_store import create_vector_store
from agent import generate_answer

# -----------------------------------
# PAGE CONFIG
# -----------------------------------
st.set_page_config(
    page_title="Subject Guide and Question Bank Assistant AI Agent",
    layout="wide"
)

# -----------------------------------
# PROFESSIONAL LIGHT UI CSS
# -----------------------------------
st.markdown("""
<style>

/* Main App */
.stApp {
    background-color: #f8fafc;
    color: #111827;
    font-family: 'Segoe UI', sans-serif;
}

/* Main Container */
.main .block-container {
    padding-top: 2rem;
    padding-left: 4rem;
    padding-right: 4rem;
    max-width: 1200px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: white;
    border-right: 1px solid #e5e7eb;
}

/* Sidebar Text */
section[data-testid="stSidebar"] * {
    color: #111827 !important;
}

/* Main Title */
.main-title {
    font-size: 48px;
    font-weight: 700;
    color: #111827;
    margin-bottom: 10px;
    line-height: 1.2;
}

/* Subtitle */
.sub-title {
    font-size: 18px;
    color: #6b7280;
    margin-bottom: 40px;
    max-width: 850px;
}

/* File Upload */
[data-testid="stFileUploader"] {
    background-color: white;
    border: 2px dashed #d1d5db;
    border-radius: 18px;
    padding: 25px;
}

/* Input Box */
.stTextInput input {
    background-color: white !important;
    color: #111827 !important;
    border: 1px solid #d1d5db !important;
    border-radius: 12px !important;
    padding: 14px !important;
}

/* Buttons */
.stButton > button {
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.7rem 1rem;
    font-weight: 600;
}

.stButton > button:hover {
    background: #1d4ed8;
}

/* Metrics */
[data-testid="metric-container"] {
    background: white;
    border: 1px solid #e5e7eb;
    padding: 18px;
    border-radius: 16px;
}

/* User Chat */
.chat-user {
    background: #2563eb;
    color: white;
    padding: 16px;
    border-radius: 16px;
    margin-bottom: 15px;
    margin-left: auto;
    width: fit-content;
    max-width: 75%;
}

/* Bot Chat */
.chat-bot {
    background: white;
    color: #111827;
    padding: 18px;
    border-radius: 16px;
    margin-bottom: 20px;
    border: 1px solid #e5e7eb;
    width: fit-content;
    max-width: 80%;
}

/* Horizontal Line */
hr {
    border: 1px solid #e5e7eb;
}

/* Hide Streamlit Branding */
footer {
    visibility: hidden;
}

header {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------------
# SIDEBAR
# -----------------------------------
with st.sidebar:

    st.markdown("## AI Academic Assistant")

    st.markdown("---")

    st.markdown("""
    ### Features

    - PDF/DOCX Question Answering
    - Semantic Search
    - AI Generated Responses
    - RAG Architecture
    - Academic Assistance
    - Question Bank Support
    """)

    st.markdown("---")

    st.info("Upload academic material and ask questions.")

# -----------------------------------
# MAIN TITLE
# -----------------------------------
st.markdown("""
<div class="main-title">
Subject Guide and Question Bank Assistant AI Agent
</div>

<div class="sub-title">
AI-powered academic assistant using semantic search and Retrieval-Augmented Generation to provide intelligent answers from uploaded study materials.
</div>
""", unsafe_allow_html=True)

# -----------------------------------
# SESSION STATE
# -----------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -----------------------------------
# FILE UPLOADER
# -----------------------------------
uploaded_file = st.file_uploader(
    "Upload Study Material",
    type=["pdf", "docx"]
)

# -----------------------------------
# PROCESS FILE
# -----------------------------------
if uploaded_file:

    with st.spinner("Reading document..."):

        if uploaded_file.name.endswith(".pdf"):
            text = load_pdf(uploaded_file)

        elif uploaded_file.name.endswith(".docx"):
            text = load_docx(uploaded_file)

        else:
            st.error("Unsupported file type")
            st.stop()

    st.success("Document loaded successfully.")

    # -----------------------------------
    # TEXT SPLITTING
    # -----------------------------------
    chunks = split_text(text)

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Text Length", len(text))

    with col2:
        st.metric("Chunks Created", len(chunks))

    # -----------------------------------
    # VECTOR STORE
    # -----------------------------------
    with st.spinner("Creating vector database..."):
        vectorstore = create_vector_store(chunks)

    st.success("AI knowledge base created.")

    # -----------------------------------
    # QUICK QUESTIONS
    # -----------------------------------
    st.markdown("### Suggested Queries")

    q1, q2, q3 = st.columns(3)

    with q1:
        if st.button("Important Topics"):
            st.session_state.quick_question = (
                "What are the important topics in this document?"
            )

    with q2:
        if st.button("Document Summary"):
            st.session_state.quick_question = (
                "Give a summary of this document."
            )

    with q3:
        if st.button("Viva Questions"):
            st.session_state.quick_question = (
                "Generate important viva questions from this document."
            )

    # -----------------------------------
    # USER INPUT
    # -----------------------------------
    default_question = st.session_state.get("quick_question", "")

    query = st.text_input(
        "Ask your question",
        value=default_question,
        placeholder="Example: Explain normalization in DBMS"
    )

    # -----------------------------------
    # GENERATE ANSWER
    # -----------------------------------
    if query:

        st.session_state.chat_history.append(("user", query))

        with st.spinner("Generating response..."):
            answer = generate_answer(query, vectorstore)

        st.session_state.chat_history.append(("bot", answer))

    # -----------------------------------
    # CHAT SECTION
    # -----------------------------------
    st.markdown("---")
    st.markdown("### Conversation")

    for role, message in st.session_state.chat_history:

        if role == "user":

            st.markdown(
                f"""
                <div class="chat-user">
                <b>You</b><br><br>
                {message}
                </div>
                """,
                unsafe_allow_html=True
            )

        else:

            st.markdown(
                f"""
                <div class="chat-bot">
                <b>AI Assistant</b><br><br>
                {message}
                </div>
                """,
                unsafe_allow_html=True
            )

# -----------------------------------
# FOOTER
# -----------------------------------
st.markdown("---")

st.markdown("""
<center>

Built using Python, Streamlit, LangChain, HuggingFace,
ChromaDB and RAG Architecture

</center>
""", unsafe_allow_html=True)