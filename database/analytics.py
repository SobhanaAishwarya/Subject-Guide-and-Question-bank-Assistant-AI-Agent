from database.db import get_connection


def create_analytics_table():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analytics(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        total_questions INTEGER,
        total_quizzes INTEGER,
        average_score REAL
    )
    """)

    conn.commit()
    conn.close()