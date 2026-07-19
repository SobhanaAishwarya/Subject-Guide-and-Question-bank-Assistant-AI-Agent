import sqlite3
import json
from datetime import datetime
from config import Config

def get_db_connection():
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Documents Registry Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                name TEXT,
                category TEXT,
                upload_time TEXT,
                file_size INTEGER
            )
        ''')
        
        # Interactive Chat History Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TEXT
            )
        ''')
        
        # Active Flashcards Datastore
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flashcards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT,
                front TEXT,
                back TEXT,
                difficulty TEXT DEFAULT 'Medium',
                is_bookmarked INTEGER DEFAULT 0
            )
        ''')
        
        # Platform Operational Metrics Engine
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                key TEXT PRIMARY KEY,
                value_int INTEGER DEFAULT 0,
                value_real REAL DEFAULT 0.0
            )
        ''')
        
        # Populate Default Metrics Counter
        metrics = [('questions_asked', 0), ('study_time_mins', 45), ('quizzes_taken', 0), ('avg_quiz_score', 0)]
        for key, val in metrics:
            cursor.execute('INSERT OR IGNORE INTO analytics (key, value_int) VALUES (?, ?)', (key, val))
            
        conn.commit()

def increment_analytic(key: str, amount: int = 1):
    with get_db_connection() as conn:
        conn.execute('UPDATE analytics SET value_int = value_int + ? WHERE key = ?', (amount, key))
        conn.commit()

def update_avg_score(new_score: float):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT value_int, value_real FROM analytics WHERE key = "quizzes_taken"')
        res = cursor.fetchone()
        count = res['value_int'] if res else 1
        cursor.execute('UPDATE analytics SET value_real = ((value_real * ?) + ?) / (? + 1) WHERE key = "avg_quiz_score"', (count-1, new_score, count-1))
        conn.commit()