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
    page_title="agentic_ai_clean | Advanced Study Assistant",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply sleek production-grade deep dark theme CSS overrides
st.markdown("""
    <style>
    /* Main layout colors */
    .stApp {
        background-color: #0E1117;
        color: #E2E8F0;
    }
    /* Round up card boxes and containers */
    div[data-testid="stVerticalBlock"] > div {
        background-color: #1A1D24;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 12px;
        border: 1px solid #2D3748;
    }
    /* Buttons custom styling */
    .stButton>button {
        background-color: #4F46E5 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #6366F1 !important;
        transform: translateY(-1px);
    }
    /* Text inputs styling */
    input, textarea {
        background-color: #0E1117 !important;
        color: #E2E8F0 !important;
        border: 1px solid #4A5568 !important;
        border-radius: 6px !important;
    }
    /* Metric label styling */
    div[data-testid="stMetricValue"] {
        color: #10B981 !important;
        font-weight: 700;
    }
    hr {
        border-top: 1px solid #2D3748 !important;
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
    st.title("✈️ agentic_ai_clean")
    st.subheader("Your Intelligent Agentic AI Study Assistant")
    
    tab1, tab2 = st.tabs(["🔒 Secure Login", "📝 Create Account"])
    
    with tab1:
        st.write("### Sign In")
        login_email = st.text_input("Email Address", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_password")
        if st.button("Authenticate Session"):
            with get_db_session() as session:
                user = AuthManager.authenticate_user(session, login_email, login_password)
                if user:
                    st.session_state.user = {"id": user.id, "name": user.name, "email": user.email}
                    st.success(f"Welcome back, {user.name}!")
                    st.rerun()
                else:
                    st.error("Invalid email payload coordinates or password match.")

    with tab2:
        st.write("### Sign Up")
        reg_name = st.text_input("Full Name", key="reg_name")
        reg_email = st.text_input("Email Address", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        if st.button("Register & Initialize Profile"):
            if not reg_name or not reg_email or not reg_password:
                st.warning("All verification text fields are strictly required.")
            else:
                with get_db_session() as session:
                    new_user = AuthManager.register_user(session, reg_name, reg_email, reg_password)
                    if new_user:
                        st.success("Account initialized successfully! Please sign in above.")
                    else:
                        st.error("Registration rejected: Email target address may be already registered.")

def render_dashboard():
    user = st.session_state.user
    st.title(f"📊 Welcome, {user['name']}")
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
    st.info("💡 **Pro-Tip**: Use the left sidebar selection terminal to toggle between specialized view modes. Our Supervisor agent dynamically monitors chat requests to distribute computational workloads.")

def render_chat():
    st.title("💬 Cognitive Workspace")
    user = st.session_state.user
    
    col1, col2 = st.columns(2)
    with col1:
        teacher_mode = st.selectbox("Pedagogical Target Mode", ["Beginner", "Advanced", "Interview"])
    with col2:
        clear_hist = st.button("Purge Chat Window Cache")
        
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

    if prompt := st.chat_input("Ask a conceptual question or interface document contents..."):
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Agentic loop processing workflow..."):
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
                    with st.expander("📄 Source Documents Citations"):
                        for cite in citations:
                            st.markdown(f"**[{cite['citation_index']}] File:** {cite['source']} (Page {cite['page']})")
                            st.caption(f"Snippet: *{cite['snippet']}*")
                
                with get_db_session() as session:
                    HistoryManager.save_chat_turn(session, user["id"], prompt, output_content)

def render_upload():
    st.title("📁 Upload Material Library")
    user = st.session_state.user
    
    uploaded_file = st.file_uploader("Index personal reference materials (PDF only)", type=["pdf"])
    if uploaded_file is not None:
        if st.button("Execute Indexing Pipeline"):
            with st.spinner("Extracting layout matrix nodes and saving to vector stores..."):
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
    st.title("🎯 Quiz Assessment Engine")
    user = st.session_state.user
    
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input("Target Evaluation Topic Context", "Operating Systems Process Synchronization")
    with col2:
        q_type = st.selectbox("Format Type", ["MCQ", "FILL", "CODING"])
        
    if st.button("Generate Dynamic Assessment"):
        with st.spinner("Compiling structural challenge questions..."):
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
                ans = st.text_input("Input your answer sequence", key=f"q_{idx}")
                if ans.strip().lower() == str(item.get("correct_answer")).strip().lower():
                    score_counter += 1
            with st.expander("See Explanation Details"):
                st.write(f"*Correct Answer:* **{item.get('correct_answer')}**")
                st.write(item.get("explanation"))
            st.write("---")
            
        if st.button("Submit Score Transcript"):
            pct = (score_counter / total_q) * 100.0
            with get_db_session() as session:
                rec = QuizResult(user_id=user["id"], topic=st.session_state.quiz_topic, score=pct)
                session.add(rec)
                
                progress = session.query(StudyProgress).filter(StudyProgress.user_id == user["id"]).first()
                if progress:
                    progress.study_time += 0.25
            st.success(f"Transcript captured perfectly! Score: {pct:.1f}%")

def render_flashcards():
    st.title("⚡ Active Recall Flashcards")
    user = st.session_state.user
    
    topic = st.text_input("Enter Focus Domain Topic Key", "Data Structures Trees and Graphs")
    if st.button("Build Flashcard Deck"):
        with st.spinner("Extracting active recall terms..."):
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
            st.error("Error constructing structured deck. Please retry query syntax.")
            return
            
        for card in st.session_state.active_deck:
            with st.container():
                st.markdown(f"#### ❔ Question: {card.get('front')}")
                with st.expander("🔄 Flip Card to View Core Answer"):
                    st.success(f"**Answer:** {card.get('back')}")
                st.markdown("---")

def render_planner():
    st.title("📅 Personalized Study Schedule Planner")
    user = st.session_state.user
    
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input("Target Objective/Exam Scope", "DBMS Midterm Review")
        weeks = st.slider("Duration (Weeks)", 1, 12, 4)
    with col2:
        hours = st.slider("Daily Allocation Threshold Commitment (Hours)", 1, 8, 2)
        
    if st.button("Generate Complete Schedule Map"):
        with st.spinner("Assembling curriculum architecture tracks..."):
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
    st.title("📈 Progress Analytics Matrix")
    user = st.session_state.user
    
    with get_db_session() as session:
        progress = session.query(StudyProgress).filter(StudyProgress.user_id == user["id"]).first()
        quizzes = session.query(QuizResult).filter(QuizResult.user_id == user["id"]).order_by(QuizResult.date.desc()).all()
        
        st.write("### Core System Performance Metrics")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Cumulative Calculated Study Time", f"{progress.study_time if progress else 0.0} Hours")
        with col2:
            st.metric("Total Assessments Concluded", f"{len(quizzes)} Quizzes")
            
        st.write("---")
        st.write("### Evaluation History Matrix")
        if quizzes:
            for q in quizzes:
                st.write(f"🎯 **Topic:** {q.topic} | **Score Profile:** `{q.score:.1f}%` | *Date:* {q.date.strftime('%Y-%m-%d')}")
        else:
            st.caption("No systemic evaluation records logged for this session account.")

def render_settings():
    st.title("⚙️ Workspace Profile Settings")
    user = st.session_state.user
    st.write("### Session Profile Context Data")
    st.write(f"- **Student Profile Name Target:** {user['name']}")
    st.write(f"- **Secure Identity Communication Email Address:** {user['email']}")
    st.markdown("---")
    st.caption("agentic_ai_clean Architecture Core System Engine — Built with Streamlit & LangGraph State Engines.")

# Core Sidebar Selection Layout Controllers Routing Context Matrix
if st.session_state.user is None:
    render_login_signup()
else:
    with st.sidebar:
        st.markdown(f"### ✈️ StudyPilot AI\n**User:** {st.session_state.user['name']}")
        st.markdown("---")
        choice = st.radio(
            "Navigation Menu Desk",
            ["Dashboard", "Chat Workspace", "Upload Library", "Quiz Center", "Flashcards Deck", "Curriculum Planner", "Progress Matrix", "Settings Desk"]
        )
        st.markdown("---")
        if st.button("Terminate Active Session"):
            st.session_state.user = None
            st.rerun()

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