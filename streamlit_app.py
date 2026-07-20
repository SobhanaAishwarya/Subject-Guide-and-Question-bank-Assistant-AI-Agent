import os
import sys
import runpy

APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "studyai_streamlit", "studyai")
sys.path.insert(0, APP_DIR)
os.chdir(APP_DIR)

runpy.run_path(os.path.join(APP_DIR, "streamlit_app.py"), run_name="__main__")
