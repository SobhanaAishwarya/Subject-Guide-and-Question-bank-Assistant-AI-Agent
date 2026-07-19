import streamlit as st
import os
from dotenv import load_dotenv

# Load configurations first
load_dotenv()

from database.connection import init_db, get_db_session
from database.schemas import User, QuizResult, StudyProgress
from auth.manager import AuthManager
from services.pdf_service import PDFService
from memory.history_manager import HistoryManager
from agents.graph_orchestrator import GraphOrchestrator
from utils.logger import logger

# Initialize foundational app configurations
st.set_page_config(
    page_title="StudyPilot AI - Agentic AI Study Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Modern SaaS Dark Theme CSS (Refined Deep Slate & Vivid Sky Blue Accents)
st.markdown("""
    <style>
    /* Main Layout Base */
    .stApp {
        background-color: #0B0F19;
        color: #F1F5F9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Clean Cards & Structural Dynamic Containers */
    div[data-testid="stVerticalBlock"] > div {
        background-color: #111827;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 16px;
        border: 1px solid #1F2937;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2), 0 2px 4px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Left Navigation Sidebar Override */
    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 1px solid #1E293B;
    }
    
    /* Constrain and Center the Authentication Screen Block Layout */
    .auth-container {
        max-width: 460px;
        margin: 60px auto;
        padding: 36px;
        background-color: #111827;
        border-radius: 16px;
        border: 1px solid #1F2937;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2);
    }
    
    /* Buttons Custom Action Styling */
    .stButton>button {
        background-color: #0EA5E9 !important; /* Premium Sky Blue */
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 10px 24px !important;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background-color: #0284C7 !important; /* Deeper Ocean Blue */
        box-shadow: 0 0 16px rgba(14, 165, 233, 0.4);
        transform: translateY(-1px);
    }
    
    /* Input Fields Accent Refinements */
    input, textarea, select {
        background-color: #1F2937 !important;
        color: #F8FAFC !important;
        border: 1px solid #374151 !important;
        border-radius: 8px !important;
        padding: 10px !important;
    }
    input:focus, textarea:focus {
        border-color: #0EA5E9 !important;
        box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.2) !important;
    }
    
    /* Balanced Metrics Design Matrix */
    div[data-testid="stMetricValue"] {
        color: #38BDF8 !important; /* Cyber Sky Accent */
        font-weight: 700;
        font-size: 2.4rem !important;
        letter-spacing: -0.025em;
    }
    div[data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-size: 0.95rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Custom Decorative Clean Badge Lines */
    .hero-title {
        font-size: 2.25rem;
        font-weight: 800;
        color: #F8FAFC;
        letter-spacing: -0.025em;
        margin-bottom: 4px;
    }
    .hero-subtitle {
        color: #94A3B8;
        font-size: 1.05rem;
        margin-bottom: 24px;
    }
    
    hr {
        border-top: 1px solid #1F2937 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Instantiate application singletons inside session caches safely
if "initialized" not in st.session_state:
    init_db()
    pdf_svc = PDFService()
    pdf_svc.initialize_global_knowledge_base()
    st.session_state.orchestrator = GraphOrchestrator()
    st.session_state.pdf_service = pdf_svc
    st.session_state.user = None
    st.session_state.initialized = True
    logger.info("Application infrastructure states fully hydrated.")

def render_login_signup():
    # Use asymmetric structural column spacing to center layout cleanly
    _, center_col, _ = st.columns([1, 1.25, 1])
    
    with center_col:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.markdown('<div class="hero-title">✈️ StudyPilot AI</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-subtitle">Intelligent Agentic Study Workspace</div>', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔒 Secure Login", "📝 Create Account"])
        
        with tab1:
            st.write(" ")
            login_email = st.text_input("Email Address", key="login_email")
            login_password = st.text_input("Password", type="password", key="login_password")
            st.write(" ")
            if st.button("Authenticate Session", use_container_width=True):
                with get_db_session() as session:
                    user = AuthManager.authenticate_user(session, login_email, login_password)
                    if user:
                        st.session_state.user = {"id": user.id, "name": user.name, "email": user.email}
                        st.success(f"Welcome back, {user.name}!")
                        st.rerun()
                    else:
                        st.error("Invalid email coordinates or password match.")

        with tab2:
            st.write(" ")
            reg_name = st.text_input("Full Name", key="reg_name")
            reg_email = st.text_input("Email Address", key="reg_email")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            st.write(" ")
            if st.button("Register & Initialize Profile", use_container_width=True):
                if not reg_name or not reg_email or not reg_password:
                    st.warning("All tracking data fields are strictly required.")
                else:
                    with get_db_session() as session:
                        new_user = AuthManager.register_user(session, reg_name, reg_email, reg_password)
                        if new_user:
                            st.success("Account initialized successfully! Please sign in.")
                        else:
                            st.error("Registration rejected: Target email already registered.")
        st.markdown('</div>', unsafe_allow_html=True)

def render_dashboard():
    user = st.session_state.user
    st.markdown(f"## 📊 Academic Workspace Overview")
    st.markdown(f"Welcome back, **{user['name']}**. Track your real-time analytics indicators below.")
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with get_db_session() as session:
        progress = session.query(StudyProgress).filter(StudyProgress.user_id == user["id"]).first()
        quizzes = session.query(QuizResult).filter(QuizResult.user_id == user["id"]).all()
        pdfs = st.session_state.pdf_service.get_user_uploaded_pdfs(session, user["id"])
        
        avg_score = sum([q.score for q in quizzes]) / len(quizzes) if quizzes else 0.0
        
        with col1:
            st.metric("Total Study Context", f"{progress.study_time if progress else 0.0} Hours")
        with col2:
            st.metric("Evaluation Accuracy", f"{avg_score:.1f}%")
        with col3:
            st.metric("Custom Indexed Library", f"{len(pdfs)} PDFs")

    st.write("### Available Architectural Capabilities")
    st.info("💡 **Pro-Tip**: Use the left sidebar navigation matrix to toggle between cognitive work subnodes. Our Supervisor agent dynamically balances operational requests.")

def render_chat():
    st.markdown("## 💬 Cognitive Chat Workspace")
    user = st.session_state.user
    
    col1, col2 = st.columns([3, 1])
    with col1:
        teacher_mode = st.selectbox("Pedagogical Target Mode Override", ["Beginner", "Advanced", "Interview"])
    with col2:
        st.write(" ")
        st.write(" ")
        clear_hist = st.button("Purge Workspace Cache", use_container_width=True)
        
    with get_db_session() as session:
        if clear_hist:
            HistoryManager.clear_user_history(session, user["id"])
            st.success("History cache cleared.")
            st.rerun()

        history_msgs = HistoryManager.get_serialized_messages(session, user["id"], limit=15)
        
        for msg in history_msgs:
            role = "user" if msg.type == "human" else "assistant"
            with st.chat_message(role):
                st.markdown(msg.content)

    if prompt := st.chat_input("Ask a conceptual problem or run cross-document analysis vectors..."):
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Agentic workflow balancing execution tracks..."):
                initial_graph_state = {
                    "user_input": prompt,
                    "user_id": user["id"],
                    "metadata": {"teacher_mode": teacher_mode.lower()},
                    "next_agent": "supervisor",
                    "retrieved_context": "",
                    "citations": [],
                    "messages": history_msgs,
                    "agent_output": {},
                    "errors": []
                }
                
                final_state = st.session_state.orchestrator.run_workflow(initial_graph_state)
                output_content = final_state.get("agent_output", {}).get("content", "I am unable to resolve this request context turn completely.")
                
                st.markdown(output_content)
                
                citations = final_state.get("citations", [])
                if citations:
                    with st.expander("📄 Source Document Context Citations"):
                        for cite in citations:
                            st.markdown(f"**[{cite['citation_index']}] File:** {cite['source']} (Page {cite['page']})")
                            st.caption(f"Snippet: *{cite['snippet']}*")
                
                with get_db_session() as session:
                    HistoryManager.save_chat_turn(session, user["id"], prompt, output_content)

def render_upload():
    st.markdown("## 📁 Knowledge Vector Material Library")
    user = st.session_state.user
    
    uploaded_file = st.file_uploader("Index personal reference materials (PDF format strictly supported)", type=["pdf"])
    if uploaded_file is not None:
        if st.button("Execute Ingestion Pipeline", use_container_width=True):
            with st.spinner("Extracting layout matrices and compiling FAISS storage indices..."):
                file_bytes = uploaded_file.read()
                with get_db_session() as session:
                    record = st.session_state.pdf_service.process_and_index_user_pdf(
                        session, user["id"], uploaded_file.name, file_bytes
                    )
                    if record:
                        st.success(f"Successfully processed and generated semantic vector coordinates for: '{uploaded_file.name}'")
                    else:
                        st.error("Pipeline failure: check text processor integrity configurations.")

    st.write("---")
    st.write("### Your Active Document Catalog")
    with get_db_session() as session:
        pdfs = st.session_state.pdf_service.get_user_uploaded_pdfs(session, user["id"])
        if pdfs:
            for pdf in pdfs:
                st.write(f"📎 **{pdf.filename}** — *Indexed on {pdf.created_at.strftime('%Y-%m-%d')}*")
        else:
            st.caption("No custom study documents uploaded yet.")

def render_quiz():
    st.markdown("## 🎯 Adaptive Assessment Engine")
    user = st.session_state.user
    
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input("Target Evaluation Topic Context", "Operating Systems Process Synchronization")
    with col2:
        q_type = st.selectbox("Format Architecture Style", ["MCQ", "FILL", "CODING"])
        
    if st.button("Generate Assessment Deck", use_container_width=True):
        with st.spinner("Compiling structural verification items..."):
            initial_state = {
                "user_input": topic,
                "user_id": user["id"],
                "metadata": {"quiz_type": q_type, "num_questions": 3},
                "next_agent": "supervisor",
                "retrieved_context": "",
                "citations": [],
                "messages": [],
                "agent_output": {},
                "errors": []
            }
            res = st.session_state.orchestrator.quiz_master.process(initial_state)
            st.session_state.active_quiz = res.get("agent_output", {}).get("quiz_questions", [])
            st.session_state.quiz_topic = topic

    if "active_quiz" in st.session_state and st.session_state.active_quiz:
        st.write("### Complete Your Assessment")
        
        if isinstance(st.session_state.active_quiz, dict) and "error_fallback" in st.session_state.active_quiz:
            st.error("Could not construct structured assessment array loop. Please rerun the engine.")
            return

        score_counter = 0
        total_q = len(st.session_state.active_quiz)
        
        for idx, item in enumerate(st.session_state.active_quiz):
            st.markdown(f"**Q{idx+1}: {item.get('question')}**")
            if item.get("type") == "MCQ":
                opts = item.get("options", ["A", "B", "C", "D"])
                ans = st.radio(f"Select choice for Q{idx+1}", opts, key=f"q_{idx}")
                if ans == item.get("correct_answer"):
                    score_counter += 1
            else:
                ans = st.text_input("Input exact structural response token", key=f"q_{idx}")
                if ans.strip().lower() == str(item.get("correct_answer")).strip().lower():
                    score_counter += 1
            with st.expander("Review Academic Breakdown Summary"):
                st.write(f"*Correct Answer:* **{item.get('correct_answer')}**")
                st.write(item.get("explanation"))
            st.write("---")
            
        if st.button("Submit Score Transcript", use_container_width=True):
            pct = (score_counter / total_q) * 100.0
            with get_db_session() as session:
                rec = QuizResult(user_id=user["id"], topic=st.session_state.quiz_topic, score=pct)
                session.add(rec)
                
                progress = session.query(StudyProgress).filter(StudyProgress.user_id == user["id"]).first()
                if progress:
                    progress.study_time += 0.25
            st.success(f"Transcript captured perfectly! Score profile tracked: {pct:.1f}%")

def render_flashcards():
    st.markdown("## ⚡ High-Yield Active Recall Decks")
    user = st.session_state.user
    
    topic = st.text_input("Enter Focus Domain Topic Area", "Data Structures Trees and Graphs")
    if st.button("Build Dynamic Recall Deck", use_container_width=True):
        with st.spinner("Extracting functional context dimensions..."):
            initial_state = {
                "user_input": topic,
                "user_id": user["id"],
                "metadata": {"num_cards": 4},
                "next_agent": "supervisor",
                "retrieved_context": "",
                "citations": [],
                "messages": [],
                "agent_output": {},
                "errors": []
            }
            res = st.session_state.orchestrator.flashcard_worker.process(initial_state)
            st.session_state.active_deck = res.get("agent_output", {}).get("flashcards", [])

    if "active_deck" in st.session_state and st.session_state.active_deck:
        if isinstance(st.session_state.active_deck, dict):
            st.error("Error constructing structured deck. Please retry query layout.")
            return
            
        for card in st.session_state.active_deck:
            with st.container():
                st.markdown(f"#### ❔ Question: {card.get('front')}")
                with st.expander("🔄 Flip Active Card Structure"):
                    st.info(f"**Answer Core:** {card.get('back')}")
                st.markdown("---")

def render_planner():
    st.markdown("## 📅 Dynamic Curriculum & Milestone Planner")
    user = st.session_state.user
    
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input("Target Objective/Exam Horizon Scope", "DBMS Midterm Review")
        weeks = st.slider("Timeline Horizon Allocation (Weeks)", 1, 12, 4)
    with col2:
        hours = st.slider("Daily Study Time Threshold Commitment (Hours)", 1, 8, 2)
        
    if st.button("Generate Complete Schedule Map", use_container_width=True):
        with st.spinner("Assembling personalized milestone charts..."):
            state = {
                "user_input": topic,
                "user_id": user["id"],
                "metadata": {"duration_weeks": weeks, "daily_hours": hours},
                "next_agent": "supervisor",
                "retrieved_context": "",
                "citations": [],
                "messages": [],
                "agent_output": {},
                "errors": []
            }
            res = st.session_state.orchestrator.planner.process(state)
            st.markdown(res.get("agent_output", {}).get("content", ""))

def render_progress():
    st.markdown("## 📈 Performance Analytics Matrix")
    user = st.session_state.user
    
    with get_db_session() as session:
        progress = session.query(StudyProgress).filter(StudyProgress.user_id == user["id"]).first()
        quizzes = session.query(QuizResult).filter(QuizResult.user_id == user["id"]).order_by(QuizResult.date.desc()).all()
        
        st.write("### Core System Diagnostics Summary")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Cumulative Calculated Study Time", f"{progress.study_time if progress else 0.0} Hours")
        with col2:
            st.metric("Total Assessments Concluded", f"{len(quizzes)} Quizzes")
            
        st.write("---")
        st.write("### Historical Evaluation Records Log")
        if quizzes:
            for q in quizzes:
                st.write(f"🎯 **Topic Target:** {q.topic} | **Score:** `{q.score:.1f}%` | *Date Logged:* {q.date.strftime('%Y-%m-%d')}")
        else:
            st.caption("No historical diagnostic score items logged for this workspace account.")

def render_settings():
    st.markdown("## ⚙️ Profile Workspace Settings")
    user = st.session_state.user
    st.write("### Active Session Context")
    st.write(f"- **Student Profile Identity Name:** {user['name']}")
    st.write(f"- **Linked Communication Email Endpoint:** {user['email']}")
    st.markdown("---")
    st.caption("StudyPilot AI Engine running on LangGraph Orchestration Topology Layers.")

# Core Sidebar Context Router Terminal Setup
if st.session_state.user is None:
    render_login_signup()
else:
    with st.sidebar:
        st.markdown(f"### ✈️ StudyPilot AI\n**Active Student:** {st.session_state.user['name']}")
        st.markdown("---")
        choice = st.radio(
            "Navigation Workspace Desk",
            ["Dashboard", "Chat Workspace", "Upload Library", "Quiz Center", "Flashcards Deck", "Curriculum Planner", "Progress Matrix", "Settings Desk"]
        )
        st.markdown("---")
        if st.button("Terminate Session Profile", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    # Route selected layout controller bounds viewport screens cleanly
    if choice == "Dashboard":
        render_dashboard()
    elif choice == "Chat Workspace":
        render_chat()
    elif choice == "Upload Library":
        render_upload()
    elif choice == "Quiz Center":
        render_quiz()
    elif choice == "Flashcards Deck":
        render_flashcards()
    elif choice == "Curriculum Planner":
        render_planner()
    elif choice == "Progress Matrix":
        render_progress()
    elif choice == "Settings Desk":
        render_settings()