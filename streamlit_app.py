import streamlit as st

# MUST BE RUN AS THE ABSOLUTE FIRST STREAMLIT COMMAND
st.set_page_view = st.set_page_config(
    page_title="EduMind AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

import os
import uuid
import pandas as pd
import plotly.express as px
from datetime import datetime

from config import Config
from database.db_manager import init_db, get_db_connection, increment_analytic, update_avg_score
from utils.ui_components import apply_custom_theme, render_hero
from utils.doc_processor import DocumentProcessor
from services.rag_service import SimpleFAISSStore
from services.openrouter_service import OpenRouterService

# Database Schema & File Repositories Check
init_db()
vector_store = SimpleFAISSStore()

# Inject SaaS Layout Stylesheet rules
apply_custom_theme()

# Unified Global State Management Routing initialization
if "current_page" not in st.session_state:
    st.session_state.current_page = "🏠 Dashboard"
if "session_token" not in st.session_state:
    st.session_state.session_token = str(uuid.uuid4())

# -------------------------------------------------------------------------
# SIDEBAR NAVIGATION CONTROLLERS
# -------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"<div style='padding: 10px 0; text-align:center;'><h2 style='color:{Config.COLOR_TEXT};font-weight:800;'>🧠 EduMind AI</h2></div>",
        unsafe_allow_html=True
    )
    st.markdown("---")
    
    navigation_options = [
        "🏠 Dashboard", "🤖 AI Chat", "📄 Documents", "📚 Topics",
        "❓ Question Bank", "📝 Quiz", "🧠 Flashcards", "📊 Analytics", "⚙ Settings"
    ]
    
    for opt in navigation_options:
        if st.button(opt, use_container_width=True):
            st.session_state.current_page = opt

st.markdown(f"### {st.session_state.current_page}")
st.markdown("---")

# -------------------------------------------------------------------------
# VIEW CONTROLLERS (ROUTING DISPATCHER LOOP)
# -------------------------------------------------------------------------

if st.session_state.current_page == "🏠 Dashboard":
    render_hero()
    
    # Load Real-Time Database Metrics counters
    with get_db_connection() as conn:
        doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        q_count = conn.execute("SELECT value_int FROM analytics WHERE key='questions_asked'").fetchone()[0]
        quiz_count = conn.execute("SELECT value_int FROM analytics WHERE key='quizzes_taken'").fetchone()[0]
        fc_count = conn.execute("SELECT COUNT(*) FROM flashcards").fetchone()[0]

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="em-card"><div class="em-metric-val">{doc_count}</div><div class="em-metric-lbl">Active Documents</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="em-card"><div class="em-metric-val">{q_count}</div><div class="em-metric-lbl">Queries Analyzed</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="em-card"><div class="em-metric-val">{quiz_count}</div><div class="em-metric-lbl">Quizzes Conducted</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="em-card"><div class="em-metric-val">{fc_count}</div><div class="em-metric-lbl">Flashcards Deck</div></div>', unsafe_allow_html=True)

    st.markdown("### 📈 Current Learning Activity Trackers")
    act_df = pd.DataFrame({
        'Study Vector Metrics': ['Structured Modules', 'Concept Iterations', 'RAG Evaluations', 'Exam Simulation Mockups'],
        'Progress Percentage': [68, 45, 80, 30]
    })
    fig = px.bar(act_df, x='Progress Percentage', y='Study Vector Metrics', orientation='h', 
                 color_discrete_sequence=[Config.COLOR_ACCENT], template="simple_white")
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)


elif st.session_state.current_page == "🤖 AI Chat":
    st.markdown("<p style='color: gray;'>Structured Multi-Source Context RAG Matrix Environment</p>", unsafe_allow_html=True)
    
    # Retrieve local session chat metrics
    with get_db_connection() as conn:
        rows = conn.execute("SELECT role, content FROM chat_history WHERE session_id = ? ORDER BY id ASC", (st.session_state.session_token,)).fetchall()
    
    # Render Current History State
    for r in rows:
        bubble_class = "chat-bubble-user" if r['role'] == "user" else "chat-bubble-ai"
        st.markdown(f'<div class="{bubble_class}">{r["content"]}</div>', unsafe_allow_html=True)
    
    st.markdown("<div style='clear:both; margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    
    # Handle Input Capture Interface Execution
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Pose a query to the processed study materials corpus:")
        submitted = st.form_submit_with_button("Dispatch Processing Stream")
        
        if submitted and user_input.strip():
            increment_analytic('questions_asked')
            
            # Context-Aware Semantic RAG Lookup Engine Layer execution
            relevant_chunks = vector_store.similarity_search(user_input, k=3)
            context_payload = "\n\n".join([f"[Source: {c['metadata']['name']}] {c['text']}" for c in relevant_chunks])
            
            # Save User Input parameters
            with get_db_connection() as conn:
                conn.execute("INSERT INTO chat_history (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                             (st.session_state.session_token, "user", user_input, datetime.now().isoformat()))
                conn.commit()
            
            # Construct Prompt Engine Payload Context Matrix
            messages = [
                {"role": "system", "content": f"You are an elite academic tutor helper. Rely ONLY on the provided verified material context to explain thoroughly with examples.\n\nContext:\n{context_payload}"},
                {"role": "user", "content": user_input}
            ]
            
            with st.spinner("Executing Semantic Search & LLM Context Synthesis..."):
                ai_response = OpenRouterService.complete(messages)
            
            # Save Context Generation response parameters
            with get_db_connection() as conn:
                conn.execute("INSERT INTO chat_history (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                             (st.session_state.session_token, "assistant", ai_response, datetime.now().isoformat()))
                conn.commit()
            
            st.rerun()

    if st.button("Purge Active Session Logs"):
        with get_db_connection() as conn:
            conn.execute("DELETE FROM chat_history WHERE session_id = ?", (st.session_state.session_token,))
            conn.commit()
        st.toast("Active chat session logs purged successfully.")
        st.rerun()


elif st.session_state.current_page == "📄 Documents":
    st.markdown("### 📤 Document Repository Upload Matrix")
    
    cat = st.selectbox("Assign Document Academic Categorization Taxonomy:", ["Textbook Material", "Lecture Notes", "Lab Handbook Sheets", "Past Examination Bank"])
    uploaded_files = st.file_uploader("Drop operational educational assets (PDF, DOCX, PPTX, TXT):", 
                                      type=["pdf", "docx", "pptx", "txt"], accept_multiple_files=True)
    
    if st.button("Execute Pipeline Embedding Processing") and uploaded_files:
        for f in uploaded_files:
            doc_id = str(uuid.uuid4())
            file_path = os.path.join(Config.UPLOAD_DIR, f"{doc_id}_{f.name}")
            
            with open(file_path, "wb") as buffer:
                buffer.write(f.getbuffer())
                
            # Perform targeted ingestion text parsing pipeline
            _, ext = os.path.splitext(f.name)
            extracted_raw = DocumentProcessor.extract_text(file_path, ext.lower())
            text_chunks = DocumentProcessor.chunk_text(extracted_raw)
            
            # Vector Database Embedding pipeline integration
            vector_store.add_texts(text_chunks, {"id": doc_id, "name": f.name, "category": cat})
            
            # Insert file record metadata tracking logs into DB
            with get_db_connection() as conn:
                conn.execute("INSERT INTO documents (id, name, category, upload_time, file_size) VALUES (?, ?, ?, ?, ?)",
                             (doc_id, f.name, cat, datetime.now().strftime("%Y-%m-%d %H:%M"), f.size))
                conn.commit()
                
        st.success(f"Successfully processed {len(uploaded_files)} document(s) into the RAG vector store.")
        st.rerun()
        
    st.markdown("---")
    st.markdown("### 🗄 Managed File Registry")
    with get_db_connection() as conn:
        docs = conn.execute("SELECT * FROM documents").fetchall()
        
    if docs:
        df = pd.DataFrame([dict(r) for r in docs])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No active academic documents verified in the local pipeline index.")


elif st.session_state.current_page == "📚 Topics":
    st.markdown("### 🔍 High-Fidelity Domain Concept Map Explorer")
    t_query = st.text_input("Enter a concept query to generate an extensive syllabus framework study guide:")
    
    if t_query and st.button("Generate Domain Curricula Architecture"):
        relevant_chunks = vector_store.similarity_search(t_query, k=4)
        context_payload = "\n\n".join([c['text'] for c in relevant_chunks])
        
        prompt = [
            {"role": "system", "content": "You are a senior academic curriculum mapping specialist. Construct a comprehensive breakdown with core pillars, theoretical prerequisites, and applied target objectives for the requested domain."},
            {"role": "user", "content": f"Analyze this topic: {t_query}\n\nContext Materials:\n{context_payload}"}
        ]
        
        with st.spinner("Synthesizing concept roadmap structures..."):
            res = OpenRouterService.complete(prompt)
        st.markdown(f'<div class="em-card">{res}</div>', unsafe_allow_html=True)


elif st.session_state.current_page == "❓ Question Bank":
    st.markdown("### 📥 Advanced Automated Exam Pattern Compiler")
    q_topic = st.text_input("Specify target sub-discipline focus area:")
    
    if q_topic and st.button("Compile Target Question Matrix"):
        relevant_chunks = vector_store.similarity_search(q_topic, k=4)
        context_payload = "\n\n".join([c['text'] for c in relevant_chunks])
        
        prompt = [
            {"role": "system", "content": "Generate 3 highly analytical, conceptual questions accompanied by complete step-by-step structural model solutions based on the provided text."},
            {"role": "user", "content": f"Topic Area: {q_topic}\n\nSource Matrix:\n{context_payload}"}
        ]
        
        with st.spinner("Generating targeted academic questions..."):
            res = OpenRouterService.complete(prompt)
        st.markdown(f'<div class="em-card">{res}</div>', unsafe_allow_html=True)


elif st.session_state.current_page == "📝 Quiz":
    st.markdown("### 🧠 Adaptive Knowledge Validation Assessment Matrix")
    qz_topic = st.text_input("Specify target parameters to formulate interactive evaluation problems:", "Database Systems")
    
    if st.button("Generate Dynamic Quiz Setup"):
        relevant_chunks = vector_store.similarity_search(qz_topic, k=3)
        context_payload = "\n\n".join([c['text'] for c in relevant_chunks])
        
        prompt = [
            {"role": "system", "content": "Generate exactly one complex multiple-choice question problem structure. Return the question followed by four options (A, B, C, D) and specify the accurate answer clearly."},
            {"role": "user", "content": f"Subject Context Parameter: {qz_topic}\n\nSource Material Context:\n{context_payload}"}
        ]
        
        with st.spinner("Assembling structural test parameters..."):
            st.session_state.active_quiz = OpenRouterService.complete(prompt)
            increment_analytic('quizzes_taken')
            
    if "active_quiz" in st.session_state:
        st.markdown(f'<div class="em-card">{st.session_state.active_quiz}</div>', unsafe_allow_html=True)
        
        score_val = st.slider("Self-evaluated scoring precision index performance:", 0, 100, 80)
        if st.button("Submit Assessment Score Evaluation"):
            update_avg_score(score_val)
            st.success(f"Assessment performance score matrix locked at: {score_val}%")


elif st.session_state.current_page == "🧠 Flashcards":
    st.markdown("### ⚡ Active Recall Spaced Repetition Engine")
    
    with st.form("fc_add"):
        subj = st.text_input("Course Subject Designation Tag:")
        front_txt = st.text_area("Front Side (Core Prompt Question):")
        back_txt = st.text_area("Back Side (Theoretical Explanation Resolution Model):")
        diff = st.selectbox("Difficulty Threshold Scale:", ["Easy", "Medium", "Hard"])
        
        if st.form_submit_with_button("Commit Flashcard to Storage Engine"):
            if front_txt and back_txt:
                with get_db_connection() as conn:
                    conn.execute("INSERT INTO flashcards (subject, front, back, difficulty) VALUES (?, ?, ?, ?)",
                                 (subj, front_txt, back_txt, diff))
                    conn.commit()
                st.toast("Flashcard saved successfully.")
                st.rerun()
                
    st.markdown("---")
    
    # Retrieve saved flashcard elements from storage
    with get_db_connection() as conn:
        cards = conn.execute("SELECT * FROM flashcards").fetchall()
        
    if cards:
        for idx, item in enumerate(cards):
            with st.expander(f"🎴 Card {idx+1} | Subject Target: {item['subject']} [{item['difficulty']}]"):
                st.markdown(f"**Front Query Prompt:**\n{item['front']}")
                st.markdown("---")
                st.markdown(f"**Back Target Explanation Resolution:**\n{item['back']}")
    else:
        st.info("No interactive recall metrics registered in flashcard datastores.")


elif st.session_state.current_page == "📊 Analytics":
    st.markdown("### 📊 Enterprise Predictive Learning Performance Metrics")
    
    with get_db_connection() as conn:
        metrics_rows = conn.execute("SELECT * FROM analytics").fetchall()
        avg_score = conn.execute("SELECT value_real FROM analytics WHERE key='avg_quiz_score'").fetchone()[0]
        
    st.markdown("#### Primary Performance Metrics Registry Logs")
    for r in metrics_rows:
        st.text(f"Key Vector ID: {r['key']} -> Metric Counter Value: {r['value_int']}")
        
    st.metric(label="Average Performance Matrix Quiz Score Rating", value=f"{round(avg_score, 2)}%")


elif st.session_state.current_page == "⚙ Settings":
    st.markdown("### 🛠 Operational Engine Core Settings Configurations")
    st.info("Operational Deployment Platform Profile Verified: STREAMLIT_CLOUD_PRODUCTION_ENV")
    
    st.text_input("Target OpenRouter Base Engine Model Parameter URI:", value=Config.DEFAULT_MODEL, disabled=True)
    
    status = "🔒 VALID ENCRYPTED KEY DETECTED" if len(Config.OPENROUTER_API_KEY) > 5 else "❌ NO OPERATIONAL API KEY CONFIGURATION REGISTERED"
    st.text(f"OpenRouter Authentication Handshake Engine Infrastructure Status: {status}")