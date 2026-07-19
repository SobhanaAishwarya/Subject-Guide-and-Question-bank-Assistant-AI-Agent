import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PROJECT_NAME = "EduMind AI"
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct"
    
    # CSS Custom Palette Definitions
    COLOR_PRIMARY = "#F7E7A9"
    COLOR_ACCENT = "#FFD54F"
    COLOR_BG = "#FFFDF5"
    COLOR_CARD = "#FFFFFF"
    COLOR_TEXT = "#2B2B2B"
    COLOR_BORDER = "#EFE5BE"
    COLOR_HOVER = "#FFF6CC"
    
    # Storage Directives
    UPLOAD_DIR = "uploads"
    VECTOR_DIR = "vectorstore"
    DB_PATH = "database/edumind.db"

# Ensure runtime initialization directories exist
for folder in [UPLOAD_DIR, VECTOR_DIR, "database"]:
    os.makedirs(folder, exist_ok=True)