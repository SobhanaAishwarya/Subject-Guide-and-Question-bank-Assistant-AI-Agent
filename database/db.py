import sqlite3

from config.settings import DB_PATH


def get_connection():

    conn = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )

    return conn