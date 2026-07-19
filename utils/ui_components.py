import streamlit as st
from config import Config

def apply_custom_theme():
    """Injects high-grade premium CSS to strip default Streamlit styling overrides."""
    css = f"""
    <style>
        /* Base Global Overrides */
        html, body, [data-testid="stAppViewContainer"] {{
            background-color: {Config.COLOR_BG} !important;
            color: {Config.COLOR_TEXT} !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}
        
        /* Eliminate Core Streamlit Headers/Footers */
        [data-testid="stHeader"], footer, #tabs-bui3-tabpanel-0 {{
            visibility: hidden !important;
            display: none !important;
        }}
        
        /* Modernized Elegant Sidebar Architecture */
        [data-testid="stSidebar"] {{
            background-color: #FFFFFF !important;
            border-right: 1px solid {Config.COLOR_BORDER} !important;
        }}
        
        /* Premium Card UI System Component Structuring */
        .em-card {{
            background: {Config.COLOR_CARD};
            border: 1px solid {Config.COLOR_BORDER};
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(239, 229, 190, 0.2);
            transition: all 0.3s ease-in-out;
        }}
        .em-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(239, 229, 190, 0.4);
            background-color: {Config.COLOR_HOVER};
        }}
        
        /* Premium Metric Display Cards Layouts */
        .em-metric-val {{
            font-size: 2.2rem;
            font-weight: 700;
            color: {Config.COLOR_TEXT};
            margin-bottom: 4px;
        }}
        .em-metric-lbl {{
            font-size: 0.9rem;
            color: #757575;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        /* Beautiful Buttons Custom Theming Configuration */
        .stButton>button {{
            background: linear-gradient(135deg, {Config.COLOR_PRIMARY} 0%, {Config.COLOR_ACCENT} 100%) !important;
            color: {Config.COLOR_TEXT} !important;
            border: 1px solid {Config.COLOR_BORDER} !important;
            border-radius: 12px !important;
            padding: 10px 24px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 2px 8px rgba(255, 213, 79, 0.3) !important;
        }}
        .stButton>button:hover {{
            transform: scale(1.02) !important;
            box-shadow: 0 4px 12px rgba(255, 213, 79, 0.5) !important;
        }}
        
        /* Custom Chat Elements Architectures styling */
        .chat-bubble-user {{
            background-color: #F0EDE0 !important;
            color: {Config.COLOR_TEXT} !important;
            border-radius: 16px 16px 4px 16px !important;
            padding: 14px;
            margin: 8px 0;
            max-width: 85%;
            float: right;
            clear: both;
        }}
        .chat-bubble-ai {{
            background-color: #FFFFFF !important;
            color: {Config.COLOR_TEXT} !important;
            border: 1px solid {Config.COLOR_BORDER} !important;
            border-radius: 16px 16px 16px 4px !important;
            padding: 14px;
            margin: 8px 0;
            max-width: 85%;
            float: left;
            clear: both;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def render_hero():
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #FFFDF5 0%, {Config.COLOR_PRIMARY} 100%); 
                    padding: 40px; border-radius: 24px; border: 1px solid {Config.COLOR_BORDER}; 
                    margin-bottom: 32px; text-align: center;">
            <h1 style="color: {Config.COLOR_TEXT}; font-weight: 800; font-size: 3rem; margin-bottom: 8px;">EduMind AI</h1>
            <p style="color: #555555; font-size: 1.2rem; font-weight: 400; max-width: 600px; margin: 0 auto;">
                Your production-grade workspace companion processing advanced Academic RAG Engineering analytics.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )