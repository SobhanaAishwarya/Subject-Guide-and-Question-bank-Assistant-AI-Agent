import streamlit as st
from document_processing import load_pdf, load_docx, split_text
from vector_store import create_vector_store
from agent import generate_answer

# -----------------------------------
# PAGE CONFIG
# -----------------------------------
st.set_page_config(
    page_title="Subject Guide and Question Bank Assistant AI Agent",
    page_icon="📚",
    layout="wide"
)

# -----------------------------------
# CUSTOM CSS
# -----------------------------------
st.markdown("""
<style>

.main {
    background-color: #0E1117;
    color: white;
}

.stApp {
    background: linear-gradient(to right, #0f172a, #1e293b);
}

h1, h2, h3 {
    color: #38bdf8;
}

.chat-user {
    background-color: #2563eb;
    padding: 15px;
    border-radius: 12px;
    margin-bottom: 10px;
    color: white;
    font-size: 17px;
}

.chat-bot {
    background-color: #1e293b;
    padding: 15px;
    border-radius: 12px;
    margin-bottom: 20px;
    border-left: 5px solid #38bdf8;
    color: white;
    font-size: 17px;
}

.sidebar .sidebar-content {
    background-color: #111827;
}

.stButton>button {
    background-color: #2563eb;
    color: white;
    border-radius: 10px;
    height: 3em;
    width: 100%;
    font-size: 16px;
}

.stTextInput>div>div>input {
    background-color: #1e293b;
    color: white;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------------
# SIDEBAR
# -----------------------------------
with st.sidebar:

    st.title("📚 AI Academic Assistant")

    st.markdown("---")

    st.markdown("""
    ### 🚀 Features

    ✅ PDF/DOCX Question Answering  
    ✅ Semantic Search  
    ✅ AI Generated Answers  
    ✅ RAG Architecture  
    ✅ Academic Assistance  
    ✅ Question Bank Support  
    """)

    st.markdown("---")

    st.info("Upload your academic material and start asking questions.")

# -----------------------------------
# MAIN TITLE
# -----------------------------------
st.title("📚 Subject Guide and Question Bank Assistant AI Agent")

st.markdown("""
### 🎓 AI Powered Academic Learning Assistant

Upload your:
- Subject Notes
- Question Banks
- PDFs
- DOCX Files

Ask questions and get intelligent answers instantly.
""")

# -----------------------------------
# SESSION STATE
# -----------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -----------------------------------
# FILE UPLOAD
# -----------------------------------
uploaded_file = st.file_uploader(
    "📂 Upload your study material",
    type=["pdf", "docx"]
)

# -----------------------------------
# PROCESS FILE
# -----------------------------------
if uploaded_file:

    with st.spinner("📖 Reading document..."):

        # PDF
        if uploaded_file.name.endswith(".pdf"):
            text = load_pdf(uploaded_file)

        # DOCX
        elif uploaded_file.name.endswith(".docx"):
            text = load_docx(uploaded_file)

        else:
            st.error("Unsupported file type")
            st.stop()

    st.success("✅ Document loaded successfully!")

    # -----------------------------------
    # DOCUMENT STATS
    # -----------------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.metric("📄 Text Length", len(text))

    # Split text
    chunks = split_text(text)

    with col2:
        st.metric("🧩 Chunks Created", len(chunks))

    # -----------------------------------
    # VECTOR STORE
    # -----------------------------------
    with st.spinner("🧠 Creating AI knowledge base..."):
        vectorstore = create_vector_store(chunks)

    st.success("✅ AI Knowledge Base Ready!")

    # -----------------------------------
    # QUICK QUESTIONS
    # -----------------------------------
    st.subheader("🔥 Suggested Questions")

    q1, q2, q3 = st.columns(3)

    with q1:
        if st.button("Important Topics"):
            st.session_state.quick_question = "What are the important topics in this document?"

    with q2:
        if st.button("Generate Summary"):
            st.session_state.quick_question = "Give a summary of this document."

    with q3:
        if st.button("Generate Viva Questions"):
            st.session_state.quick_question = "Generate important viva questions from this document."

    # -----------------------------------
    # USER INPUT
    # -----------------------------------
    default_question = st.session_state.get("quick_question", "")

    query = st.text_input(
        "💬 Ask your academic question",
        value=default_question,
        placeholder="Example: Explain normalization in DBMS"
    )

    # -----------------------------------
    # GENERATE ANSWER
    # -----------------------------------
    if query:

        # Add user chat
        st.session_state.chat_history.append(("user", query))

        with st.spinner("🤖 AI is generating answer..."):
            answer = generate_answer(query, vectorstore)

        # Add bot chat
        st.session_state.chat_history.append(("bot", answer))

    # -----------------------------------
    # CHAT DISPLAY
    # -----------------------------------
    st.markdown("---")
    st.subheader("💬 AI Conversation")

    for role, message in st.session_state.chat_history:

        if role == "user":
            st.markdown(
                f"<div class='chat-user'><b>🧑 You:</b><br>{message}</div>",
                unsafe_allow_html=True
            )

        else:
            st.markdown(
                f"<div class='chat-bot'><b>🤖 AI Assistant:</b><br>{message}</div>",
                unsafe_allow_html=True
            )

# -----------------------------------
# FOOTER
# -----------------------------------
st.markdown("---")

st.markdown("""
<center>

### 🚀 Built with Agentic AI + RAG Architecture

Powered by:
Python | Streamlit | HuggingFace | FAISS | LangChain

</center>
""", unsafe_allow_html=True)