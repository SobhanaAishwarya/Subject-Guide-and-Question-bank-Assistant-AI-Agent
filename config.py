import os
from dotenv import load_dotenv

load_dotenv()

# 1. Define these as global constants at the file level
UPLOAD_DIR = "uploads"
VECTOR_DIR = "vectorstore"
DATABASE_DIR = "database"
DB_PATH = os.path.join(DATABASE_DIR, "edumind.db")

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
    
    # 2. Attach them to the class namespace so the rest of your files don't break
    UPLOAD_DIR = UPLOAD_DIR
    VECTOR_DIR = VECTOR_DIR
    DB_PATH = DB_PATH

# 3. Now the initialization loop can safely execute without scoping errors
for folder in [UPLOAD_DIR, VECTOR_DIR, DATABASE_DIR]:
    os.makedirs(folder, exist_ok=True)