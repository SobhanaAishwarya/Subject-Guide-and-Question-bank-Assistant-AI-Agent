import os

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

UPLOAD_DIR = os.path.join(
    BASE_DIR,
    "uploads"
)

VECTORSTORE_DIR = os.path.join(
    BASE_DIR,
    "vectorstore"
)

DB_PATH = os.path.join(
    BASE_DIR,
    "database",
    "subjectguide.db"
)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200